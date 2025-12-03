"""
JWT Token Handling
معالجة توكنات JWT
"""

from datetime import datetime, timedelta
from typing import Any, Optional
import uuid

from jose import JWTError, jwt
from pydantic import BaseModel


class TokenPayload(BaseModel):
    """JWT Token payload structure."""
    sub: str  # Subject (user_id)
    tenant_id: str
    role: str
    type: str = "access"  # access or refresh
    exp: datetime
    iat: datetime
    jti: str  # Unique token ID

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class JWTHandler:
    """
    JWT Token handler for authentication.
    معالج توكنات JWT للمصادقة
    """

    def __init__(
        self,
        secret_key: str,
        refresh_secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        self.secret_key = secret_key
        self.refresh_secret_key = refresh_secret_key or secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        role: str,
        extra_claims: Optional[dict[str, Any]] = None,
    ) -> str:
        """Create a new access token."""
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "role": role,
            "type": "access",
            "exp": expires,
            "iat": now,
            "jti": str(uuid.uuid4()),
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str,
        role: str,
    ) -> str:
        """Create a new refresh token."""
        now = datetime.utcnow()
        expires = now + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "role": role,
            "type": "refresh",
            "exp": expires,
            "iat": now,
            "jti": str(uuid.uuid4()),
        }

        return jwt.encode(payload, self.refresh_secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, token_type: str = "access") -> TokenPayload:
        """
        Verify and decode a token.
        Raises JWTError if token is invalid.
        """
        secret = self.secret_key if token_type == "access" else self.refresh_secret_key

        try:
            payload = jwt.decode(token, secret, algorithms=[self.algorithm])

            if payload.get("type") != token_type:
                raise JWTError(f"Invalid token type. Expected {token_type}")

            return TokenPayload(**payload)

        except JWTError as e:
            raise JWTError(f"Token verification failed: {str(e)}")

    def decode_token(self, token: str, verify: bool = True) -> dict[str, Any]:
        """Decode token without full verification (for inspection)."""
        options = {"verify_signature": verify, "verify_exp": verify}
        return jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
            options=options
        )

    def create_token_pair(
        self,
        user_id: str,
        tenant_id: str,
        role: str,
    ) -> dict[str, str]:
        """Create both access and refresh tokens."""
        return {
            "access_token": self.create_access_token(user_id, tenant_id, role),
            "refresh_token": self.create_refresh_token(user_id, tenant_id, role),
            "token_type": "bearer",
        }


# Default handler instance (configure with environment variables)
_jwt_handler: Optional[JWTHandler] = None


def get_jwt_handler() -> JWTHandler:
    """Get or create the default JWT handler."""
    global _jwt_handler
    if _jwt_handler is None:
        import os
        _jwt_handler = JWTHandler(
            secret_key=os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production"),
            refresh_secret_key=os.getenv("JWT_REFRESH_SECRET_KEY"),
            access_token_expire_minutes=int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7")),
        )
    return _jwt_handler


def create_access_token(user_id: str, tenant_id: str, role: str, **kwargs) -> str:
    """Convenience function to create access token."""
    return get_jwt_handler().create_access_token(user_id, tenant_id, role, **kwargs)


def create_refresh_token(user_id: str, tenant_id: str, role: str) -> str:
    """Convenience function to create refresh token."""
    return get_jwt_handler().create_refresh_token(user_id, tenant_id, role)


def verify_token(token: str, token_type: str = "access") -> TokenPayload:
    """Convenience function to verify token."""
    return get_jwt_handler().verify_token(token, token_type)


def decode_token(token: str, verify: bool = True) -> dict[str, Any]:
    """Convenience function to decode token."""
    return get_jwt_handler().decode_token(token, verify)
