from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.models.weather_forecast import WeatherForecast
from app.schemas.weather import WeatherForecastResponse, WeatherForecastPoint

def get_forecast_for_field(db: Session, tenant_id: int, field_id: int, hours_ahead: int = 72) -> WeatherForecastResponse:
    now = datetime.utcnow()
    until = now + timedelta(hours=hours_ahead)
    q = (
        db.query(WeatherForecast)
        .filter(
            WeatherForecast.tenant_id == tenant_id,
            WeatherForecast.field_id == field_id,
            WeatherForecast.timestamp >= now,
            WeatherForecast.timestamp <= until,
        )
        .order_by(WeatherForecast.timestamp.asc())
    )
    rows: List[WeatherForecast] = q.all()
    points = [
        WeatherForecastPoint(
            timestamp=r.timestamp,
            temp_c=r.temp_c,
            eto_mm=r.eto_mm,
            wind_speed_ms=r.wind_speed_ms,
            rel_humidity_pct=r.rel_humidity_pct,
            rain_mm=r.rain_mm,
        )
        for r in rows
    ]
    return WeatherForecastResponse(tenant_id=tenant_id, field_id=field_id, points=points)

def ingest_weather_points(db: Session, payload: "WeatherIngestRequest") -> int:
    """Ingest a batch of weather points for a field.

    Existing points for the same timestamp/field/tenant are not deduplicated here;
    in a real deployment you may want to either upsert or enforce uniqueness
    via constraints.
    """
    from app.models.weather_forecast import WeatherForecast  # local import to avoid cycles
    count = 0
    for p in payload.points:
        row = WeatherForecast(
            tenant_id=payload.tenant_id,
            field_id=payload.field_id,
            timestamp=p.timestamp,
            temp_c=p.temp_c,
            eto_mm=p.eto_mm,
            wind_speed_ms=p.wind_speed_ms,
            rel_humidity_pct=p.rel_humidity_pct,
            rain_mm=p.rain_mm,
        )
        db.add(row)
        count += 1
    db.commit()
    return count
