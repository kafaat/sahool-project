"""
Soil Analysis Model - نموذج تحليل التربة
"""

from datetime import date
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sahool_shared.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from sahool_shared.models.field import Field


class SoilAnalysis(Base, TimestampMixin, TenantMixin):
    """
    Soil analysis results model.
    نموذج نتائج تحليل التربة
    """

    __tablename__ = "soil_analysis"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign key
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id"),
        nullable=False,
        index=True
    )

    # pH and nutrients
    ph_value: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        comment="قيمة الحموضة"
    )
    nitrogen_ppm: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="النيتروجين (جزء في المليون)"
    )
    phosphorus_ppm: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="الفوسفور (جزء في المليون)"
    )
    potassium_ppm: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="البوتاسيوم (جزء في المليون)"
    )
    organic_matter_percent: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="نسبة المادة العضوية"
    )
    salinity_ms_cm: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        comment="الملوحة (ملي سيمنز/سم)"
    )

    # Analysis info
    analysis_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="تاريخ التحليل"
    )
    lab_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="اسم المختبر"
    )

    # Relationship
    field: Mapped["Field"] = relationship(
        "Field",
        back_populates="soil_analyses"
    )

    def __repr__(self) -> str:
        return f"<SoilAnalysis(id={self.id}, field_id={self.field_id})>"

    @property
    def fertility_status(self) -> str:
        """Determine soil fertility status."""
        if self.nitrogen_ppm and self.phosphorus_ppm and self.potassium_ppm:
            avg = (float(self.nitrogen_ppm) + float(self.phosphorus_ppm) + float(self.potassium_ppm)) / 3
            if avg >= 100:
                return "excellent"
            if avg >= 50:
                return "good"
            if avg >= 25:
                return "moderate"
            return "poor"
        return "unknown"
