from sqlalchemy import Column, Integer, Float, DateTime
from app.db.base import Base

class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    field_id = Column(Integer, index=True, nullable=False)

    timestamp = Column(DateTime, index=True, nullable=False)
    temp_c = Column(Float, nullable=True)
    eto_mm = Column(Float, nullable=True)
    wind_speed_ms = Column(Float, nullable=True)
    rel_humidity_pct = Column(Float, nullable=True)
    rain_mm = Column(Float, nullable=True)