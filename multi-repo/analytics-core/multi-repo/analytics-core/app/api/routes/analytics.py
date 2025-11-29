
from fastapi import APIRouter, Query
from app.services.analytics_service import compute_health, compute_stress, generate_insights

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/field/{field_id}/health")
def field_health(field_id: int, ndvi: float, ph: float, ec: float, eto: float):
    return compute_health(ndvi, ph, ec, eto)

@router.get("/field/{field_id}/stress")
def field_stress(field_id: int, ec: float, eto: float, temp: float):
    return compute_stress(ec, eto, temp)

@router.get("/field/{field_id}/insights")
def field_insights(field_id: int, ndvi: float, ph: float, ec: float, eto: float, temp: float):
    h = compute_health(ndvi, ph, ec, eto)
    s = compute_stress(ec, eto, temp)
    return generate_insights(h, s)
