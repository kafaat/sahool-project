"""
Centralized Error Handling Framework
تقليل الأخطاء من خلال معالجة مركزية وموحدة
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
import logging
import traceback
import uuid
from datetime import datetime

# ===================================================================
# ERROR CODES & TYPES
# ===================================================================

class ErrorCode(str, Enum):
    """Standardized error codes"""

    # Client Errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INVALID_GEOMETRY = "INVALID_GEOMETRY"
    INVALID_SPATIAL_QUERY = "INVALID_SPATIAL_QUERY"

    # Server Errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    ML_MODEL_ERROR = "ML_MODEL_ERROR"

    # Business Logic Errors
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    TENANT_ACCESS_DENIED = "TENANT_ACCESS_DENIED"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"          # Minor issues, user can continue
    MEDIUM = "medium"    # Degraded functionality
    HIGH = "high"        # Feature unavailable
    CRITICAL = "critical"  # Service down


# ===================================================================
# ERROR MODELS
# ===================================================================

class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized error response"""

    error_id: str = Field(..., description="Unique error identifier for tracking")
    error_code: ErrorCode
    message: str = Field(..., description="Human-readable error message in Arabic")
    message_en: str = Field(..., description="Human-readable error message in English")
    details: Optional[List[ErrorDetail]] = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = None

    # For debugging (only in development)
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


# ===================================================================
# CUSTOM EXCEPTIONS
# ===================================================================

