"""
Sahool Yemen - Authentication Module
وحدة المصادقة
"""

from sahool_shared.auth.jwt import (
    JWTHandler,
    TokenPayload,
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token,
)
from sahool_shared.auth.password import (
    hash_password,
    verify_password,
    needs_rehash,
)
from sahool_shared.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    require_role,
    require_tenant,
    AuthenticatedUser,
    TenantFilter,
    CurrentUser,
    ActiveUser,
    AdminUser,
    ManagerUser,
)

__all__ = [
    # JWT
    "JWTHandler",
    "TokenPayload",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "decode_token",
    # Password
    "hash_password",
    "verify_password",
    "needs_rehash",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "require_tenant",
    # Classes
    "AuthenticatedUser",
    "TenantFilter",
    # Type aliases
    "CurrentUser",
    "ActiveUser",
    "AdminUser",
    "ManagerUser",
]
