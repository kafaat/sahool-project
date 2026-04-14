"""
Weather Service - خدمة الطقس
Sahool Yemen v9.0.0

This service provides weather data for fields and regions.
"""

import sys
sys.path.insert(0, "/app/libs-shared")

from contextlib import asynccontextmanager  # noqa: E402
from datetime import date, timedelta  # noqa: E402
from typing import Optional  # noqa: E402
from uuid import UUID  # noqa: E402

from fastapi import FastAPI, Depends, HTTPException  # noqa: E402
from fastapi.responses import Response  # noqa: E402
from prometheus_client import Counter, Histogram, generate_latest  # noqa: E402
from sqlalchemy import select, and_  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from sahool_shared.models import WeatherData, Field, Region  # noqa: E402
from sahool_shared.schemas.weather import (  # noqa: E402
    WeatherForecast, WeatherData as WeatherDataSchema
)
from sahool_shared.schemas.common import HealthResponse, ErrorResponse  # noqa: E402
from sahool_shared.auth import get_current_user, AuthenticatedUser  # noqa: E402
from sahool_shared.utils import get_db, setup_logging, get_logger  # noqa: E402
from sahool_shared.cache import cached  # noqa: E402
from sahool_shared.events import publish_event, WeatherUpdatedEvent  # noqa: E402

# Metrics
REQUEST_COUNT = Counter("weather_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("weather_request_latency_seconds", "Request latency", ["method", "endpoint"])

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging(service_name="weather-service")
    logger.info("weather_service_starting", version="9.0.0")
    yield
    logger.info("weather_service_stopping")


app = FastAPI(
    title="Sahool Weather Service",
    description="خدمة الطقس لمنصة سهول اليمن",
    version="9.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="9.0.0",
        service="weather-service"
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


@app.get(
    "/api/v1/weather/fields/{field_id}",
    response_model=WeatherForecast,
    responses={404: {"model": ErrorResponse}},
)
@cached(ttl=1800, prefix="weather:field")
async def get_field_weather(
    field_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get weather data for a specific field.
    الحصول على بيانات الطقس لحقل معين
    """
    # Get field with tenant check
    result = await db.execute(
        select(Field).where(
            and_(Field.id == field_id, Field.tenant_id == UUID(user.tenant_id))
        )
    )
    field = result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=404, detail="الحقل غير موجود")

    # Get latest weather data
    weather_result = await db.execute(
        select(WeatherData)
        .where(WeatherData.field_id == field_id)
        .order_by(WeatherData.forecast_date.desc())
        .limit(6)
    )
    weather_records = weather_result.scalars().all()

    if not weather_records:
        # Return mock data if no records
        return await _generate_weather_forecast(field_id, str(user.tenant_id))

    current = weather_records[0]
    forecast = weather_records[1:] if len(weather_records) > 1 else []

    return WeatherForecast(
        location_id=str(field_id),
        location_type="field",
        current=WeatherDataSchema(
            date=current.forecast_date or date.today(),
            temperature=float(current.temperature or 25),
            humidity=float(current.humidity or 50),
            rainfall=float(current.rainfall or 0),
            wind_speed=float(current.wind_speed or 3),
            wind_direction=current.wind_direction or "N",
            pressure=float(current.pressure or 1013) if current.pressure else None,
            solar_radiation=float(current.solar_radiation) if current.solar_radiation else None,
        ),
        forecast=[
            WeatherDataSchema(
                date=w.forecast_date or date.today(),
                temperature=float(w.temperature or 25),
                humidity=float(w.humidity or 50),
                rainfall=float(w.rainfall or 0),
                wind_speed=float(w.wind_speed or 3),
                wind_direction=w.wind_direction or "N",
                pressure=float(w.pressure or 1013) if w.pressure else None,
            )
            for w in forecast
        ],
        source=current.source or "OpenWeather",
    )


@app.get(
    "/api/v1/weather/regions/{region_id}",
    response_model=WeatherForecast,
)
@cached(ttl=1800, prefix="weather:region")
async def get_region_weather(
    region_id: int,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get weather data for a region.
    الحصول على بيانات الطقس لمنطقة
    """
    # Get region
    result = await db.execute(select(Region).where(Region.id == region_id))
    region = result.scalar_one_or_none()

    if not region:
        raise HTTPException(status_code=404, detail="المنطقة غير موجودة")

    # Get latest weather data for region
    weather_result = await db.execute(
        select(WeatherData)
        .where(WeatherData.region_id == region_id)
        .order_by(WeatherData.forecast_date.desc())
        .limit(6)
    )
    weather_records = weather_result.scalars().all()

    if not weather_records:
        return await _generate_weather_forecast(None, str(user.tenant_id), region_id)

    current = weather_records[0]
    forecast = weather_records[1:] if len(weather_records) > 1 else []

    return WeatherForecast(
        location_id=str(region_id),
        location_type="region",
        current=WeatherDataSchema(
            date=current.forecast_date or date.today(),
            temperature=float(current.temperature or 25),
            humidity=float(current.humidity or 50),
            rainfall=float(current.rainfall or 0),
            wind_speed=float(current.wind_speed or 3),
            wind_direction=current.wind_direction or "N",
        ),
        forecast=[
            WeatherDataSchema(
                date=w.forecast_date or date.today(),
                temperature=float(w.temperature or 25),
                humidity=float(w.humidity or 50),
                rainfall=float(w.rainfall or 0),
                wind_speed=float(w.wind_speed or 3),
                wind_direction=w.wind_direction or "N",
            )
            for w in forecast
        ],
        source=current.source or "OpenWeather",
    )


async def _generate_weather_forecast(
    field_id: Optional[UUID],
    tenant_id: str,
    region_id: Optional[int] = None,
) -> WeatherForecast:
    """Generate weather forecast (mock data for demo)."""
    import random

    today = date.today()

    # Yemen weather profiles
    profiles = {
        "coastal": {"temp_base": 30, "humidity_base": 70, "rain_chance": 0.1},
        "highland": {"temp_base": 22, "humidity_base": 45, "rain_chance": 0.2},
        "desert": {"temp_base": 35, "humidity_base": 25, "rain_chance": 0.05},
    }
    profile = profiles.get("highland")  # Default to highland

    def generate_day(d: date) -> WeatherDataSchema:
        return WeatherDataSchema(
            date=d,
            temperature=round(profile["temp_base"] + random.uniform(-5, 8), 1),
            humidity=round(profile["humidity_base"] + random.uniform(-15, 20), 1),
            rainfall=round(random.uniform(0, 10) if random.random() < profile["rain_chance"] else 0, 1),
            wind_speed=round(random.uniform(1, 8), 1),
            wind_direction=random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
            pressure=round(1013 + random.uniform(-10, 10), 1),
            solar_radiation=round(random.uniform(300, 700), 0),
        )

    current = generate_day(today)
    forecast = [generate_day(today + timedelta(days=i)) for i in range(1, 6)]

    # Publish event
    await publish_event(
        WeatherUpdatedEvent.create(
            region_id=region_id,
            field_id=str(field_id) if field_id else None,
            tenant_id=tenant_id,
            temperature=current.temperature,
            humidity=current.humidity,
            rainfall=current.rainfall,
            forecast_date=today,
        )
    )

    return WeatherForecast(
        location_id=str(field_id) if field_id else str(region_id),
        location_type="field" if field_id else "region",
        current=current,
        forecast=forecast,
        source="Demo",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
