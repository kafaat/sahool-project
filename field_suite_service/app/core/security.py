"""
Security Module for Sahool Yemen
سهول اليمن - وحدة الأمان

Rate Limiting, Input Validation, Security Headers, and Authentication.
"""
import asyncio
import hashlib
import hmac
import secrets
import time
import re
from datetime import datetime, timedelta
from typing import Optional, Any
from dataclasses import dataclass

from fastapi import Request, Response, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import jwt

logger = structlog.get_logger(__name__)


# =============================================================================
# Security Configuration
# =============================================================================

@dataclass
class SecurityConfig:
    """Security configuration"""
    # JWT Settings - MUST be set via environment variable in production
    jwt_secret: str = None  # Will be loaded from JWT_SECRET_KEY env var
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    rate_limit_burst: int = 20

    # Security Headers
    enable_security_headers: bool = True
    enable_cors: bool = True
    cors_origins: list = None

    # Input Validation
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    max_field_length: int = 10000

    # API Key
    api_key_header: str = "X-API-Key"
    api_keys: list = None

    def __post_init__(self):
        import os
        # Load JWT secret from environment - required in production
        self.jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not self.jwt_secret:
            if os.getenv("SAHOOL_ENV", "local") in ("production", "staging"):
                raise ValueError("JWT_SECRET_KEY environment variable is required in production/staging")
            # Only use fallback in local/development
            self.jwt_secret = "dev-only-secret-not-for-production"
            logger.warning("jwt_secret_fallback", message="Using development JWT secret - NOT FOR PRODUCTION")

        # Initialize lists
        if self.cors_origins is None:
            self.cors_origins = ["*"]
        if self.api_keys is None:
            self.api_keys = []


# Global config instance
security_config = SecurityConfig()


# =============================================================================
# Rate Limiter
# =============================================================================

class RateLimiter:
    """
    Sliding Window Rate Limiter

    Limits requests per IP/user with configurable window.
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or security_config
        self._requests: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    def _get_key(self, request: Request) -> str:
        """Get rate limit key from request"""
        # Use IP address as key
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"rate_limit:{ip}"

    async def is_allowed(self, request: Request) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit

        Returns: (allowed: bool, info: dict)
        """
        async with self._lock:
            key = self._get_key(request)
            now = time.time()
            window_start = now - self.config.rate_limit_window

            # Get requests in current window
            if key not in self._requests:
                self._requests[key] = []

            # Clean old requests
            self._requests[key] = [
                ts for ts in self._requests[key]
                if ts > window_start
            ]

            current_count = len(self._requests[key])
            remaining = max(0, self.config.rate_limit_requests - current_count)

            # Check if allowed
            if current_count >= self.config.rate_limit_requests:
                # Calculate retry after
                oldest = min(self._requests[key]) if self._requests[key] else now
                retry_after = int(oldest + self.config.rate_limit_window - now) + 1

                return False, {
                    "limit": self.config.rate_limit_requests,
                    "remaining": 0,
                    "reset": int(oldest + self.config.rate_limit_window),
                    "retry_after": retry_after,
                }

            # Record this request
            self._requests[key].append(now)

            return True, {
                "limit": self.config.rate_limit_requests,
                "remaining": remaining - 1,
                "reset": int(now + self.config.rate_limit_window),
            }

    async def cleanup(self):
        """Cleanup old entries periodically"""
        async with self._lock:
            now = time.time()
            window_start = now - self.config.rate_limit_window

            keys_to_remove = []
            for key, timestamps in self._requests.items():
                self._requests[key] = [ts for ts in timestamps if ts > window_start]
                if not self._requests[key]:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._requests[key]


# Global rate limiter
rate_limiter = RateLimiter()


# =============================================================================
# Security Headers Middleware
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:;"
        )

        # HSTS (only in production)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


