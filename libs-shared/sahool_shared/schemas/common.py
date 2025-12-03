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
    """Error response schema."""

    error: str
    message: str
    details: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


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
