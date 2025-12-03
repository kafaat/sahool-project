"""
Alert Model - نموذج التنبيهات
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from sahool_shared.models.base import Base, TimestampMixin, TenantMixin


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Alert types."""
    WEATHER = "weather"
    NDVI = "ndvi"
    IRRIGATION = "irrigation"
    PEST = "pest"
    DISEASE = "disease"
    HARVEST = "harvest"
    SYSTEM = "system"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class Alert(Base, TimestampMixin, TenantMixin):
    """
    Alert/Notification model for the platform.
    نموذج التنبيهات والإشعارات للمنصة
    """

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Alert content
    title_ar: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="عنوان التنبيه بالعربية"
    )
    title_en: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Alert title in English"
    )
    message_ar: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="نص التنبيه بالعربية"
    )
    message_en: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Alert message in English"
    )

    # Classification
    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=AlertType.SYSTEM.value,
        comment="نوع التنبيه"
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AlertSeverity.MEDIUM.value,
        comment="درجة الخطورة"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AlertStatus.ACTIVE.value,
        index=True,
        comment="حالة التنبيه"
    )

    # Timing
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="تاريخ انتهاء الصلاحية"
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="تاريخ الإقرار"
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="تاريخ الحل"
    )

    # Related entities
    field_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id"),
        nullable=True,
        index=True
    )
    region_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("regions.id"),
        nullable=True
    )

    # Metadata
    extra_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="بيانات إضافية"
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="مصدر التنبيه"
    )

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type={self.alert_type}, severity={self.severity})>"

    def acknowledge(self) -> None:
        """Mark alert as acknowledged."""
        self.status = AlertStatus.ACKNOWLEDGED.value
        self.acknowledged_at = datetime.utcnow()

    def resolve(self) -> None:
        """Mark alert as resolved."""
        self.status = AlertStatus.RESOLVED.value
        self.resolved_at = datetime.utcnow()

    @property
    def is_active(self) -> bool:
        """Check if alert is still active."""
        if self.status != AlertStatus.ACTIVE.value:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    @property
    def display_title(self) -> str:
        """Return bilingual title."""
        if self.title_en:
            return f"{self.title_ar} / {self.title_en}"
        return self.title_ar
