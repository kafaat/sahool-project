"""
Authentication Schemas
مخططات المصادقة
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field

from sahool_shared.schemas.common import BaseSchema


class LoginRequest(BaseSchema):
    """Login request schema."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseSchema):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds


class RefreshTokenRequest(BaseSchema):
    """Refresh token request."""

    refresh_token: str


class UserResponse(BaseSchema):
    """User response schema."""

    id: UUID
    email: str
    full_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    tenant_id: UUID
    tenant_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    language: str = "ar"
    last_login: Optional[datetime] = None
    created_at: datetime


class UserCreate(BaseSchema):
    """User creation schema."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    role: str = "viewer"
    language: str = "ar"


class UserUpdate(BaseSchema):
    """User update schema."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    language: Optional[str] = None


class PasswordChange(BaseSchema):
    """Password change schema."""

    current_password: str
    new_password: str = Field(..., min_length=8)


class TenantResponse(BaseSchema):
    """Tenant response schema."""

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    plan: str = "free"
    plan_expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime


class TenantCreate(BaseSchema):
    """Tenant creation schema."""

    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=100, pattern="^[a-z0-9-]+$")
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    plan: str = "free"
