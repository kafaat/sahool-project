from fastapi import APIRouter, Query
from app.services.ingest_service import ingest_field_weather, WeatherIngestResult

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


@router.post("/field/{field_id}", response_model=WeatherIngestResult)
async def ingest_weather_for_field(
    field_id: int,
    tenant_id: int = Query(...),
):
    """Trigger weather ingestion for a specific field using Open-Meteo."""
    return await ingest_field_weather(field_id, tenant_id)
