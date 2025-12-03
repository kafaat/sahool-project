"""
Farmer Model - نموذج المزارع
"""

from datetime import date
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import Date, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sahool_shared.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from sahool_shared.models.region import Region
    from sahool_shared.models.field import Field


class Farmer(Base, TimestampMixin, TenantMixin):
    """
    Farmer model for agricultural platform users.
    نموذج المزارع لمستخدمي المنصة الزراعية
    """

    __tablename__ = "farmers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="اسم المزارع"
    )

    # Contact info (can be encrypted)
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        comment="رقم الهاتف"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="البريد الإلكتروني"
    )

    # Encrypted versions
    phone_encrypted: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary,
        nullable=True,
        comment="رقم الهاتف المشفر"
    )
    email_encrypted: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary,
        nullable=True,
        comment="البريد المشفر"
    )

    # Region relationship
    region_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("regions.id"),
        nullable=True
    )

    # Registration
    registration_date: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        comment="تاريخ التسجيل"
    )

    # Relationships
    region: Mapped[Optional["Region"]] = relationship(
        "Region",
        back_populates="farmers"
    )
    fields: Mapped[list["Field"]] = relationship(
        "Field",
        back_populates="farmer",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Farmer(id={self.id}, name='{self.name}')>"

    @property
    def total_fields(self) -> int:
        """Return total number of fields."""
        return len(self.fields) if self.fields else 0

    @property
    def total_area_hectares(self) -> float:
        """Return total area of all fields."""
        if not self.fields:
            return 0.0
        return sum(f.area_hectares for f in self.fields if f.area_hectares)
