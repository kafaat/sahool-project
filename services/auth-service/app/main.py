"""
Auth Service - خدمة المصادقة
Sahool Yemen v9.0.0

Authentication and authorization service for the platform.
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field, validator
from prometheus_client import Counter, Histogram, generate_latest
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

import sys
sys.path.insert(0, "/app/libs-shared")

from sahool_shared.models import User, Tenant
from sahool_shared.models.user import UserRole, TenantPlan
from sahool_shared.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    AuthenticatedUser,
)
from sahool_shared.utils import get_db, setup_logging, get_logger
from sahool_shared.schemas.common import HealthResponse

# Metrics
REQUEST_COUNT = Counter("auth_requests_total", "Total requests", ["endpoint", "status"])
REQUEST_LATENCY = Histogram("auth_request_latency_seconds", "Request latency", ["endpoint"])
LOGIN_ATTEMPTS = Counter("auth_login_attempts_total", "Login attempts", ["status"])

logger = get_logger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================

class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    """Registration request model."""
    email: EmailStr
    password: str = Field(
        ...,
        min_length=12,
        max_length=128,
        description="Password must be 12-128 chars with uppercase, lowercase, number, and special char"
    )
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = None
    tenant_name: Optional[str] = None  # If creating new tenant

    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets security requirements."""
        import re
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>)')
        return v


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class UserResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    role: str
    tenant_id: str
    tenant_name: str
    is_active: bool
    is_verified: bool
    language: str
    created_at: datetime
    last_login: Optional[datetime]


class UpdateProfileRequest(BaseModel):
    """Update profile request."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    phone: Optional[str] = None
    language: Optional[str] = Field(None, pattern="^(ar|en)$")


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class TenantResponse(BaseModel):
    """Tenant response."""
    id: str
    name: str
    slug: str
    email: Optional[str]
    plan: str
    is_active: bool
    created_at: datetime


class CreateTenantRequest(BaseModel):
    """Create tenant request."""
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=100, pattern="^[a-z0-9-]+$")
    email: Optional[EmailStr] = None
    description: Optional[str] = None


# =============================================================================
# Application Setup
# =============================================================================

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
CORS_ALLOW_CREDENTIALS = bool(CORS_ORIGINS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging(service_name="auth-service")
    logger.info("auth_service_starting", version="9.0.0")
    yield
    logger.info("auth_service_stopping")


app = FastAPI(
    title="Sahool Auth Service",
    description="خدمة المصادقة والتفويض لمنصة سهول اليمن",
    version="9.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health & Metrics
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="9.0.0",
        service="auth-service"
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


# =============================================================================
# Authentication Endpoints
# =============================================================================

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return tokens.
    تسجيل الدخول والحصول على توكنات المصادقة
    """
    with REQUEST_LATENCY.labels(endpoint="login").time():
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == request.email.lower())
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(request.password, user.password_hash):
            LOGIN_ATTEMPTS.labels(status="failed").inc()
            logger.warning("login_failed", email=request.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="بيانات الدخول غير صحيحة",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            LOGIN_ATTEMPTS.labels(status="inactive").inc()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="الحساب غير مفعل",
            )

        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()

        # Create tokens
        access_token = create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role,
        )
        refresh_token = create_refresh_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role,
        )

        LOGIN_ATTEMPTS.labels(status="success").inc()
        REQUEST_COUNT.labels(endpoint="login", status="success").inc()
        logger.info("login_success", user_id=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )


