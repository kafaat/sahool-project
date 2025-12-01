#!/usr/bin/env python3
"""
Sahool Geo-Core Security Module
Enhanced security with tenant isolation and spatial data protection
Version: 3.2.0
"""
import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from functools import wraps

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

# ===================================================================
# CONFIGURATION
# ===================================================================

class SecurityConfig:
    """Centralized security configuration"""

    # JWT Configuration
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "7"))

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_HIGH_FREQUENCY = int(os.getenv("RATE_LIMIT_HIGH_FREQ", "10"))
    RATE_LIMIT_EXPORT = int(os.getenv("RATE_LIMIT_EXPORT", "5"))

    # CORS
    ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    # Spatial Query Limits
    MAX_QUERY_DISTANCE = 100000  # meters (100 km)
    MAX_FIELDS_PER_REQUEST = 1000
    MIN_POLYGON_VERTICES = 3
    MAX_POLYGON_VERTICES = 1000
    MAX_AREA_HECTARES = 10000  # 100 km²

    # Password Policy
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_SPECIAL_CHAR = True
    REQUIRE_UPPERCASE = True
    REQUIRE_NUMBER = True

    # Encryption
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

    # Audit Logging
    ENABLE_AUDIT_LOG = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"

# Global config instance
security_config = SecurityConfig()

# ===================================================================
# DATA MODELS
# ===================================================================

class TokenData(BaseModel):
    """Enhanced token data with tenant isolation and spatial permissions"""

    user_id: str = Field(..., description="Unique user identifier")
    tenant_id: str = Field(..., description="Tenant identifier for isolation")
    role: str = Field(..., description="User role (admin, manager, viewer)")
    permissions: List[str] = Field(default_factory=list, description="Specific permissions")
    spatial_access_level: str = Field(default="own", description="Spatial access level")
    allowed_regions: Optional[List[str]] = Field(None, description="Allowed region IDs")
    email: Optional[str] = None

    @validator('spatial_access_level')
    def validate_access_level(cls, v):
        """Validate spatial access level"""
        valid_levels = ['own', 'region', 'tenant', 'global']
        if v not in valid_levels:
            raise ValueError(f'Invalid spatial access level. Must be one of: {valid_levels}')
        return v

    @validator('role')
    def validate_role(cls, v):
        """Validate user role"""
        valid_roles = ['admin', 'manager', 'user', 'viewer', 'api_client']
        if v not in valid_roles:
            raise ValueError(f'Invalid role. Must be one of: {valid_roles}')
        return v


class SpatialQueryLimits(BaseModel):
    """Limits for spatial queries to prevent abuse"""

    max_distance: int = Field(default=security_config.MAX_QUERY_DISTANCE)
    max_results: int = Field(default=security_config.MAX_FIELDS_PER_REQUEST)
    max_vertices: int = Field(default=security_config.MAX_POLYGON_VERTICES)
    max_area_ha: float = Field(default=security_config.MAX_AREA_HECTARES)

# ===================================================================
# TENANT ISOLATION
# ===================================================================

class TenantIsolation:
    """Tenant isolation utilities for spatial queries"""

    @staticmethod
    def validate_tenant_access(token_data: TokenData, requested_tenant_id: str) -> bool:
        """Validate user has access to requested tenant"""

        # Admin can access all tenants
        if token_data.role == 'admin':
            return True

        # User must match tenant
        if token_data.tenant_id != requested_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Cannot access tenant: {requested_tenant_id}"
            )

        return True

    @staticmethod
    def add_tenant_filter(query: str, tenant_id: str) -> str:
        """Safely add tenant filter to SQL query (use parameterized queries!)"""

        # This is a template - always use parameterized queries in actual implementation
        if "WHERE" in query.upper():
            return query.replace("WHERE", f"WHERE tenant_id = :tenant_id AND", 1)
        else:
            # Find FROM clause and add WHERE
            from_idx = query.upper().find("FROM")
            if from_idx != -1:
                # Find next clause (ORDER, GROUP, LIMIT, etc.)
                next_clause_keywords = ["ORDER BY", "GROUP BY", "LIMIT", "OFFSET", ";"]
                next_clause_idx = len(query)

                for keyword in next_clause_keywords:
                    idx = query.upper().find(keyword, from_idx)
                    if idx != -1 and idx < next_clause_idx:
                        next_clause_idx = idx

                return query[:next_clause_idx] + f" WHERE tenant_id = :tenant_id " + query[next_clause_idx:]

        return query

    @staticmethod
    def validate_spatial_access(
        token_data: TokenData,
        field_tenant_id: str,
        field_region: Optional[str] = None
    ) -> bool:
        """Validate spatial access based on user's spatial_access_level"""

        # Global access (admin only)
        if token_data.spatial_access_level == 'global' and token_data.role == 'admin':
            return True

        # Tenant-level access
        if token_data.spatial_access_level == 'tenant':
            return token_data.tenant_id == field_tenant_id

        # Region-level access
        if token_data.spatial_access_level == 'region':
            if not field_region or not token_data.allowed_regions:
                return False
            return field_region in token_data.allowed_regions

        # Own-level access (default)
        return token_data.tenant_id == field_tenant_id

