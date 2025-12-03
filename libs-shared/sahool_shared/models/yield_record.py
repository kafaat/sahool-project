"""
Yield Record Model - نموذج سجل الإنتاج
"""

from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sahool_shared.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from sahool_shared.models.field import Field


class YieldRecord(Base, TimestampMixin, TenantMixin):
    """
    Crop yield record model.
    نموذج سجل إنتاج المحاصيل
    """

    __tablename__ = "yield_records"

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

    # Crop info
    crop_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="نوع المحصول"
    )
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="سنة الإنتاج"
    )

    # Yield data
    yield_ton_per_hectare: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="الإنتاج (طن/هكتار)"
    )

    # Financial data (in Yemeni Rial)
    revenue_yer: Mapped[Optional[float]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="الإيرادات (ريال يمني)"
    )
    expenses_yer: Mapped[Optional[float]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="المصروفات (ريال يمني)"
    )
    profit_yer: Mapped[Optional[float]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="الربح (ريال يمني)"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="ملاحظات"
    )

    # Relationship
    field: Mapped["Field"] = relationship(
        "Field",
        back_populates="yield_records"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("year >= 2000 AND year <= 2100", name="check_year_range"),
        CheckConstraint("yield_ton_per_hectare >= 0", name="check_yield_positive"),
    )

    def __repr__(self) -> str:
        return f"<YieldRecord(id={self.id}, crop_type='{self.crop_type}', year={self.year})>"

    @property
    def profit_margin(self) -> Optional[float]:
        """Calculate profit margin percentage."""
        if self.revenue_yer and self.profit_yer and float(self.revenue_yer) > 0:
            return (float(self.profit_yer) / float(self.revenue_yer)) * 100
        return None
