from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class WeatherForecastPoint(BaseModel):
    timestamp: datetime
    temp_c: Optional[float] = None
    eto_mm: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    rel_humidity_pct: Optional[float] = None
    rain_mm: Optional[float] = None

class WeatherForecastResponse(BaseModel):
    tenant_id: int
    field_id: int
    points: List[WeatherForecastPoint]

class WeatherIngestPoint(BaseModel):
    timestamp: datetime
    temp_c: Optional[float] = None
    eto_mm: Optional[float] = None
    rain_mm: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    rel_humidity_pct: Optional[float] = None


class WeatherIngestRequest(BaseModel):
    tenant_id: int
    field_id: int
    points: List[WeatherIngestPoint]
