"""
Field Model - نموذج الحقل
"""

from datetime import date
from typing import TYPE_CHECKING, Any, Optional
import uuid

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sahool_shared.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from sahool_shared.models.farmer import Farmer
    from sahool_shared.models.region import Region
    from sahool_shared.models.ndvi import NDVIResult
    from sahool_shared.models.weather import WeatherData


class Field(Base, TimestampMixin, TenantMixin):
    """
    Agricultural field model with geospatial data.
    نموذج الحقل الزراعي مع البيانات الجغرافية
    """

    __tablename__ = "fields"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Basic info
    name_ar: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="اسم الحقل بالعربية"
    )
    name_en: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Field name in English"
    )

    # Area
    area_hectares: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="المساحة بالهكتار"
    )

    # Crop information
    crop_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="نوع المحصول"
    )
    crop_variety: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="صنف المحصول"
    )
    planting_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="تاريخ الزراعة"
    )
    expected_harvest_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="تاريخ الحصاد المتوقع"
    )

    # Geographic data
    coordinates = Column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
        comment="Field center point"
    )
    field_geometry = Column(
        Geography(geometry_type="POLYGON", srid=4326),
        nullable=True,
        comment="Field boundary polygon"
    )
    elevation_meters: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="الارتفاع بالمتر"
    )

    # Soil data
    soil_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="نوع التربة"
    )
    soil_ph: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        comment="حموضة التربة"
    )

    # Irrigation
    irrigation_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="نوع الري"
    )
    irrigation_system: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="تفاصيل نظام الري"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        comment="حالة الحقل"
    )

    # Foreign keys
    farmer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farmers.id"),
        nullable=True
    )
    region_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("regions.id"),
        nullable=True
    )

    # Relationships
    farmer: Mapped[Optional["Farmer"]] = relationship(
        "Farmer",
        back_populates="fields"
    )
    region: Mapped[Optional["Region"]] = relationship(
        "Region",
        back_populates="fields"
    )
    ndvi_results: Mapped[list["NDVIResult"]] = relationship(
        "NDVIResult",
        back_populates="field",
        lazy="selectin",
        order_by="desc(NDVIResult.acquisition_date)"
    )
    weather_data: Mapped[list["WeatherData"]] = relationship(
        "WeatherData",
        back_populates="field",
        lazy="selectin"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("area_hectares > 0", name="check_area_positive"),
        CheckConstraint("soil_ph BETWEEN 0 AND 14", name="check_soil_ph_range"),
    )

    def __repr__(self) -> str:
        return f"<Field(id={self.id}, name_ar='{self.name_ar}')>"

    @property
    def latest_ndvi(self) -> Optional[float]:
        """Return the latest NDVI value."""
        if self.ndvi_results:
            return float(self.ndvi_results[0].ndvi_value)
        return None

    @property
    def health_status(self) -> str:
        """Determine field health based on NDVI."""
        ndvi = self.latest_ndvi
        if ndvi is None:
            return "unknown"
        if ndvi >= 0.6:
            return "excellent"
        if ndvi >= 0.4:
            return "good"
        if ndvi >= 0.2:
            return "moderate"
        return "poor"
