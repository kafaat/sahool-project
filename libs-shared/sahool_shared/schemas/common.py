"""
Common Pydantic Schemas
مخططات Pydantic العامة
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


DataT = TypeVar("DataT")


class PaginatedResponse(BaseSchema, Generic[DataT]):
    """Paginated response schema."""

    items: List[DataT]
    total: int
    page: int = 1
    page_size: int = 20
    pages: int = 1

    @classmethod
    def create(
        cls,
        items: List[DataT],
        total: int,
        page: int = 1,
        page_size: int = 20,
    ) -> "PaginatedResponse[DataT]":
        pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )


class ErrorResponse(BaseSchema):
    """
    Standardized error response schema.
    نموذج استجابة الخطأ الموحد
    """

    error: str = Field(..., description="Error code (e.g., 'validation_error', 'not_found')")
    message: str = Field(..., description="Error message in English")
    message_ar: Optional[str] = Field(None, description="Error message in Arabic / رسالة الخطأ بالعربية")
    status_code: int = Field(500, description="HTTP status code")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    path: Optional[str] = Field(None, description="API endpoint path")

    @classmethod
    def validation_error(cls, message: str, message_ar: str = None, details: dict = None, request_id: str = None):
        """Create a validation error response."""
        return cls(
            error="validation_error",
            message=message,
            message_ar=message_ar or "خطأ في التحقق من البيانات",
            status_code=400,
            details=details,
            request_id=request_id
        )

    @classmethod
    def not_found(cls, resource: str, message_ar: str = None, request_id: str = None):
        """Create a not found error response."""
        return cls(
            error="not_found",
            message=f"{resource} not found",
            message_ar=message_ar or f"لم يتم العثور على {resource}",
            status_code=404,
            request_id=request_id
        )

    @classmethod
    def unauthorized(cls, message: str = "Unauthorized", message_ar: str = None, request_id: str = None):
        """Create an unauthorized error response."""
        return cls(
            error="unauthorized",
            message=message,
            message_ar=message_ar or "غير مصرح",
            status_code=401,
            request_id=request_id
        )

    @classmethod
    def forbidden(cls, message: str = "Forbidden", message_ar: str = None, request_id: str = None):
        """Create a forbidden error response."""
        return cls(
            error="forbidden",
            message=message,
            message_ar=message_ar or "ممنوع الوصول",
            status_code=403,
            request_id=request_id
        )

    @classmethod
    def internal_error(cls, message: str = "Internal server error", message_ar: str = None, request_id: str = None):
        """Create an internal server error response."""
        return cls(
            error="internal_error",
            message=message,
            message_ar=message_ar or "خطأ داخلي في الخادم",
            status_code=500,
            request_id=request_id
        )

    @classmethod
    def rate_limited(cls, retry_after: int = 60, request_id: str = None):
        """Create a rate limit error response."""
        return cls(
            error="rate_limit_exceeded",
            message=f"Too many requests. Retry after {retry_after} seconds",
            message_ar=f"طلبات كثيرة جداً. أعد المحاولة بعد {retry_after} ثانية",
            status_code=429,
            details={"retry_after": retry_after},
            request_id=request_id
        )


class SuccessResponse(BaseSchema):
    """Success response schema."""

    success: bool = True
    message: str
    data: Optional[dict[str, Any]] = None


class HealthResponse(BaseSchema):
    """Health check response."""

    status: str = "healthy"
    version: str
    service: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Optional[dict[str, Any]] = None


class GeoPoint(BaseSchema):
    """Geographic point."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    def to_wkt(self) -> str:
        """Convert to WKT format."""
        return f"POINT({self.longitude} {self.latitude})"


class GeoPolygon(BaseSchema):
    """Geographic polygon."""

    coordinates: List[List[float]]  # [[lon, lat], [lon, lat], ...]

    def to_wkt(self) -> str:
        """Convert to WKT format."""
        coords = ", ".join(f"{lon} {lat}" for lon, lat in self.coordinates)
        return f"POLYGON(({coords}))"


class DateRange(BaseSchema):
    """Date range for filtering."""

    start_date: datetime
    end_date: datetime

    def validate_range(self) -> bool:
        return self.start_date <= self.end_date


class PaginationParams(BaseSchema):
    """
    Standardized pagination parameters.
    معاملات التصفح الموحدة
    """

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page (max 100)")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order: 'asc' or 'desc'")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class HealthCheckResult(BaseSchema):
    """Individual health check result."""

    name: str
    status: str = Field(..., pattern="^(healthy|unhealthy|degraded)$")
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class DetailedHealthResponse(BaseSchema):
    """
    Detailed health check response with component status.
    استجابة فحص الصحة التفصيلية مع حالة المكونات
    """

    status: str = Field("healthy", pattern="^(healthy|unhealthy|degraded)$")
    version: str
    service: str
    environment: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: Optional[float] = None
    checks: List[HealthCheckResult] = Field(default_factory=list)

    @classmethod
    def from_checks(cls, service: str, version: str, checks: List[HealthCheckResult], environment: str = None, uptime: float = None):
        """Create health response from check results."""
        # Determine overall status
        statuses = [c.status for c in checks]
        if "unhealthy" in statuses:
            overall = "unhealthy"
        elif "degraded" in statuses:
            overall = "degraded"
        else:
            overall = "healthy"

        return cls(
            status=overall,
            version=version,
            service=service,
            environment=environment,
            uptime_seconds=uptime,
            checks=checks
        )
