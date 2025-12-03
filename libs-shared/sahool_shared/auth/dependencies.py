"""
FastAPI Authentication Dependencies
تبعيات المصادقة لـ FastAPI
"""

from typing import Annotated, Optional
from functools import wraps

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sahool_shared.auth.jwt import TokenPayload, verify_token

# Security scheme
security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Represents an authenticated user from JWT token."""

    def __init__(self, payload: TokenPayload):
        self.user_id = payload.sub
        self.tenant_id = payload.tenant_id
        self.role = payload.role
        self.token_id = payload.jti
        self._payload = payload

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_manager(self) -> bool:
        return self.role in ("admin", "manager")


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> AuthenticatedUser:
    """
    Get the current authenticated user from JWT token.
    الحصول على المستخدم المصادق عليه من توكن JWT
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="لم يتم توفير توكن المصادقة",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_token(credentials.credentials, "access")
        return AuthenticatedUser(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"توكن غير صالح: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]
) -> AuthenticatedUser:
    """
    Get current user and verify they are active.
    الحصول على المستخدم الحالي والتحقق من نشاطه
    """
    # Additional checks can be added here (e.g., check user status in DB)
    return current_user


def require_role(*allowed_roles: str):
    """
    Dependency factory that requires specific roles.
    مصنع التبعيات الذي يتطلب أدواراً محددة

    Usage:
        @app.get("/admin-only")
        async def admin_route(user: AuthenticatedUser = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]
    ) -> AuthenticatedUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"الدور المطلوب: {', '.join(allowed_roles)}. دورك: {current_user.role}",
            )
        return current_user

    return role_checker


def require_tenant(tenant_id: str):
    """
    Dependency factory that requires specific tenant.
    مصنع التبعيات الذي يتطلب مستأجراً محدداً
    """
    async def tenant_checker(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]
    ) -> AuthenticatedUser:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح بالوصول لهذا المستأجر",
            )
        return current_user

    return tenant_checker


class TenantFilter:
    """
    Helper class for filtering queries by tenant.
    فئة مساعدة لتصفية الاستعلامات حسب المستأجر
    """

    def __init__(self, user: AuthenticatedUser):
        self.tenant_id = user.tenant_id
        self.user_id = user.user_id

    def apply(self, query, model):
        """Apply tenant filter to SQLAlchemy query."""
        if hasattr(model, 'tenant_id'):
            return query.filter(model.tenant_id == self.tenant_id)
        return query


# Type aliases for cleaner code
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
ActiveUser = Annotated[AuthenticatedUser, Depends(get_current_active_user)]
AdminUser = Annotated[AuthenticatedUser, Depends(require_role("admin"))]
ManagerUser = Annotated[AuthenticatedUser, Depends(require_role("admin", "manager"))]
