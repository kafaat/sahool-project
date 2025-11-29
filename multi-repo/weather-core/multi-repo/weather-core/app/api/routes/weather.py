from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.weather import WeatherForecastResponse, WeatherIngestRequest
from app.services.weather_service import get_forecast_for_field, ingest_weather_points

router = APIRouter(prefix="/api/v1/weather", tags=["weather"])

@router.get("/forecast", response_model=WeatherForecastResponse)
def get_forecast_endpoint(
    tenant_id: int = Query(...),
    field_id: int = Query(...),
    hours_ahead: int = Query(72, ge=1, le=240),
    db: Session = Depends(get_db),
):
    return get_forecast_for_field(db, tenant_id, field_id, hours_ahead=hours_ahead)

@router.post("/ingest")
def ingest_weather_endpoint(
    payload: WeatherIngestRequest,
    db: Session = Depends(get_db),
):
    """Ingest weather time-series points for a field.

    This endpoint is called by weather-ingestor after fetching
    data from external APIs (e.g. Open-Meteo)."""
    count = ingest_weather_points(db, payload)
    return {"ingested": count}
