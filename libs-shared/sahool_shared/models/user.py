"""
User and Tenant Models - نماذج المستخدم والمستأجر
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sahool_shared.models.base import Base, TimestampMixin


class UserRole(str, Enum):
    """User roles."""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    FARMER = "farmer"
    VIEWER = "viewer"


class TenantPlan(str, Enum):
    """Tenant subscription plans."""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Tenant(Base, TimestampMixin):
    """
    Tenant/Organization model for multi-tenancy.
    نموذج المستأجر/المنظمة للتعدد
    """

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Basic info
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        comment="اسم المنظمة"
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="المعرف المختصر"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="وصف المنظمة"
    )

    # Contact
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="البريد الإلكتروني"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="رقم الهاتف"
    )

    # Subscription
    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=TenantPlan.FREE.value,
        comment="خطة الاشتراك"
    )
    plan_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="تاريخ انتهاء الاشتراك"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="نشط"
    )

    # Settings
    settings: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="إعدادات المنظمة"
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}')>"

    @property
    def is_plan_active(self) -> bool:
        """Check if subscription plan is active."""
        if not self.is_active:
            return False
        if self.plan_expires_at and self.plan_expires_at < datetime.utcnow():
            return False
        return True


class User(Base, TimestampMixin):
    """
    User model for authentication and authorization.
    نموذج المستخدم للمصادقة والتفويض
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="البريد الإلكتروني"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="كلمة المرور المشفرة"
    )

    # Profile
    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="الاسم الكامل"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="رقم الهاتف"
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="رابط الصورة الشخصية"
    )

    # Role and permissions
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=UserRole.VIEWER.value,
        comment="الدور"
    )
    permissions: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="الصلاحيات"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="نشط"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="تم التحقق"
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="آخر تسجيل دخول"
    )

    # Tenant relationship
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True
    )
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="users"
    )

    # Settings
    settings: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="إعدادات المستخدم"
    )
    language: Mapped[str] = mapped_column(
        String(10),
        default="ar",
        comment="اللغة المفضلة"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.role == UserRole.ADMIN.value:
            return True
        if self.permissions and permission in self.permissions:
            return self.permissions[permission]
        return False

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
