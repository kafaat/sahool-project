"""
NDVI Schemas
مخططات NDVI
"""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from sahool_shared.schemas.common import BaseSchema


class NDVIResponse(BaseSchema):
    """Single NDVI result response."""

    id: UUID
    field_id: UUID
    tenant_id: UUID
    ndvi_value: float = Field(..., ge=-1, le=1)
    acquisition_date: date
    satellite_name: str = "Sentinel-2"
    cloud_coverage: Optional[float] = Field(None, ge=0, le=100)
    tile_url: Optional[str] = None
    processing_version: Optional[str] = None
    created_at: datetime

    # Computed fields
    health_category: str = "unknown"
    health_category_ar: str = "غير معروف"

    @field_validator("health_category", mode="before")
    @classmethod
    def compute_health_category(cls, v, info):
        if v and v != "unknown":
            return v
        ndvi = info.data.get("ndvi_value")
        if ndvi is None:
            return "unknown"
        if ndvi >= 0.6:
            return "excellent"
        if ndvi >= 0.4:
            return "good"
        if ndvi >= 0.2:
            return "moderate"
        if ndvi >= 0:
            return "poor"
        return "bare"

    @field_validator("health_category_ar", mode="before")
    @classmethod
    def compute_health_category_ar(cls, v, info):
        if v and v != "غير معروف":
            return v
        ndvi = info.data.get("ndvi_value")
        if ndvi is None:
            return "غير معروف"
        if ndvi >= 0.6:
            return "ممتاز"
        if ndvi >= 0.4:
            return "جيد"
        if ndvi >= 0.2:
            return "متوسط"
        if ndvi >= 0:
            return "ضعيف"
        return "أرض جرداء"


class NDVITimelinePoint(BaseSchema):
    """Single point in NDVI timeline."""

    date: date
    ndvi_value: float
    health_category: str
    cloud_coverage: Optional[float] = None


class NDVITimeline(BaseSchema):
    """NDVI timeline for a field."""

    field_id: UUID
    field_name: str
    tenant_id: UUID
    timeline: List[NDVITimelinePoint] = []
    start_date: date
    end_date: date
    average_ndvi: Optional[float] = None
    trend: str = "stable"  # improving, declining, stable

    @classmethod
    def calculate_trend(cls, values: List[float]) -> str:
        """Calculate trend from NDVI values."""
        if len(values) < 3:
            return "stable"

        # Simple linear regression
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n

        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        if slope > 0.01:
            return "improving"
        if slope < -0.01:
            return "declining"
        return "stable"


class NDVIAnalysis(BaseSchema):
    """NDVI analysis results."""

    field_id: UUID
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    current_ndvi: float
    previous_ndvi: Optional[float] = None
    change_percent: Optional[float] = None
    health_category: str
    health_category_ar: str
    recommendations: List[str] = []
    recommendations_ar: List[str] = []


class YieldPrediction(BaseSchema):
    """Yield prediction based on NDVI."""

    field_id: UUID
    crop_type: str
    predicted_yield_kg_per_hectare: float
    confidence_percent: float = Field(..., ge=0, le=100)
    prediction_date: date
    factors: dict = {}
    recommendations: List[str] = []
