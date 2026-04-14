"""
Zones Engine - محرك مناطق الإدارة الزراعية
Sahool Yemen v9.0.0

Calculates and manages agricultural management zones based on NDVI clustering.
"""

import sys
sys.path.insert(0, "/app/libs-shared")

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
import statistics

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field as PydanticField
from prometheus_client import Counter, Histogram, generate_latest
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from sahool_shared.models import Field, NDVIResult
from sahool_shared.schemas.common import HealthResponse
from sahool_shared.auth import get_current_user, AuthenticatedUser
from sahool_shared.utils import get_db, setup_logging, get_logger

# Metrics
REQUEST_COUNT = Counter("zones_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("zones_request_latency_seconds", "Request latency", ["endpoint"])

logger = get_logger(__name__)


# =============================================================================
# Schemas
# =============================================================================

class ManagementZone(BaseModel):
    """Management zone definition."""
    zone_id: int
    name_ar: str
    name_en: str
    ndvi_min: float
    ndvi_max: float
    health_status: str
    color: str
    area_percentage: float
    recommendation_ar: str
    recommendation_en: str


class ZoneClassification(BaseModel):
    """Classification result for a point or area."""
    zone: ManagementZone
    ndvi_value: float
    confidence: float


class FieldZonesResult(BaseModel):
    """Result of zone calculation for a field."""
    field_id: UUID
    field_name: str
    calculation_date: datetime
    zones: List[ManagementZone]
    dominant_zone: ManagementZone
    avg_ndvi: float
    ndvi_std: float
    data_points: int
    needs_attention: bool


class ZoneHistoryPoint(BaseModel):
    """Historical zone distribution point."""
    date: datetime
    zones_distribution: Dict[str, float]
    dominant_zone: str


class ZoneHistoryResponse(BaseModel):
    """Zone history response."""
    field_id: UUID
    history: List[ZoneHistoryPoint]
    trend: str


class ZoneRecommendation(BaseModel):
    """Zone-specific recommendation."""
    zone_id: int
    zone_name: str
    priority: str
    action_ar: str
    action_en: str
    expected_improvement: str


class FieldRecommendationsResponse(BaseModel):
    """Recommendations based on zone analysis."""
    field_id: UUID
    recommendations: List[ZoneRecommendation]
    overall_health: str
    priority_areas: List[str]


# =============================================================================
# Zone Definitions (Standard Agricultural Management Zones)
# =============================================================================

MANAGEMENT_ZONES = [
    ManagementZone(
        zone_id=1,
        name_ar="منطقة ممتازة",
        name_en="Excellent Zone",
        ndvi_min=0.7,
        ndvi_max=1.0,
        health_status="excellent",
        color="#1a9850",
        area_percentage=0,
        recommendation_ar="الحفاظ على الممارسات الحالية",
        recommendation_en="Maintain current practices",
    ),
    ManagementZone(
        zone_id=2,
        name_ar="منطقة جيدة",
        name_en="Good Zone",
        ndvi_min=0.5,
        ndvi_max=0.7,
        health_status="good",
        color="#91cf60",
        area_percentage=0,
        recommendation_ar="مراقبة دورية",
        recommendation_en="Regular monitoring",
    ),
    ManagementZone(
        zone_id=3,
        name_ar="منطقة معتدلة",
        name_en="Moderate Zone",
        ndvi_min=0.3,
        ndvi_max=0.5,
        health_status="moderate",
        color="#fee08b",
        area_percentage=0,
        recommendation_ar="زيادة الري والتسميد",
        recommendation_en="Increase irrigation and fertilization",
    ),
    ManagementZone(
        zone_id=4,
        name_ar="منطقة ضعيفة",
        name_en="Poor Zone",
        ndvi_min=0.15,
        ndvi_max=0.3,
        health_status="poor",
        color="#fc8d59",
        area_percentage=0,
        recommendation_ar="تدخل عاجل - فحص الآفات والأمراض",
        recommendation_en="Urgent intervention - check for pests and diseases",
    ),
    ManagementZone(
        zone_id=5,
        name_ar="منطقة حرجة",
        name_en="Critical Zone",
        ndvi_min=0.0,
        ndvi_max=0.15,
        health_status="critical",
        color="#d73027",
        area_percentage=0,
        recommendation_ar="تدخل فوري - إعادة تأهيل",
        recommendation_en="Immediate intervention - rehabilitation required",
    ),
]


def classify_ndvi(ndvi_value: float) -> ManagementZone:
    """Classify NDVI value into management zone."""
    for zone in MANAGEMENT_ZONES:
        if zone.ndvi_min <= ndvi_value < zone.ndvi_max:
            return zone
    # Default to last zone for edge cases
    return MANAGEMENT_ZONES[-1] if ndvi_value < 0.15 else MANAGEMENT_ZONES[0]


# =============================================================================
# Application Setup
# =============================================================================

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging(service_name="zones-engine")
    logger.info("zones_engine_starting", version="9.0.0")
    yield
    logger.info("zones_engine_stopping")


app = FastAPI(
    title="Sahool Zones Engine",
    description="محرك مناطق الإدارة الزراعية - Agricultural Management Zones Engine",
    version="9.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=bool(CORS_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health & Metrics
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="9.0.0", service="zones-engine")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


# =============================================================================
# Zones Endpoints
# =============================================================================

@app.get("/api/v1/zones/definitions", response_model=List[ManagementZone])
async def get_zone_definitions():
    """
    Get all management zone definitions.
    الحصول على تعريفات مناطق الإدارة
    """
    return MANAGEMENT_ZONES


@app.get("/api/v1/zones/field/{field_id}", response_model=FieldZonesResult)
async def get_field_zones(
    field_id: UUID,
    days: int = Query(30, ge=7, le=90, description="Days of NDVI data to analyze"),
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get management zones for a field based on recent NDVI data.
    الحصول على مناطق الإدارة لحقل بناءً على بيانات NDVI الأخيرة
    """
    with REQUEST_LATENCY.labels(endpoint="field_zones").time():
        tenant_id = UUID(user.tenant_id)

        # Verify field belongs to tenant
        field_result = await db.execute(
            select(Field.id, Field.name_ar)
            .where(and_(Field.id == field_id, Field.tenant_id == tenant_id))
        )
        field = field_result.one_or_none()

        if not field:
            raise HTTPException(status_code=404, detail="الحقل غير موجود")

        # Get NDVI data for the period
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        ndvi_result = await db.execute(
            select(NDVIResult.ndvi_value, NDVIResult.acquisition_date)
            .where(
                and_(
                    NDVIResult.field_id == field_id,
                    NDVIResult.acquisition_date >= start_date,
                    NDVIResult.acquisition_date <= end_date,
                )
            )
            .order_by(desc(NDVIResult.acquisition_date))
        )
        ndvi_data = ndvi_result.all()

        if not ndvi_data:
            raise HTTPException(status_code=404, detail="لا توجد بيانات NDVI لهذا الحقل")

        # Calculate zone distribution
        ndvi_values = [float(row[0]) for row in ndvi_data]
        avg_ndvi = statistics.mean(ndvi_values)
        ndvi_std = statistics.stdev(ndvi_values) if len(ndvi_values) > 1 else 0.0

        # Count values in each zone
        zone_counts = {zone.zone_id: 0 for zone in MANAGEMENT_ZONES}
        for ndvi in ndvi_values:
            zone = classify_ndvi(ndvi)
            zone_counts[zone.zone_id] += 1

        total_points = len(ndvi_values)
        zones_with_percentages = []

        for zone in MANAGEMENT_ZONES:
            count = zone_counts[zone.zone_id]
            percentage = (count / total_points) * 100 if total_points > 0 else 0

            zones_with_percentages.append(ManagementZone(
                zone_id=zone.zone_id,
                name_ar=zone.name_ar,
                name_en=zone.name_en,
                ndvi_min=zone.ndvi_min,
                ndvi_max=zone.ndvi_max,
                health_status=zone.health_status,
                color=zone.color,
                area_percentage=round(percentage, 2),
                recommendation_ar=zone.recommendation_ar,
                recommendation_en=zone.recommendation_en,
            ))

        # Determine dominant zone
        dominant_zone = classify_ndvi(avg_ndvi)
        dominant_zone_updated = ManagementZone(
            zone_id=dominant_zone.zone_id,
            name_ar=dominant_zone.name_ar,
            name_en=dominant_zone.name_en,
            ndvi_min=dominant_zone.ndvi_min,
            ndvi_max=dominant_zone.ndvi_max,
            health_status=dominant_zone.health_status,
            color=dominant_zone.color,
            area_percentage=zone_counts[dominant_zone.zone_id] / total_points * 100 if total_points > 0 else 0,
            recommendation_ar=dominant_zone.recommendation_ar,
            recommendation_en=dominant_zone.recommendation_en,
        )

        # Determine if field needs attention
        poor_critical_percentage = sum(
            z.area_percentage for z in zones_with_percentages
            if z.health_status in ("poor", "critical")
        )
        needs_attention = poor_critical_percentage > 20 or avg_ndvi < 0.3

        REQUEST_COUNT.labels(method="GET", endpoint="field_zones", status="success").inc()

        return FieldZonesResult(
            field_id=field_id,
            field_name=field.name_ar,
            calculation_date=datetime.now(timezone.utc),
            zones=zones_with_percentages,
            dominant_zone=dominant_zone_updated,
            avg_ndvi=round(avg_ndvi, 4),
            ndvi_std=round(ndvi_std, 4),
            data_points=total_points,
            needs_attention=needs_attention,
        )


@app.post("/api/v1/zones/calculate/{field_id}", response_model=FieldZonesResult)
async def calculate_zones(
    field_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Trigger zone calculation for a field.
    حساب مناطق الإدارة لحقل
    """
    # Reuse get_field_zones logic
    return await get_field_zones(field_id=field_id, days=30, db=db, user=user)


@app.get("/api/v1/zones/classify")
async def classify_point(
    ndvi: float = Query(..., ge=-1, le=1, description="NDVI value to classify"),
):
    """
    Classify a single NDVI value into a management zone.
    تصنيف قيمة NDVI واحدة إلى منطقة إدارة
    """
    with REQUEST_LATENCY.labels(endpoint="classify").time():
        zone = classify_ndvi(ndvi)

        REQUEST_COUNT.labels(method="GET", endpoint="classify", status="success").inc()

        return ZoneClassification(
            zone=zone,
            ndvi_value=ndvi,
            confidence=0.95 if zone.ndvi_min < ndvi < zone.ndvi_max - 0.05 else 0.75,
        )


@app.get("/api/v1/zones/field/{field_id}/history", response_model=ZoneHistoryResponse)
async def get_zone_history(
    field_id: UUID,
    months: int = Query(6, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get historical zone distribution for a field.
    الحصول على التوزيع التاريخي للمناطق لحقل
    """
    with REQUEST_LATENCY.labels(endpoint="zone_history").time():
        tenant_id = UUID(user.tenant_id)

        # Verify field belongs to tenant
        field_result = await db.execute(
            select(Field.id).where(and_(Field.id == field_id, Field.tenant_id == tenant_id))
        )
        if not field_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="الحقل غير موجود")

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=months * 30)

        # Get monthly aggregated NDVI data
        ndvi_result = await db.execute(
            select(
                func.date_trunc('month', NDVIResult.acquisition_date).label("month"),
                func.avg(NDVIResult.ndvi_value).label("avg_ndvi"),
            )
            .where(
                and_(
                    NDVIResult.field_id == field_id,
                    NDVIResult.acquisition_date >= start_date,
                    NDVIResult.acquisition_date <= end_date,
                )
            )
            .group_by(func.date_trunc('month', NDVIResult.acquisition_date))
            .order_by(func.date_trunc('month', NDVIResult.acquisition_date))
        )
        rows = ndvi_result.all()

        history = []
        for row in rows:
            avg_ndvi = float(row.avg_ndvi)
            dominant = classify_ndvi(avg_ndvi)

            # Estimate zone distribution based on average (simplified)
            distribution = {}
            for zone in MANAGEMENT_ZONES:
                if zone.zone_id == dominant.zone_id:
                    distribution[zone.name_en] = 60.0
                elif abs(zone.zone_id - dominant.zone_id) == 1:
                    distribution[zone.name_en] = 20.0
                else:
                    distribution[zone.name_en] = 0.0

            history.append(ZoneHistoryPoint(
                date=row.month,
                zones_distribution=distribution,
                dominant_zone=dominant.name_en,
            ))

        # Determine trend
        if len(history) >= 2:
            first_zones = list(history[0].zones_distribution.keys())
            last_zones = list(history[-1].zones_distribution.keys())

            # Compare dominant zones
            first_dominant_idx = MANAGEMENT_ZONES.index(
                next(z for z in MANAGEMENT_ZONES if z.name_en == history[0].dominant_zone)
            )
            last_dominant_idx = MANAGEMENT_ZONES.index(
                next(z for z in MANAGEMENT_ZONES if z.name_en == history[-1].dominant_zone)
            )

            if last_dominant_idx < first_dominant_idx:
                trend = "improving"
            elif last_dominant_idx > first_dominant_idx:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        REQUEST_COUNT.labels(method="GET", endpoint="zone_history", status="success").inc()

        return ZoneHistoryResponse(
            field_id=field_id,
            history=history,
            trend=trend,
        )


@app.get("/api/v1/zones/field/{field_id}/recommendations", response_model=FieldRecommendationsResponse)
async def get_zone_recommendations(
    field_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get management recommendations based on zone analysis.
    الحصول على توصيات الإدارة بناءً على تحليل المناطق
    """
    with REQUEST_LATENCY.labels(endpoint="recommendations").time():
        # Get current zones
        zones_result = await get_field_zones(field_id=field_id, days=30, db=db, user=user)

        recommendations = []
        priority_areas = []

        for zone in zones_result.zones:
            if zone.area_percentage > 5:  # Only recommend for significant zones
                priority = "low"
                if zone.health_status == "critical":
                    priority = "critical"
                    priority_areas.append(zone.name_ar)
                elif zone.health_status == "poor":
                    priority = "high"
                    priority_areas.append(zone.name_ar)
                elif zone.health_status == "moderate":
                    priority = "medium"

                if zone.health_status in ("critical", "poor", "moderate"):
                    recommendations.append(ZoneRecommendation(
                        zone_id=zone.zone_id,
                        zone_name=zone.name_ar,
                        priority=priority,
                        action_ar=zone.recommendation_ar,
                        action_en=zone.recommendation_en,
                        expected_improvement=f"تحسين بنسبة {15 if priority == 'high' else 10}% خلال شهر"
                    ))

        overall_health = zones_result.dominant_zone.health_status

        REQUEST_COUNT.labels(method="GET", endpoint="recommendations", status="success").inc()

        return FieldRecommendationsResponse(
            field_id=field_id,
            recommendations=sorted(
                recommendations,
                key=lambda r: {"critical": 0, "high": 1, "medium": 2, "low": 3}[r.priority]
            ),
            overall_health=overall_health,
            priority_areas=priority_areas,
        )


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "zones-engine",
        "version": "9.0.0",
        "description": "Management Zones Engine - محرك مناطق الإدارة",
        "endpoints": [
            "GET /health",
            "GET /api/v1/zones/definitions",
            "GET /api/v1/zones/field/{field_id}",
            "POST /api/v1/zones/calculate/{field_id}",
            "GET /api/v1/zones/classify",
            "GET /api/v1/zones/field/{field_id}/history",
            "GET /api/v1/zones/field/{field_id}/recommendations",
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
