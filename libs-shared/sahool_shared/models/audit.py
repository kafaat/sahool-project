"""
Audit Log Model - نموذج سجل التدقيق
"""

from datetime import datetime
from typing import Any, Optional
import uuid

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import INET, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from sahool_shared.models.base import Base, TenantMixin


class AuditLog(Base, TenantMixin):
    """
    Audit log model for tracking all changes.
    نموذج سجل التدقيق لتتبع جميع التغييرات
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # User info
    user_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="معرف المستخدم"
    )
    user_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="بريد المستخدم"
    )

    # Action details
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="نوع العملية: create, update, delete, login, etc."
    )
    table_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="اسم الجدول"
    )
    record_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="معرف السجل المتأثر"
    )

    # Change data
    old_values: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="القيم القديمة"
    )
    new_values: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="القيم الجديدة"
    )

    # Request info
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="عنوان IP"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="معلومات المتصفح"
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="معرف الطلب"
    )

    # Additional context
    context: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="سياق إضافي"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        index=True,
        comment="وقت الحدث"
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', table='{self.table_name}')>"

    @classmethod
    def create_log(
        cls,
        tenant_id: uuid.UUID,
        action: str,
        user_id: Optional[str] = None,
        table_name: Optional[str] = None,
        record_id: Optional[uuid.UUID] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        context: Optional[dict] = None
    ) -> "AuditLog":
        """Create a new audit log entry."""
        return cls(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            context=context
        )