# ===================================================================
# RATE LIMITING
# ===================================================================

class GeoRateLimiter:
    """Custom rate limiter for spatial endpoints"""

    def __init__(self):
        self.limiter = Limiter(key_func=get_remote_address)

    def get_limit(self, endpoint_type: str = "standard") -> str:
        """Get rate limit string based on endpoint type"""

        limits = {
            "standard": f"{security_config.RATE_LIMIT_PER_MINUTE}/minute",
            "heavy": f"{security_config.RATE_LIMIT_HIGH_FREQUENCY}/minute",
            "export": f"{security_config.RATE_LIMIT_EXPORT}/minute",
            "search": "30/minute",
            "create": "20/minute",
            "update": "30/minute",
            "delete": "10/minute",
        }

        return limits.get(endpoint_type, limits["standard"])

# Global rate limiter instance
geo_limiter = GeoRateLimiter()

# ===================================================================
# SECURITY MANAGER
# ===================================================================

class SecurityManager:
    """Centralized security manager for authentication and authorization"""

    def __init__(self):
        self.security = HTTPBearer()
        self.config = security_config

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create secure JWT access token with spatial permissions"""

        to_encode = data.copy()

        # Set expiration
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Add standard claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": "sahool-geo-core",
            "version": "3.2.0",
            "aud": "spatial-data-access",
            "type": "access"
        })

        # Encode token
        encoded_jwt = jwt.encode(
            to_encode,
            self.config.SECRET_KEY,
            algorithm=self.config.ALGORITHM,
            headers={"kid": "geo-core-v1", "typ": "JWT"}
        )

        return encoded_jwt

    def create_refresh_token(self, user_id: str, tenant_id: str) -> str:
        """Create refresh token for token renewal"""

        data = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "type": "refresh"
        }

        return self.create_access_token(
            data,
            expires_delta=timedelta(days=self.config.REFRESH_TOKEN_EXPIRE_DAYS)
        )

    def verify_token(self, token: str) -> TokenData:
        """Verify JWT token and extract spatial permissions"""

        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                self.config.SECRET_KEY,
                algorithms=[self.config.ALGORITHM],
                issuer="sahool-geo-core",
                audience="spatial-data-access"
            )

            # Verify token type
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type. Access token required."
                )

            # Extract token data
            token_data = TokenData(
                user_id=payload["sub"],
                tenant_id=payload["tenant_id"],
                role=payload.get("role", "user"),
                permissions=payload.get("permissions", []),
                spatial_access_level=payload.get("spatial_access_level", "own"),
                allowed_regions=payload.get("allowed_regions"),
                email=payload.get("email")
            )

            return token_data

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please re-authenticate.",
                headers={"WWW-Authenticate": 'Bearer realm="geo-core", error="token_expired"'},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": 'Bearer realm="geo-core", error="invalid_token"'},
            )
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token missing required field: {str(e)}",
                headers={"WWW-Authenticate": 'Bearer realm="geo-core", error="malformed_token"'},
            )

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials
    ) -> TokenData:
        """FastAPI dependency - get current authenticated user"""
        return self.verify_token(credentials.credentials)

    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 (use bcrypt in production!)"""
        # TODO: Replace with bcrypt or argon2 in production
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(plain_password) == hashed_password

# Global security manager instance
security_manager = SecurityManager()

# ===================================================================
# FASTAPI DEPENDENCIES
# ===================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_manager.security)
) -> TokenData:
    """FastAPI dependency for authentication"""
    return await security_manager.get_current_user(credentials)