class SahoolException(Exception):
    """Base exception for all Sahool errors"""

    def __init__(
        self,
        error_code: ErrorCode,
        message_ar: str,
        message_en: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[List[ErrorDetail]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        context: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message_ar = message_ar
        self.message_en = message_en
        self.severity = severity
        self.details = details or []
        self.status_code = status_code
        self.context = context or {}
        super().__init__(message_ar)


class ValidationException(SahoolException):
    """Validation errors"""
    def __init__(self, message_ar: str, message_en: str, details: List[ErrorDetail] = None):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message_ar=message_ar,
            message_en=message_en,
            severity=ErrorSeverity.LOW,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class AuthenticationException(SahoolException):
    """Authentication errors"""
    def __init__(self, message_ar: str = "فشلت عملية المصادقة", message_en: str = "Authentication failed"):
        super().__init__(
            error_code=ErrorCode.AUTHENTICATION_ERROR,
            message_ar=message_ar,
            message_en=message_en,
            severity=ErrorSeverity.HIGH,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(SahoolException):
    """Authorization errors"""
    def __init__(self, message_ar: str = "ليس لديك صلاحية للوصول", message_en: str = "Access denied"):
        super().__init__(
            error_code=ErrorCode.AUTHORIZATION_ERROR,
            message_ar=message_ar,
            message_en=message_en,
            severity=ErrorSeverity.HIGH,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundException(SahoolException):
    """Resource not found errors"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message_ar=f"{resource_type} غير موجود: {resource_id}",
            message_en=f"{resource_type} not found: {resource_id}",
            severity=ErrorSeverity.LOW,
            status_code=status.HTTP_404_NOT_FOUND,
            context={"resource_type": resource_type, "resource_id": resource_id}
        )


class DatabaseException(SahoolException):
    """Database errors"""
    def __init__(self, operation: str, original_error: Exception):
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            message_ar=f"خطأ في قاعدة البيانات أثناء {operation}",
            message_en=f"Database error during {operation}",
            severity=ErrorSeverity.CRITICAL,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            context={"operation": operation, "original_error": str(original_error)}
        )


class SpatialDataException(SahoolException):
    """Spatial data errors"""
    def __init__(self, message_ar: str, message_en: str, details: List[ErrorDetail] = None):
        super().__init__(
            error_code=ErrorCode.INVALID_GEOMETRY,
            message_ar=message_ar,
            message_en=message_en,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class MLModelException(SahoolException):
    """ML model errors"""
    def __init__(self, model_name: str, operation: str, original_error: Exception):
        super().__init__(
            error_code=ErrorCode.ML_MODEL_ERROR,
            message_ar=f"خطأ في نموذج {model_name} أثناء {operation}",
            message_en=f"ML model error in {model_name} during {operation}",
            severity=ErrorSeverity.HIGH,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            context={
                "model_name": model_name,
                "operation": operation,
                "original_error": str(original_error)
            }
        )


class TenantAccessException(SahoolException):
    """Tenant access violation"""
    def __init__(self, tenant_id: str, resource_id: str):
        super().__init__(
            error_code=ErrorCode.TENANT_ACCESS_DENIED,
            message_ar=f"لا يمكنك الوصول إلى هذا المورد من مستأجر آخر",
            message_en=f"Cannot access resource from different tenant",
            severity=ErrorSeverity.HIGH,
            status_code=status.HTTP_403_FORBIDDEN,
            context={"tenant_id": tenant_id, "resource_id": resource_id}
        )


# ===================================================================
# ERROR LOGGER
# ===================================================================

class ErrorLogger:
    """Centralized error logging with context"""

    def __init__(self):
        self.logger = logging.getLogger("sahool.errors")
        self.logger.setLevel(logging.ERROR)

        # File handler for errors
        handler = logging.FileHandler("/var/log/sahool/errors.log")
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)

    def log_error(
        self,
        error: Exception,
        error_id: str,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ):
        """Log error with full context"""

        context = {
            "error_id": error_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "user_id": user_id,
            "tenant_id": tenant_id
        }

        if request:
            context.update({
                "method": request.method,
                "url": str(request.url),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            })

        if isinstance(error, SahoolException):
            context.update({
                "error_code": error.error_code,
                "severity": error.severity,
                "context": error.context
            })

        # Log with full traceback
        self.logger.error(
            f"Error occurred: {error_id}",
            extra=context,
            exc_info=True
        )

        # Send to external monitoring (optional)
        # self._send_to_sentry(error, context)


error_logger = ErrorLogger()


# ===================================================================
# ERROR HANDLERS
# ===================================================================

async def sahool_exception_handler(request: Request, exc: SahoolException) -> JSONResponse:
    """Handle SahoolException"""

    error_id = str(uuid.uuid4())

    # Extract user context
    user_id = None
    tenant_id = None
    if hasattr(request.state, "user"):
        user_id = request.state.user.user_id
        tenant_id = request.state.user.tenant_id

    # Log error
    error_logger.log_error(exc, error_id, request, user_id, tenant_id)

    # Build response
    error_response = ErrorResponse(
        error_id=error_id,
        error_code=exc.error_code,
        message=exc.message_ar,
        message_en=exc.message_en,
        details=exc.details,
        severity=exc.severity,
        path=str(request.url.path)
    )

    # Add stack trace in development
    import os
    if os.getenv("ENVIRONMENT") == "development":
        error_response.stack_trace = traceback.format_exc()
        error_response.context = exc.context

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict(exclude_none=True)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""

    error_id = str(uuid.uuid4())

    # Convert validation errors to ErrorDetail
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        details.append(ErrorDetail(
            field=field,
            message=error["msg"],
            code=error["type"]
        ))

    error_response = ErrorResponse(
        error_id=error_id,
        error_code=ErrorCode.VALIDATION_ERROR,
        message="خطأ في التحقق من صحة البيانات المدخلة",
        message_en="Validation error",
        details=details,
        severity=ErrorSeverity.LOW,
        path=str(request.url.path)
    )

    error_logger.log_error(exc, error_id, request)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.dict(exclude_none=True)
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors"""

    error_id = str(uuid.uuid4())

    error_logger.log_error(exc, error_id, request)

    error_response = ErrorResponse(
        error_id=error_id,
        error_code=ErrorCode.INTERNAL_ERROR,
        message="حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى أو الاتصال بالدعم الفني.",
        message_en="An unexpected error occurred. Please try again or contact support.",
        severity=ErrorSeverity.CRITICAL,
        path=str(request.url.path)
    )

    # Add details in development
    import os
    if os.getenv("ENVIRONMENT") == "development":
        error_response.stack_trace = traceback.format_exc()
        error_response.context = {"exception_type": type(exc).__name__, "message": str(exc)}

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.dict(exclude_none=True)
    )


# ===================================================================
# DECORATORS FOR ERROR HANDLING
# ===================================================================

def handle_errors(operation_name: str):
    """Decorator to handle errors in service functions"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)

            except SahoolException:
                # Re-raise Sahool exceptions
                raise

            except Exception as e:
                # Wrap unexpected errors
                logger = logging.getLogger(__name__)
                logger.error(f"Error in {operation_name}: {e}", exc_info=True)

                raise SahoolException(
                    error_code=ErrorCode.INTERNAL_ERROR,
                    message_ar=f"خطأ أثناء {operation_name}",
                    message_en=f"Error during {operation_name}",
                    severity=ErrorSeverity.HIGH,
                    context={"operation": operation_name, "original_error": str(e)}
                )

        return wrapper
    return decorator


def handle_database_errors(operation: str):
    """Decorator specifically for database operations"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)

            except Exception as e:
                raise DatabaseException(operation, e)

        return wrapper
    return decorator


# ===================================================================
# USAGE EXAMPLE
# ===================================================================

"""
# In FastAPI app:

from app.core.error_handling import (
    sahool_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
    SahoolException
)

app.add_exception_handler(SahoolException, sahool_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# In service functions:

@handle_errors("create_field")
async def create_field(db: Session, field_data: FieldCreate):
    # Validate geometry
    if not is_valid_geometry(field_data.geometry):
        raise SpatialDataException(
            message_ar="الشكل الهندسي غير صحيح",
            message_en="Invalid geometry",
            details=[ErrorDetail(
                field="geometry",
                message="Geometry is not valid",
                code="INVALID_GEOMETRY"
            )]
        )

    # Create field
    field = Field(**field_data.dict())
    db.add(field)

    try:
        db.commit()
    except IntegrityError as e:
        raise DatabaseException("create_field", e)

    return field


# In API routes:

@router.get("/fields/{field_id}")
async def get_field(field_id: str, current_user: TokenData = Depends(get_current_user)):
    field = await get_field_by_id(field_id)

    if not field:
        raise NotFoundException("Field", field_id)

    if field.tenant_id != current_user.tenant_id:
        raise TenantAccessException(current_user.tenant_id, field_id)

    return field
"""
