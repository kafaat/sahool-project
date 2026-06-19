"""
Health check endpoints
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from ...models import get_db
from ...schemas.advisor import HealthCheckResponse
from ...core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """Basic health check"""
    # Check database
    db_status = "unknown"
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return HealthCheckResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        service=settings.service_name,
        version=settings.service_version,
        timestamp=datetime.utcnow(),
        database=db_status,
        dependencies={
            "ndvi_service": settings.ndvi_service_url,
            "weather_api": settings.weather_api_url,
        },
    )


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}


@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}