@app.post("/api/v1/auth/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.
    تسجيل مستخدم جديد
    """
    with REQUEST_LATENCY.labels(endpoint="register").time():
        # Check if email exists
        result = await db.execute(
            select(User).where(User.email == request.email.lower())
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="البريد الإلكتروني مسجل مسبقاً",
            )

        # Get or create tenant
        if request.tenant_name:
            # Create new tenant
            import re
            slug = re.sub(r'[^a-z0-9-]', '-', request.tenant_name.lower())
            slug = re.sub(r'-+', '-', slug).strip('-')

            tenant = Tenant(
                name=request.tenant_name,
                slug=slug,
                plan=TenantPlan.FREE.value,
            )
            db.add(tenant)
            await db.flush()
            user_role = UserRole.ADMIN.value  # First user is admin
        else:
            # Use default tenant or raise error
            result = await db.execute(
                select(Tenant).where(Tenant.slug == "default").limit(1)
            )
            tenant = result.scalar_one_or_none()

            if not tenant:
                # Create default tenant
                tenant = Tenant(
                    name="Default Organization",
                    slug="default",
                    plan=TenantPlan.FREE.value,
                )
                db.add(tenant)
                await db.flush()

            user_role = UserRole.VIEWER.value

        # Create user
        user = User(
            email=request.email.lower(),
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            phone=request.phone,
            role=user_role,
            tenant_id=tenant.id,
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        await db.commit()

        # Create tokens
        access_token = create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role,
        )
        refresh_token = create_refresh_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role,
        )

        REQUEST_COUNT.labels(endpoint="register", status="success").inc()
        logger.info("user_registered", user_id=str(user.id), tenant_id=str(tenant.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )


@app.post("/api/v1/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token.
    تجديد توكن الوصول
    """
    with REQUEST_LATENCY.labels(endpoint="refresh").time():
        try:
            payload = verify_token(request.refresh_token, "refresh")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="توكن التجديد غير صالح",
            )

        # Verify user still exists and is active
        result = await db.execute(
            select(User).where(User.id == UUID(payload.sub))
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="المستخدم غير موجود أو غير مفعل",
            )

        # Create new tokens
        access_token = create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role,
        )
        new_refresh_token = create_refresh_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role,
        )

        REQUEST_COUNT.labels(endpoint="refresh", status="success").inc()

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )


# =============================================================================
# User Profile Endpoints
# =============================================================================

@app.get("/api/v1/users/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user profile.
    الحصول على الملف الشخصي للمستخدم الحالي
    """
    result = await db.execute(
        select(User, Tenant)
        .join(Tenant, User.tenant_id == Tenant.id)
        .where(User.id == UUID(current_user.user_id))
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود",
        )

    user, tenant = row

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        tenant_id=str(user.tenant_id),
        tenant_name=tenant.name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        language=user.language,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@app.patch("/api/v1/users/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user profile.
    تحديث الملف الشخصي
    """
    result = await db.execute(
        select(User, Tenant)
        .join(Tenant, User.tenant_id == Tenant.id)
        .where(User.id == UUID(current_user.user_id))
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود",
        )

    user, tenant = row

    # Update fields
    if request.full_name:
        user.full_name = request.full_name
    if request.phone is not None:
        user.phone = request.phone
    if request.language:
        user.language = request.language

    await db.commit()

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        tenant_id=str(user.tenant_id),
        tenant_name=tenant.name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        language=user.language,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@app.post("/api/v1/users/me/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change password.
    تغيير كلمة المرور
    """
    result = await db.execute(
        select(User).where(User.id == UUID(current_user.user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود",
        )

    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور الحالية غير صحيحة",
        )

    user.password_hash = hash_password(request.new_password)
    await db.commit()

    logger.info("password_changed", user_id=str(user.id))

    return {"message": "تم تغيير كلمة المرور بنجاح"}


# =============================================================================
# Tenant Endpoints
# =============================================================================

@app.get("/api/v1/tenants/me", response_model=TenantResponse)
async def get_current_tenant(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current tenant info.
    الحصول على معلومات المنظمة الحالية
    """
    result = await db.execute(
        select(Tenant).where(Tenant.id == UUID(current_user.tenant_id))
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المنظمة غير موجودة",
        )

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        email=tenant.email,
        plan=tenant.plan,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
    )


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
