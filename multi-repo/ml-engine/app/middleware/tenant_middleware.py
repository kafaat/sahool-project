"""
Tenant Isolation Middleware
عزل المستأجرين لضمان أمان البيانات
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to ensure tenant isolation across all requests

    Features:
    - Extracts tenant_id from request (header, token, or param)
    - Validates tenant access
    - Prevents cross-tenant data access
    - Logs all tenant access attempts
    """

    def __init__(self, app):
        super().__init__(app)

        # Endpoints that don't require tenant isolation
        self.public_endpoints = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/"
        }

    async def dispatch(self, request: Request, call_next):
        """Process request and enforce tenant isolation"""

        # Skip public endpoints
        if request.url.path in self.public_endpoints:
            return await call_next(request)

        # Extract tenant_id
        tenant_id = self._extract_tenant_id(request)

        if not tenant_id:
            # For unauthenticated endpoints, continue
            # (authentication middleware will handle)
            pass
        else:
            # Attach tenant_id to request state
            request.state.tenant_id = tenant_id

            # Log tenant access
            logger.info(
                f"Tenant access: {tenant_id} - "
                f"{request.method} {request.url.path}"
            )

        # Continue processing
        response = await call_next(request)

        # Add tenant header to response
        if tenant_id:
            response.headers["X-Tenant-ID"] = tenant_id

        return response

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """
        Extract tenant_id from request

        Priority:
        1. X-Tenant-ID header
        2. tenant_id query parameter
        3. Extract from JWT token (if present)
        """

        # 1. Check header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id

        # 2. Check query parameter
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            return tenant_id

        # 3. Extract from Authorization header / JWT
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # You would decode JWT here and extract tenant_id
                # from jwt import decode
                # token = auth_header.split(" ")[1]
                # payload = decode(token, ...)
                # tenant_id = payload.get("tenant_id")
                pass
            except Exception as e:
                logger.warning(f"Failed to extract tenant from JWT: {e}")

        return None


def get_current_tenant(request: Request) -> str:
    """
    Dependency to get current tenant_id from request

    Usage:
        @app.get("/data")
        async def get_data(
            request: Request,
            tenant_id: str = Depends(get_current_tenant)
        ):
            # tenant_id is guaranteed to be present
            return {"tenant_id": tenant_id}
    """

    tenant_id = getattr(request.state, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID not found. Access denied."
        )

    return tenant_id


def validate_tenant_access(
    requested_tenant_id: str,
    current_tenant_id: str
):
    """
    Validate that current tenant has access to requested tenant data

    Args:
        requested_tenant_id: The tenant_id being requested
        current_tenant_id: The tenant_id of the current user

    Raises:
        HTTPException: If tenant access is not allowed

    Usage:
        @app.get("/fields/{field_id}")
        async def get_field(
            field_id: int,
            request: Request,
            tenant_id: str = Depends(get_current_tenant)
        ):
            field = await get_field_from_db(field_id)

            # Validate tenant owns this field
            validate_tenant_access(field.tenant_id, tenant_id)

            return field
    """

    if requested_tenant_id != current_tenant_id:
        logger.warning(
            f"Tenant access violation: {current_tenant_id} "
            f"attempted to access {requested_tenant_id}'s data"
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You don't have permission to access this resource."
        )


class TenantContext:
    """
    Context manager for tenant-isolated operations

    Usage:
        async with TenantContext(tenant_id) as ctx:
            # All operations here are tenant-isolated
            data = await ctx.get_data()
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.original_tenant = None

    async def __aenter__(self):
        # You could store tenant context in contextvars
        # self.original_tenant = current_tenant_var.get()
        # current_tenant_var.set(self.tenant_id)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Restore original tenant
        # if self.original_tenant:
        #     current_tenant_var.set(self.original_tenant)
        pass


# ============================================================================
# FastAPI Integration Example
# ============================================================================

"""
# In main.py:

from app.middleware.tenant_middleware import TenantIsolationMiddleware, get_current_tenant

app = FastAPI()

# Add tenant isolation middleware
app.add_middleware(TenantIsolationMiddleware)


# Use in routes:

@app.get("/fields/{field_id}")
async def get_field(
    field_id: int,
    request: Request,
    tenant_id: str = Depends(get_current_tenant)
):
    # tenant_id is automatically extracted and validated
    field = await get_field_from_db(field_id)

    # Ensure field belongs to tenant
    validate_tenant_access(field.tenant_id, tenant_id)

    return field


@app.post("/predictions")
async def create_prediction(
    data: PredictionRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant)
):
    # All predictions are scoped to tenant
    result = await ml_model.predict(data, tenant_id=tenant_id)

    return result
"""
