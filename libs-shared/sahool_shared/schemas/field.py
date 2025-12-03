"""
Field Schemas
مخططات الحقل
"""

from datetime import date, datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from sahool_shared.schemas.common import BaseSchema, GeoPoint, PaginatedResponse


class FieldCreate(BaseSchema):
    """Schema for creating a field."""

    name_ar: str = Field(..., min_length=1, max_length=200, description="اسم الحقل بالعربية")
    name_en: Optional[str] = Field(None, max_length=200, description="Field name in English")
    area_hectares: float = Field(..., gt=0, description="المساحة بالهكتار")
    crop_type: Optional[str] = Field(None, max_length=100, description="نوع المحصول")
    crop_variety: Optional[str] = Field(None, max_length=100, description="صنف المحصول")
    planting_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    coordinates: GeoPoint
    elevation_meters: Optional[int] = Field(None, ge=0, le=5000)
    soil_type: Optional[str] = Field(None, max_length=50)
    soil_ph: Optional[float] = Field(None, ge=0, le=14)
    irrigation_type: Optional[str] = Field(None, max_length=50)
    farmer_id: Optional[UUID] = None
    region_id: Optional[int] = None


class FieldUpdate(BaseSchema):
    """Schema for updating a field."""

    name_ar: Optional[str] = Field(None, min_length=1, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    area_hectares: Optional[float] = Field(None, gt=0)
    crop_type: Optional[str] = Field(None, max_length=100)
    crop_variety: Optional[str] = Field(None, max_length=100)
    planting_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    elevation_meters: Optional[int] = Field(None, ge=0, le=5000)
    soil_type: Optional[str] = Field(None, max_length=50)
    soil_ph: Optional[float] = Field(None, ge=0, le=14)
    irrigation_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, pattern="^(active|inactive|harvested)$")


class FieldResponse(BaseSchema):
    """Schema for field response."""

    id: UUID
    tenant_id: UUID
    name_ar: str
    name_en: Optional[str] = None
    area_hectares: float
    crop_type: Optional[str] = None
    crop_variety: Optional[str] = None
    planting_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    elevation_meters: Optional[int] = None
    soil_type: Optional[str] = None
    soil_ph: Optional[float] = None
    irrigation_type: Optional[str] = None
    irrigation_system: Optional[dict[str, Any]] = None
    status: str = "active"
    farmer_id: Optional[UUID] = None
    region_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Computed fields
    latest_ndvi: Optional[float] = None
    health_status: Optional[str] = None

    @field_validator("health_status", mode="before")
    @classmethod
    def compute_health_status(cls, v, info):
        if v is not None:
            return v
        ndvi = info.data.get("latest_ndvi")
        if ndvi is None:
            return "unknown"
        if ndvi >= 0.6:
            return "excellent"
        if ndvi >= 0.4:
            return "good"
        if ndvi >= 0.2:
            return "moderate"
        return "poor"


class FieldListResponse(PaginatedResponse[FieldResponse]):
    """Paginated list of fields."""
    pass


class FieldSummary(BaseSchema):
    """Summary statistics for fields."""

    total_fields: int
    total_area_hectares: float
    average_ndvi: Optional[float] = None
    fields_by_status: dict[str, int] = {}
    fields_by_crop: dict[str, int] = {}
