"""
Weather Data Model - نموذج بيانات الطقس
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
    from sahool_shared.models.region import Region


class WeatherData(Base, TimestampMixin, TenantMixin):
    """
    Weather data for fields and regions.
    بيانات الطقس للحقول والمناطق
    """

    __tablename__ = "weather_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Temperature
    temperature: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        comment="درجة الحرارة (سيليزية)"
    )
    temperature_min: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        comment="أدنى درجة حرارة"
    )
    temperature_max: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        comment="أعلى درجة حرارة"
    )

    # Humidity & Precipitation
    humidity: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="الرطوبة النسبية %"
    )
    rainfall: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="هطول الأمطار (مم)"
    )

    # Wind
    wind_speed: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        comment="سرعة الرياح (م/ث)"
    )
    wind_direction: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="اتجاه الرياح"
    )

    # Pressure & Solar
    pressure: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 2),
        nullable=True,
        comment="الضغط الجوي (hPa)"
    )
    solar_radiation: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="الإشعاع الشمسي (W/m²)"
    )

    # Forecast info
    forecast_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
        comment="تاريخ التوقع"
    )
    forecast_accuracy: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="دقة التوقع %"
    )

    # Source
    source: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="OpenWeather",
        comment="مصدر البيانات"
    )
    station_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="معرف محطة الرصد"
    )

    # Foreign keys
    region_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("regions.id"),
        nullable=True,
        index=True
    )
    field_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id"),
        nullable=True,
        index=True
    )

    # Relationships
    field: Mapped[Optional["Field"]] = relationship(
        "Field",
        back_populates="weather_data"
    )

    def __repr__(self) -> str:
        return f"<WeatherData(id={self.id}, temp={self.temperature}, date={self.forecast_date})>"

    @property
    def is_favorable_for_agriculture(self) -> bool:
        """Check if weather conditions are favorable."""
        if self.temperature is None:
            return True
        temp = float(self.temperature)
        # Favorable: 15-35°C, humidity 40-80%, wind < 10 m/s
        temp_ok = 15 <= temp <= 35
        humidity_ok = self.humidity is None or 40 <= float(self.humidity) <= 80
        wind_ok = self.wind_speed is None or float(self.wind_speed) < 10
        return temp_ok and humidity_ok and wind_ok

    @property
    def alert_conditions(self) -> list[str]:
        """Return list of weather alert conditions."""
        alerts = []
        if self.temperature:
            if float(self.temperature) > 40:
                alerts.append("حرارة شديدة")
            elif float(self.temperature) < 5:
                alerts.append("برودة شديدة")
        if self.wind_speed and float(self.wind_speed) > 15:
            alerts.append("رياح قوية")
        if self.rainfall and float(self.rainfall) > 50:
            alerts.append("أمطار غزيرة")
        return alerts
