"""
NDVI Result Model - نموذج نتائج NDVI
"""

from datetime import date
from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sahool_shared.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from sahool_shared.models.field import Field


class NDVIResult(Base, TimestampMixin, TenantMixin):
    """
    NDVI (Normalized Difference Vegetation Index) results.
    نتائج مؤشر الغطاء النباتي الطبيعي
    """

    __tablename__ = "ndvi_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # NDVI value (-1 to 1)
    ndvi_value: Mapped[float] = mapped_column(
        Numeric(5, 3),
        nullable=False,
        comment="قيمة NDVI"
    )

    # Acquisition info
    acquisition_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="تاريخ الاستحواذ"
    )

    # Satellite data
    satellite_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="Sentinel-2",
        comment="اسم القمر الصناعي"
    )
    tile_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="رابط الصورة"
    )
    tile_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="بيانات الصورة الوصفية"
    )

    # Quality
    cloud_coverage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="نسبة الغطاء السحابي"
    )
    processing_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="إصدار المعالجة"
    )

    # Foreign key
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationship
    field: Mapped["Field"] = relationship(
        "Field",
        back_populates="ndvi_results"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("ndvi_value BETWEEN -1 AND 1", name="check_ndvi_range"),
        CheckConstraint("cloud_coverage BETWEEN 0 AND 100", name="check_cloud_range"),
    )

    def __repr__(self) -> str:
        return f"<NDVIResult(id={self.id}, ndvi={self.ndvi_value}, date={self.acquisition_date})>"

    @property
    def health_category(self) -> str:
        """Categorize NDVI value into health status."""
        v = float(self.ndvi_value)
        if v >= 0.6:
            return "ممتاز"  # Excellent
        if v >= 0.4:
            return "جيد"  # Good
        if v >= 0.2:
            return "متوسط"  # Moderate
        if v >= 0:
            return "ضعيف"  # Poor
        return "غير مزروع"  # Bare/Water

    @property
    def is_high_quality(self) -> bool:
        """Check if result has acceptable cloud coverage."""
        if self.cloud_coverage is None:
            return True
        return float(self.cloud_coverage) < 20.0