# =============================================================================
# Rate Limit Middleware
# =============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware
    """

    def __init__(self, app, limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.limiter = limiter or rate_limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/live", "/health/ready", "/metrics"]:
            return await call_next(request)

        allowed, info = await self.limiter.is_allowed(request)

        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                path=request.url.path,
                client=request.client.host if request.client else "unknown"
            )
            response = Response(
                content='{"error": "Rate limit exceeded", "message": "Too many requests"}',
                status_code=429,
                media_type="application/json"
            )
            response.headers["Retry-After"] = str(info.get("retry_after", 60))
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(info["reset"])
            return response

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

        return response


# =============================================================================
# Input Validation
# =============================================================================

class InputValidator:
    """
    Input validation utilities
    """

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>",           # XSS
        r"javascript:",              # JS injection
        r"on\w+\s*=",               # Event handlers
        r"{{.*}}",                  # Template injection
        r"\$\{.*\}",                # Template literals
        r";\s*(?:rm|del|format)",   # Command injection
        r"(?:--|;|'|\"|\\x00)",     # SQL injection indicators
    ]

    # Yemen-specific valid patterns
    ARABIC_TEXT = re.compile(r'^[\u0600-\u06FF\u0750-\u077F\s\d\.\,\-\_]+$')
    COORDINATE_LAT = re.compile(r'^-?([1-8]?\d(\.\d+)?|90(\.0+)?)$')
    COORDINATE_LON = re.compile(r'^-?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$')

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 10000) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return str(value)

        # Truncate
        value = value[:max_length]

        # Remove null bytes
        value = value.replace("\x00", "")

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning("dangerous_input_detected", pattern=pattern)
                value = re.sub(pattern, "", value, flags=re.IGNORECASE)

        return value.strip()

    @classmethod
    def validate_coordinate(cls, lat: float, lon: float) -> tuple[bool, str]:
        """Validate coordinates are within Yemen bounds"""
        # Yemen bounds: lat 12-19, lon 42-55
        if not (12.0 <= lat <= 19.0):
            return False, f"Latitude {lat} is outside Yemen bounds (12-19)"
        if not (42.0 <= lon <= 55.0):
            return False, f"Longitude {lon} is outside Yemen bounds (42-55)"
        return True, "Valid"

    @classmethod
    def validate_arabic_text(cls, text: str) -> bool:
        """Validate Arabic text input"""
        return bool(cls.ARABIC_TEXT.match(text))

    @classmethod
    def validate_field_id(cls, field_id: Any) -> tuple[bool, str]:
        """Validate field ID"""
        if isinstance(field_id, str):
            if not field_id.isdigit():
                return False, "Field ID must be a positive integer"
            field_id = int(field_id)

        if not isinstance(field_id, int) or field_id <= 0:
            return False, "Field ID must be a positive integer"

        if field_id > 1000000:
            return False, "Field ID exceeds maximum allowed value"

        return True, "Valid"

    @classmethod
    def validate_region_id(cls, region_id: Any) -> tuple[bool, str]:
        """Validate Yemen region ID (1-20)"""
        try:
            rid = int(region_id)
            if 1 <= rid <= 20:
                return True, "Valid"
            return False, "Region ID must be between 1 and 20"
        except (ValueError, TypeError):
            return False, "Invalid region ID format"

    @classmethod
    def validate_crop_type(cls, crop_type: str) -> tuple[bool, str]:
        """Validate crop type"""
        valid_crops = {
            "قمح", "ذرة", "شعير", "بن", "طماطم",
            "بصل", "بطاطس", "خضروات", "فواكه", "أعلاف",
            "wheat", "corn", "barley", "coffee", "tomato",
            "onion", "potato", "vegetables", "fruits", "fodder"
        }

        if crop_type.lower() in {c.lower() for c in valid_crops}:
            return True, "Valid"
        return False, f"Invalid crop type: {crop_type}"


# =============================================================================
# JWT Authentication
# =============================================================================

class JWTAuth:
    """
    JWT Authentication Handler
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or security_config

    def create_token(
        self,
        user_id: str,
        role: str = "user",
        extra_claims: Optional[dict] = None
    ) -> str:
        """Create JWT token"""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=self.config.jwt_expiry_minutes),
            "iss": "sahool-yemen",
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(
            payload,
            self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm
        )

    def verify_token(self, token: str) -> dict:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                issuer="sahool-yemen"
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    def refresh_token(self, token: str) -> str:
        """Refresh an existing token"""
        payload = self.verify_token(token)
        return self.create_token(
            user_id=payload["sub"],
            role=payload.get("role", "user")
        )


