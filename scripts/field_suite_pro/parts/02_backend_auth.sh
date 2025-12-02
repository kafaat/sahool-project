#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Part 2: Backend Authentication - JWT, Users, Dependencies
# ═══════════════════════════════════════════════════════════════════════════════

log_info "إنشاء نظام المصادقة..."

# ─────────────────────────────────────────────────────────────────────────────
# User Model
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/models/user.py" << 'EOF'
"""
User Model
نموذج المستخدم
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
import uuid

from app.core.database import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)

    # Tenant/Organization
    tenant_id = Column(Integer, nullable=False, index=True)

    # Role and permissions
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    fields = relationship("Field", back_populates="owner")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class RefreshToken(Base):
    """Refresh token storage"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked = Column(Boolean, default=False)

    user = relationship("User", back_populates="refresh_tokens")
EOF

# ─────────────────────────────────────────────────────────────────────────────
# User Schema
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/schemas/user.py" << 'EOF'
"""
User Schemas - Pydantic v2
مخططات المستخدم
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum
import re


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


# ─────────────────────────────────────────────────────────────────────────────
# Request Schemas
# ─────────────────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = None
    tenant_id: int
    role: UserRole = UserRole.VIEWER

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and not re.match(r"^\+?[1-9]\d{6,14}$", v):
            raise ValueError("Invalid phone number format")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class PasswordReset(BaseModel):
    """Schema for password reset"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


# ─────────────────────────────────────────────────────────────────────────────
# Response Schemas
# ─────────────────────────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    uuid: str
    email: EmailStr
    full_name: str
    phone: Optional[str]
    tenant_id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    """Schema for token refresh"""
    refresh_token: str
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Auth Service
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/services/auth_service.py" << 'EOF'
"""
Authentication Service
خدمة المصادقة
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.user import User, RefreshToken
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.config import settings
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """Authentication service for user management"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if email exists
        existing = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing.scalar_one_or_none():
            raise ValidationError("Email already registered")

        # Create user
        user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            phone=user_data.phone,
            tenant_id=user_data.tenant_id,
            role=user_data.role
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"User registered: {user.email}")
        return user

    async def login(self, credentials: UserLogin) -> Tuple[User, TokenResponse]:
        """Authenticate user and return tokens"""
        # Find user
        result = await self.db.execute(
            select(User).where(User.email == credentials.email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(credentials.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        # Update last login
        await self.db.execute(
            update(User).where(User.id == user.id).values(last_login=datetime.utcnow())
        )

        # Generate tokens
        access_token = create_access_token(
            subject=str(user.id),
            extra_data={
                "email": user.email,
                "tenant_id": user.tenant_id,
                "role": user.role.value
            }
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        # Store refresh token
        token_record = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        )
        self.db.add(token_record)
        await self.db.commit()

        logger.info(f"User logged in: {user.email}")

        return user, TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
        # Verify refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")

        # Check if token exists and not revoked
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.revoked == False
            )
        )
        token_record = result.scalar_one_or_none()

        if not token_record or token_record.expires_at < datetime.utcnow():
            raise AuthenticationError("Refresh token expired or revoked")

        # Get user
        result = await self.db.execute(
            select(User).where(User.id == token_record.user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise AuthenticationError("User not found or deactivated")

        # Revoke old refresh token
        token_record.revoked = True

        # Generate new tokens
        new_access_token = create_access_token(
            subject=str(user.id),
            extra_data={
                "email": user.email,
                "tenant_id": user.tenant_id,
                "role": user.role.value
            }
        )
        new_refresh_token = create_refresh_token(subject=str(user.id))

        # Store new refresh token
        new_token_record = RefreshToken(
            token=new_refresh_token,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        )
        self.db.add(new_token_record)
        await self.db.commit()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def logout(self, user_id: int, refresh_token: Optional[str] = None) -> None:
        """Logout user - revoke refresh tokens"""
        if refresh_token:
            # Revoke specific token
            await self.db.execute(
                update(RefreshToken).where(
                    RefreshToken.token == refresh_token
                ).values(revoked=True)
            )
        else:
            # Revoke all tokens for user
            await self.db.execute(
                update(RefreshToken).where(
                    RefreshToken.user_id == user_id
                ).values(revoked=True)
            )

        await self.db.commit()
        logger.info(f"User logged out: {user_id}")

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Dependencies
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/api/deps.py" << 'EOF'
"""
API Dependencies
اعتماديات API
"""
from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.core.redis import get_redis, RedisManager
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models.user import User, UserRole
from app.services.auth_service import AuthService
from app.services.field_service import FieldService
from app.services.ndvi_service import NDVIService
from app.services.advisor_service import AdvisorService

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    if not credentials:
        raise AuthenticationError("Not authenticated")

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise AuthenticationError("Invalid or expired token")

    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    # Get user from database
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("User account is deactivated")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise AuthorizationError("Inactive user")
    return current_user


def require_role(*roles: UserRole):
    """Dependency factory for role-based access control"""
    async def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.role not in roles and not current_user.is_superuser:
            raise AuthorizationError(
                f"Required role: {', '.join(r.value for r in roles)}"
            )
        return current_user
    return role_checker


def require_admin():
    """Require admin role"""
    return require_role(UserRole.ADMIN)


def require_manager():
    """Require manager or admin role"""
    return require_role(UserRole.ADMIN, UserRole.MANAGER)


# ─────────────────────────────────────────────────────────────────────────────
# Service Dependencies
# ─────────────────────────────────────────────────────────────────────────────
async def get_auth_service(
    db: AsyncSession = Depends(get_db)
) -> AuthService:
    """Get auth service instance"""
    return AuthService(db)


async def get_field_service(
    db: AsyncSession = Depends(get_db),
    redis: RedisManager = Depends(get_redis)
) -> FieldService:
    """Get field service instance"""
    return FieldService(db, redis)


async def get_ndvi_service(
    db: AsyncSession = Depends(get_db),
    redis: RedisManager = Depends(get_redis)
) -> NDVIService:
    """Get NDVI service instance"""
    return NDVIService(db, redis)


async def get_advisor_service(
    db: AsyncSession = Depends(get_db),
    redis: RedisManager = Depends(get_redis)
) -> AdvisorService:
    """Get advisor service instance"""
    return AdvisorService(db, redis)
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Auth API Endpoints
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/api/v1/endpoints/auth.py" << 'EOF'
"""
Authentication API Endpoints
نقاط نهاية المصادقة
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import Any

from app.schemas.user import (
    UserCreate, UserLogin, UserResponse,
    TokenResponse, TokenRefresh, PasswordChange
)
from app.services.auth_service import AuthService
from app.api.deps import get_auth_service, get_current_user
from app.models.user import User
from app.core.logging import get_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    تسجيل مستخدم جديد
    Register a new user
    """
    user = await auth_service.register(user_data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    تسجيل الدخول والحصول على التوكن
    Login and get access token
    """
    user, tokens = await auth_service.login(credentials)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    تجديد التوكن
    Refresh access token
    """
    tokens = await auth_service.refresh_tokens(token_data.refresh_token)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> None:
    """
    تسجيل الخروج
    Logout and revoke tokens
    """
    await auth_service.logout(current_user.id)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    الحصول على بيانات المستخدم الحالي
    Get current user info
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    تحديث بيانات المستخدم الحالي
    Update current user info
    """
    # Implementation for password change
    pass
EOF

log_success "تم إنشاء نظام المصادقة"
