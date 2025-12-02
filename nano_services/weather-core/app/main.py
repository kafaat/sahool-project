"""
سهول اليمن - Weather Core Service
خدمة بيانات الطقس الزراعي لليمن
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date
from typing import Optional, List
import random

app = FastAPI(
    title="Weather Core - سهول اليمن",
    description="خدمة بيانات الطقس الزراعي لجميع المحافظات اليمنية",
    version="1.0.0"
)

class WeatherResponse(BaseModel):
    field_id: int
    date: date
    tmax: float
    tmin: float
    tmean: float
    rain_mm: float
    humidity: float
    wind_speed: float
    wind_direction: str
    pressure_hpa: float
    uv_index: float
    visibility_km: float

class WeatherForecast(BaseModel):
    date: date
    tmax: float
    tmin: float
    rain_probability: float
    description_ar: str

class WeatherForecastResponse(BaseModel):
    field_id: int
    forecasts: List[WeatherForecast]

# Yemen-specific weather patterns by region
YEMEN_WEATHER_PROFILES = {
    "coastal": {"temp_range": (28, 38), "humidity": (60, 90), "rain": (0, 5)},
    "highland": {"temp_range": (15, 28), "humidity": (30, 60), "rain": (0, 20)},
    "desert": {"temp_range": (25, 45), "humidity": (10, 30), "rain": (0, 2)},
}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "weather-core", "region": "Yemen"}

@app.get("/api/v1/weather/fields/{field_id}", response_model=WeatherResponse)
async def get_weather(field_id: int, target_date: Optional[date] = None, region_type: str = "highland"):
    """الحصول على بيانات الطقس الحالية للحقل"""
    d = target_date or date.today()
    profile = YEMEN_WEATHER_PROFILES.get(region_type, YEMEN_WEATHER_PROFILES["highland"])

    tmax = round(random.uniform(*profile["temp_range"]), 1)
    tmin = round(tmax - random.uniform(8, 15), 1)

    return WeatherResponse(
        field_id=field_id,
        date=d,
        tmax=tmax,
        tmin=tmin,
        tmean=round((tmax + tmin) / 2, 1),
        rain_mm=round(random.uniform(*profile["rain"]), 1),
        humidity=round(random.uniform(*profile["humidity"]), 1),
        wind_speed=round(random.uniform(0.5, 8.0), 1),
        wind_direction=random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
        pressure_hpa=round(random.uniform(1010, 1025), 1),
        uv_index=round(random.uniform(5, 11), 1),
        visibility_km=round(random.uniform(8, 20), 1),
    )

@app.get("/api/v1/weather/fields/{field_id}/forecast", response_model=WeatherForecastResponse)
async def get_forecast(field_id: int, days: int = 7):
    """الحصول على توقعات الطقس للأيام القادمة"""
    from datetime import timedelta

    forecasts = []
    base_date = date.today()
    descriptions = [
        "صحو مع ارتفاع في درجات الحرارة",
        "غائم جزئياً",
        "احتمال أمطار خفيفة",
        "طقس معتدل",
        "رياح نشطة",
        "صحو",
        "غائم مع احتمال زخات مطرية",
    ]

    for i in range(days):
        d = base_date + timedelta(days=i)
        tmax = round(random.uniform(20, 32), 1)
        forecasts.append(WeatherForecast(
            date=d,
            tmax=tmax,
            tmin=round(tmax - random.uniform(8, 12), 1),
            rain_probability=round(random.uniform(0, 60), 0),
            description_ar=random.choice(descriptions),
        ))

    return WeatherForecastResponse(field_id=field_id, forecasts=forecasts)

@app.get("/api/v1/weather/alerts")
async def get_weather_alerts(region_id: Optional[int] = None):
    """الحصول على تنبيهات الطقس"""
    return {
        "alerts": [
            {
                "id": "alert-001",
                "type": "heat_wave",
                "severity": "medium",
                "title_ar": "موجة حرارة متوقعة",
                "description_ar": "ارتفاع ملحوظ في درجات الحرارة خلال الأيام القادمة",
                "affected_regions": ["Sanaa", "Marib", "Al Jawf"],
                "valid_from": str(date.today()),
                "valid_until": str(date.today()),
            }
        ]
    }
