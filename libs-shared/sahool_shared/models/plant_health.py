"""
Plant Health Model - نموذج صحة النبات
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sahool_shared.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from sahool_shared.models.field import Field


class PlantHealth(Base, TimestampMixin, TenantMixin):
    """
    Plant health detection model.
    نموذج كشف صحة النبات
    """

    __tablename__ = "plant_health"

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

    # Disease detection
    disease_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="اسم المرض"
    )
    disease_name_ar: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="اسم المرض بالعربية"
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="نسبة الثقة في التشخيص"
    )
    severity_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="مستوى الخطورة: low, medium, high, critical"
    )

    # Recommendation
    recommendation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="التوصية العلاجية"
    )
    recommendation_ar: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="التوصية بالعربية"
    )

    # Image data
    image_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="رابط الصورة"
    )
    metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        default={},
        comment="بيانات إضافية"
    )

    # Detection info
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        comment="وقت الاكتشاف"
    )
    detection_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="طريقة الكشف: ai, manual, sensor"
    )

    # Status
    is_resolved: Mapped[bool] = mapped_column(
        default=False,
        comment="هل تم حل المشكلة"
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="وقت حل المشكلة"
    )

    # Relationship
    field: Mapped["Field"] = relationship(
        "Field",
        back_populates="plant_health_records"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "confidence_score BETWEEN 0 AND 100",
            name="check_confidence_range"
        ),
        CheckConstraint(
            "severity_level IN ('low', 'medium', 'high', 'critical')",
            name="check_severity_valid"
        ),
    )

    def __repr__(self) -> str:
        return f"<PlantHealth(id={self.id}, disease='{self.disease_name}', severity='{self.severity_level}')>"

    def mark_resolved(self) -> None:
        """Mark health issue as resolved."""
        self.is_resolved = True
        self.resolved_at = datetime.utcnow()

    @property
    def is_critical(self) -> bool:
        """Check if this is a critical health issue."""
        return self.severity_level in ("high", "critical")