def require_permission(permission: str):
    """RBAC - Require specific permission decorator"""

    async def permission_checker(current_user: TokenData = Depends(get_current_user)):
        if permission not in current_user.permissions and current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required. Your permissions: {current_user.permissions}"
            )
        return current_user

    return permission_checker


def require_role(allowed_roles: List[str]):
    """RBAC - Require specific role(s)"""

    async def role_checker(current_user: TokenData = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles {allowed_roles} required. Your role: {current_user.role}"
            )
        return current_user

    return role_checker


def require_spatial_access(level: str):
    """Spatial access control - require minimum spatial access level"""

    async def spatial_checker(current_user: TokenData = Depends(get_current_user)):
        access_levels = ['own', 'region', 'tenant', 'global']

        try:
            user_level_idx = access_levels.index(current_user.spatial_access_level)
            required_level_idx = access_levels.index(level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid spatial access level"
            )

        if user_level_idx < required_level_idx:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Spatial access level '{level}' required. Your level: {current_user.spatial_access_level}"
            )

        return current_user

    return spatial_checker


def validate_tenant_access(tenant_id: str):
    """Validate tenant access decorator"""

    async def tenant_checker(current_user: TokenData = Depends(get_current_user)):
        TenantIsolation.validate_tenant_access(current_user, tenant_id)
        return current_user

    return tenant_checker

# ===================================================================
# SPATIAL VALIDATION
# ===================================================================

class SpatialValidator:
    """Validate spatial data to prevent abuse and errors"""

    @staticmethod
    def validate_geometry(geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GeoJSON geometry"""

        # Check type
        if "type" not in geometry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geometry must have 'type' field"
            )

        # Check coordinates
        if "coordinates" not in geometry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geometry must have 'coordinates' field"
            )

        # Validate polygon
        if geometry["type"] in ["Polygon", "MultiPolygon"]:
            coords = geometry["coordinates"]

            # Count vertices
            if geometry["type"] == "Polygon":
                num_vertices = len(coords[0]) if coords else 0
            else:  # MultiPolygon
                num_vertices = sum(len(poly[0]) for poly in coords if poly)

            # Check limits
            if num_vertices < security_config.MIN_POLYGON_VERTICES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Polygon must have at least {security_config.MIN_POLYGON_VERTICES} vertices"
                )

            if num_vertices > security_config.MAX_POLYGON_VERTICES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Polygon cannot exceed {security_config.MAX_POLYGON_VERTICES} vertices"
                )

        return geometry

    @staticmethod
    def validate_query_distance(distance: float) -> float:
        """Validate spatial query distance"""

        if distance < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Distance cannot be negative"
            )

        if distance > security_config.MAX_QUERY_DISTANCE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Distance cannot exceed {security_config.MAX_QUERY_DISTANCE} meters"
            )

        return distance

    @staticmethod
    def validate_pagination(page: int, page_size: int) -> tuple:
        """Validate pagination parameters"""

        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be >= 1"
            )

        if page_size < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be >= 1"
            )

        if page_size > security_config.MAX_FIELDS_PER_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Page size cannot exceed {security_config.MAX_FIELDS_PER_REQUEST}"
            )

        return page, page_size

# Global validator instance
spatial_validator = SpatialValidator()

# ===================================================================
# AUDIT LOGGING
# ===================================================================

class AuditLogger:
    """Audit logging for security-sensitive operations"""

    @staticmethod
    def log_access(
        user_id: str,
        tenant_id: str,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log access to spatial data"""

        if not security_config.ENABLE_AUDIT_LOG:
            return

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "tenant_id": tenant_id,
            "action": action,
            "resource": resource,
            "details": details or {}
        }

        # TODO: Implement actual logging (database, file, external service)
        # For now, just print (replace with proper logging)
        # logger.info(f"AUDIT: {log_entry}")
        pass

# Global audit logger
audit_logger = AuditLogger()

# ===================================================================
# EXPORTS
# ===================================================================

__all__ = [
    'SecurityConfig',
    'TokenData',
    'SpatialQueryLimits',
    'TenantIsolation',
    'GeoRateLimiter',
    'SecurityManager',
    'SpatialValidator',
    'AuditLogger',
    'security_config',
    'security_manager',
    'geo_limiter',
    'spatial_validator',
    'audit_logger',
    'get_current_user',
    'require_permission',
    'require_role',
    'require_spatial_access',
    'validate_tenant_access',
]
