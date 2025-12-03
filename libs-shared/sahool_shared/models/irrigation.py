"""
Irrigation Schedule Model - نموذج جدول الري
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sahool_shared.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from sahool_shared.models.field import Field


class IrrigationSchedule(Base, TimestampMixin, TenantMixin):
    """
    Irrigation schedule model.
    نموذج جدول الري
    """

    __tablename__ = "irrigation_schedules"

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

    # Schedule info
    schedule_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="تاريخ الري المجدول"
    )
    water_amount_mm: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="كمية الماء (ملم)"
    )
    irrigation_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="نوع الري"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="الحالة: pending, completed, cancelled, skipped"
    )
    executed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="وقت التنفيذ الفعلي"
    )

    # Duration
    duration_minutes: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="مدة الري بالدقائق"
    )

    # Relationship
    field: Mapped["Field"] = relationship(
        "Field",
        back_populates="irrigation_schedules"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'cancelled', 'skipped')",
            name="check_status_valid"
        ),
        CheckConstraint("water_amount_mm >= 0", name="check_water_positive"),
    )

    def __repr__(self) -> str:
        return f"<IrrigationSchedule(id={self.id}, date={self.schedule_date}, status='{self.status}')>"

    def mark_completed(self) -> None:
        """Mark irrigation as completed."""
        self.status = "completed"
        self.executed_at = datetime.utcnow()

    def mark_cancelled(self) -> None:
        """Mark irrigation as cancelled."""
        self.status = "cancelled"

    @property
    def is_overdue(self) -> bool:
        """Check if irrigation is overdue."""
        return (
            self.status == "pending" and
            self.schedule_date < date.today()
        )
