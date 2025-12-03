"""
Weather Schemas
مخططات الطقس
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import Field

from sahool_shared.schemas.common import BaseSchema


class WeatherData(BaseSchema):
    """Single weather data point."""

    date: date
    temperature: float = Field(..., description="درجة الحرارة (سيليزية)")
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None
    humidity: float = Field(..., ge=0, le=100, description="الرطوبة النسبية %")
    rainfall: float = Field(default=0, ge=0, description="هطول الأمطار (مم)")
    wind_speed: float = Field(default=0, ge=0, description="سرعة الرياح (م/ث)")
    wind_direction: Optional[str] = None
    pressure: Optional[float] = Field(None, description="الضغط الجوي (hPa)")
    solar_radiation: Optional[float] = Field(None, description="الإشعاع الشمسي (W/m²)")


class WeatherResponse(BaseSchema):
    """Weather response for a location."""

    location_id: Optional[str] = None  # field_id or region_id
    location_type: str = "field"  # field or region
    current: WeatherData
    source: str = "OpenWeather"
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)


class WeatherForecast(BaseSchema):
    """Weather forecast response."""

    location_id: Optional[str] = None
    location_type: str = "field"
    current: WeatherData
    forecast: List[WeatherData] = []
    forecast_days: int = 5
    source: str = "OpenWeather"
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_favorable(self) -> bool:
        """Check if current weather is favorable for agriculture."""
        temp = self.current.temperature
        humidity = self.current.humidity
        wind = self.current.wind_speed
        return 15 <= temp <= 35 and 40 <= humidity <= 80 and wind < 10


class WeatherAlert(BaseSchema):
    """Weather alert."""

    alert_type: str  # heat, cold, wind, rain, frost
    severity: str = "medium"  # low, medium, high, critical
    title_ar: str
    title_en: Optional[str] = None
    message_ar: str
    message_en: Optional[str] = None
    valid_from: datetime
    valid_until: datetime
    affected_regions: List[int] = []


class WeatherSummary(BaseSchema):
    """Weather summary for a period."""

    period_start: date
    period_end: date
    avg_temperature: float
    max_temperature: float
    min_temperature: float
    total_rainfall: float
    avg_humidity: float
    favorable_days: int
    total_days: int
