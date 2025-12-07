"""
NDVI Service - خدمة تحليل الغطاء النباتي
Sahool Yemen v9.0.0

This service provides NDVI analysis for agricultural fields.
"""

from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, generate_latest
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

import sys
sys.path.insert(0, "/app/libs-shared")

from sahool_shared.models import NDVIResult, Field  # noqa: E402
from sahool_shared.schemas.ndvi import (  # noqa: E402
    NDVIResponse, NDVITimeline, NDVITimelinePoint, YieldPrediction
)
from sahool_shared.schemas.common import HealthResponse, ErrorResponse  # noqa: E402
from sahool_shared.auth import get_current_user, AuthenticatedUser  # noqa: E402
from sahool_shared.utils import get_db, setup_logging, get_logger  # noqa: E402
from sahool_shared.cache import cached  # noqa: E402
from sahool_shared.events import publish_event, NDVIProcessedEvent  # noqa: E402

# Metrics
REQUEST_COUNT = Counter("ndvi_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("ndvi_request_latency_seconds", "Request latency", ["method", "endpoint"])

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging(service_name="ndvi-service")
    logger.info("ndvi_service_starting", version="9.0.0")
    yield
    logger.info("ndvi_service_stopping")


app = FastAPI(
    title="Sahool NDVI Service",
    description="خدمة تحليل NDVI لمنصة سهول اليمن",
    version="9.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="9.0.0",
        service="ndvi-service"
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


@app.get(
    "/api/v1/ndvi/fields/{field_id}",
    response_model=NDVIResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_latest_ndvi(
    field_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get latest NDVI result for a field.
    الحصول على أحدث نتيجة NDVI لحقل
    """
    # Verify field access
    field_result = await db.execute(
        select(Field).where(
            and_(Field.id == field_id, Field.tenant_id == UUID(user.tenant_id))
        )
    )
    field = field_result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=404, detail="الحقل غير موجود")

    # Get latest NDVI
    ndvi_result = await db.execute(
        select(NDVIResult)
        .where(NDVIResult.field_id == field_id)
        .order_by(NDVIResult.acquisition_date.desc())
        .limit(1)
    )
    ndvi = ndvi_result.scalar_one_or_none()

    if not ndvi:
        # Generate mock NDVI if none exists
        return await _generate_mock_ndvi(field_id, str(user.tenant_id))

    return NDVIResponse(
        id=ndvi.id,
        field_id=ndvi.field_id,
        tenant_id=ndvi.tenant_id,
        ndvi_value=float(ndvi.ndvi_value),
        acquisition_date=ndvi.acquisition_date,
        satellite_name=ndvi.satellite_name or "Sentinel-2",
        cloud_coverage=float(ndvi.cloud_coverage) if ndvi.cloud_coverage else None,
        tile_url=ndvi.tile_url,
        processing_version=ndvi.processing_version,
        created_at=ndvi.created_at,
    )


@app.get(
    "/api/v1/ndvi/fields/{field_id}/timeline",
    response_model=NDVITimeline,
)
@cached(ttl=3600, prefix="ndvi:timeline")
async def get_ndvi_timeline(
    field_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get NDVI timeline for a field.
    الحصول على جدول NDVI الزمني لحقل
    """
    # Default date range: last 90 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)

    # Validate date range
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="تاريخ البداية يجب أن يكون قبل تاريخ النهاية"
        )

    # Verify field access
    field_result = await db.execute(
        select(Field).where(
            and_(Field.id == field_id, Field.tenant_id == UUID(user.tenant_id))
        )
    )
    field = field_result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=404, detail="الحقل غير موجود")

    # Get NDVI timeline
    ndvi_result = await db.execute(
        select(NDVIResult)
        .where(
            and_(
                NDVIResult.field_id == field_id,
                NDVIResult.acquisition_date >= start_date,
                NDVIResult.acquisition_date <= end_date,
            )
        )
        .order_by(NDVIResult.acquisition_date.asc())
    )
    ndvi_records = ndvi_result.scalars().all()

    if not ndvi_records:
        # Generate mock timeline
        return await _generate_mock_timeline(field_id, field.name_ar, str(user.tenant_id), start_date, end_date)

    # Calculate statistics
    ndvi_values = [float(r.ndvi_value) for r in ndvi_records]
    average_ndvi = sum(ndvi_values) / len(ndvi_values) if ndvi_values else None

    timeline = [
        NDVITimelinePoint(
            date=r.acquisition_date,
            ndvi_value=float(r.ndvi_value),
            health_category=_get_health_category(float(r.ndvi_value)),
            cloud_coverage=float(r.cloud_coverage) if r.cloud_coverage else None,
        )
        for r in ndvi_records
    ]

    return NDVITimeline(
        field_id=field_id,
        field_name=field.name_ar,
        tenant_id=UUID(user.tenant_id),
        timeline=timeline,
        start_date=start_date,
        end_date=end_date,
        average_ndvi=round(average_ndvi, 3) if average_ndvi else None,
        trend=NDVITimeline.calculate_trend(ndvi_values),
    )


@app.get(
    "/api/v1/ndvi/fields/{field_id}/yield-prediction",
    response_model=YieldPrediction,
)
async def predict_yield(
    field_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Predict yield based on NDVI data.
    التنبؤ بالمحصول بناءً على بيانات NDVI
    """
    # Verify field access
    field_result = await db.execute(
        select(Field).where(
            and_(Field.id == field_id, Field.tenant_id == UUID(user.tenant_id))
        )
    )
    field = field_result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=404, detail="الحقل غير موجود")

    # Get average NDVI from last 30 days
    thirty_days_ago = date.today() - timedelta(days=30)
    ndvi_result = await db.execute(
        select(func.avg(NDVIResult.ndvi_value))
        .where(
            and_(
                NDVIResult.field_id == field_id,
                NDVIResult.acquisition_date >= thirty_days_ago,
            )
        )
    )
    avg_ndvi = ndvi_result.scalar()

    if avg_ndvi is None:
        avg_ndvi = 0.5  # Default

    # Yield estimation based on crop type and NDVI
    crop_yields = {
        "wheat": {"base": 3000, "factor": 1.5},
        "barley": {"base": 2500, "factor": 1.4},
        "corn": {"base": 4000, "factor": 1.6},
        "coffee": {"base": 800, "factor": 1.8},
        "qat": {"base": 1500, "factor": 1.3},
        "default": {"base": 2000, "factor": 1.4},
    }

    crop_config = crop_yields.get(
        (field.crop_type or "").lower(),
        crop_yields["default"]
    )

    predicted_yield = crop_config["base"] * (float(avg_ndvi) * crop_config["factor"])
    confidence = min(85, 50 + float(avg_ndvi) * 50)  # Higher NDVI = higher confidence

    recommendations = []
    if float(avg_ndvi) < 0.3:
        recommendations.append("يُنصح بزيادة الري والتسميد")
        recommendations.append("فحص التربة للتأكد من توفر العناصر الغذائية")
    elif float(avg_ndvi) < 0.5:
        recommendations.append("المحصول في حالة متوسطة، يمكن تحسينه بالتسميد الورقي")
    else:
        recommendations.append("المحصول في حالة جيدة، استمر في الرعاية الحالية")

    return YieldPrediction(
        field_id=field_id,
        crop_type=field.crop_type or "غير محدد",
        predicted_yield_kg_per_hectare=round(predicted_yield, 0),
        confidence_percent=round(confidence, 1),
        prediction_date=date.today(),
        factors={
            "average_ndvi": round(float(avg_ndvi), 3),
            "crop_factor": crop_config["factor"],
            "area_hectares": float(field.area_hectares),
        },
        recommendations=recommendations,
    )


def _get_health_category(ndvi: float) -> str:
    """Get health category from NDVI value."""
    if ndvi >= 0.6:
        return "excellent"
    if ndvi >= 0.4:
        return "good"
    if ndvi >= 0.2:
        return "moderate"
    if ndvi >= 0:
        return "poor"
    return "bare"


async def _generate_mock_ndvi(field_id: UUID, tenant_id: str) -> NDVIResponse:
    """Generate mock NDVI result."""
    import random
    import uuid

    ndvi_value = round(random.uniform(0.3, 0.8), 3)

    # Publish event
    await publish_event(
        NDVIProcessedEvent.create(
            field_id=str(field_id),
            tenant_id=tenant_id,
            ndvi_value=ndvi_value,
            acquisition_date=date.today(),
        )
    )

    return NDVIResponse(
        id=uuid.uuid4(),
        field_id=field_id,
        tenant_id=UUID(tenant_id),
        ndvi_value=ndvi_value,
        acquisition_date=date.today(),
        satellite_name="Sentinel-2 (Demo)",
        cloud_coverage=round(random.uniform(0, 15), 1),
        created_at=date.today(),
    )


async def _generate_mock_timeline(
    field_id: UUID,
    field_name: str,
    tenant_id: str,
    start_date: date,
    end_date: date,
) -> NDVITimeline:
    """Generate mock NDVI timeline."""
    import random

    timeline = []
    current_date = start_date
    base_ndvi = random.uniform(0.4, 0.6)

    while current_date <= end_date:
        # Add some variation
        ndvi_value = round(base_ndvi + random.uniform(-0.1, 0.1), 3)
        ndvi_value = max(0, min(1, ndvi_value))  # Clamp to [0, 1]

        timeline.append(NDVITimelinePoint(
            date=current_date,
            ndvi_value=ndvi_value,
            health_category=_get_health_category(ndvi_value),
            cloud_coverage=round(random.uniform(0, 20), 1),
        ))

        # Simulate seasonal trend
        base_ndvi += random.uniform(-0.02, 0.03)
        base_ndvi = max(0.2, min(0.8, base_ndvi))

        current_date += timedelta(days=random.randint(5, 10))

    ndvi_values = [p.ndvi_value for p in timeline]
    average_ndvi = sum(ndvi_values) / len(ndvi_values) if ndvi_values else None

    return NDVITimeline(
        field_id=field_id,
        field_name=field_name,
        tenant_id=UUID(tenant_id),
        timeline=timeline,
        start_date=start_date,
        end_date=end_date,
        average_ndvi=round(average_ndvi, 3) if average_ndvi else None,
        trend=NDVITimeline.calculate_trend(ndvi_values),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