# Global JWT handler
jwt_auth = JWTAuth()

# Security bearer scheme
security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> Optional[dict]:
    """
    Dependency to get current authenticated user

    Returns None if no authentication provided (for optional auth endpoints).
    """
    if credentials is None:
        return None

    return jwt_auth.verify_token(credentials.credentials)


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> dict:
    """
    Dependency to require authentication

    Raises 401 if not authenticated.
    """
    return jwt_auth.verify_token(credentials.credentials)


def require_role(required_role: str):
    """
    Dependency factory to require specific role

    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: dict = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(user: dict = Depends(require_auth)) -> dict:
        if user.get("role") != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{required_role}' required"
            )
        return user
    return role_checker


# =============================================================================
# API Key Authentication
# =============================================================================

class APIKeyAuth:
    """
    API Key Authentication Handler
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or security_config

    def generate_key(self) -> str:
        """Generate a new API key"""
        return f"sk_sahool_{secrets.token_urlsafe(32)}"

    def hash_key(self, key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()

    async def verify_key(self, request: Request) -> bool:
        """Verify API key from request"""
        api_key = request.headers.get(self.config.api_key_header)
        if not api_key:
            return False

        hashed = self.hash_key(api_key)
        return hashed in [self.hash_key(k) for k in self.config.api_keys]


# Global API key handler
api_key_auth = APIKeyAuth()


async def verify_api_key(request: Request) -> bool:
    """Dependency to verify API key"""
    if not await api_key_auth.verify_key(request):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# =============================================================================
# Request Signing
# =============================================================================

class RequestSigner:
    """
    Request signing for webhook callbacks and inter-service communication
    """

    def __init__(self, secret: str):
        self.secret = secret.encode()

    def sign(self, payload: bytes, timestamp: Optional[int] = None) -> str:
        """Sign a payload"""
        timestamp = timestamp or int(time.time())
        message = f"{timestamp}.".encode() + payload
        signature = hmac.new(self.secret, message, hashlib.sha256).hexdigest()
        return f"t={timestamp},v1={signature}"

    def verify(self, payload: bytes, signature: str, max_age: int = 300) -> bool:
        """Verify a signed payload"""
        try:
            parts = dict(p.split("=") for p in signature.split(","))
            timestamp = int(parts["t"])
            expected_sig = parts["v1"]

            # Check timestamp
            if time.time() - timestamp > max_age:
                return False

            # Verify signature
            message = f"{timestamp}.".encode() + payload
            computed = hmac.new(self.secret, message, hashlib.sha256).hexdigest()
            return hmac.compare_digest(computed, expected_sig)
        except (KeyError, ValueError):
            return False


# =============================================================================
# CSRF Protection
# =============================================================================

class CSRFProtection:
    """
    CSRF token generation and validation
    """

    def __init__(self, secret: str = "csrf-secret"):
        self.secret = secret

    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token"""
        timestamp = str(int(time.time()))
        message = f"{session_id}:{timestamp}"
        signature = hmac.new(
            self.secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        return f"{timestamp}:{signature}"

    def verify_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """Verify CSRF token"""
        try:
            timestamp, signature = token.split(":")
            if time.time() - int(timestamp) > max_age:
                return False

            message = f"{session_id}:{timestamp}"
            expected = hmac.new(
                self.secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            return hmac.compare_digest(signature, expected)
        except (ValueError, AttributeError):
            return False


csrf_protection = CSRFProtection()
