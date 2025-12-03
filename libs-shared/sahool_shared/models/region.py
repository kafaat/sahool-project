"""
Region Model - نموذج المنطقة/المحافظة
"""

from typing import TYPE_CHECKING, Optional
import uuid

from geoalchemy2 import Geography
from sqlalchemy import Column, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sahool_shared.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from sahool_shared.models.farmer import Farmer
    from sahool_shared.models.field import Field


class Region(Base, TimestampMixin):
    """
    Region/Governorate model for Yemen agricultural regions.
    نموذج المنطقة/المحافظة للمناطق الزراعية اليمنية
    """

    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_ar: Mapped[str] = mapped_column(String(100), nullable=False, comment="اسم المنطقة بالعربية")
    name_en: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="Region name in English")

    # Geographic data
    coordinates = Column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
        comment="Region center point coordinates"
    )
    area_km2: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Area in square kilometers"
    )

    # Agricultural data
    agricultural_potential: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Agricultural potential description"
    )
    climate_zone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Climate zone classification"
    )

    # Relationships
    farmers: Mapped[list["Farmer"]] = relationship(
        "Farmer",
        back_populates="region",
        lazy="selectin"
    )
    fields: Mapped[list["Field"]] = relationship(
        "Field",
        back_populates="region",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Region(id={self.id}, name_ar='{self.name_ar}')>"

    @property
    def display_name(self) -> str:
        """Return bilingual display name."""
        if self.name_en:
            return f"{self.name_ar} ({self.name_en})"
        return self.name_ar
