"""
Analytics Service - خدمة التحليلات
Sahool Yemen Platform v9.0.0

Provides agricultural analytics and insights with database persistence.
"""

import sys
sys.path.insert(0, "/app/libs-shared")

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field as PydanticField
from prometheus_client import Counter, Histogram, generate_latest
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from sahool_shared.models import Field, NDVIResult, WeatherData, Alert, YieldRecord
from sahool_shared.schemas.common import HealthResponse
from sahool_shared.auth import get_current_user, AuthenticatedUser
from sahool_shared.utils import get_db, setup_logging, get_logger

# Metrics
REQUEST_COUNT = Counter("analytics_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("analytics_request_latency_seconds", "Request latency", ["endpoint"])

logger = get_logger(__name__)


# =============================================================================
# Schemas
# =============================================================================

class DataPoint(BaseModel):
    """Single data point."""
    timestamp: datetime
    value: float
    unit: str


class FieldSummary(BaseModel):
    """Field analytics summary."""
    field_id: UUID
    name_ar: str
    name_en: Optional[str]
    area_hectares: float
    crop_type: Optional[str]
    latest_ndvi: Optional[float]
    health_status: str
    alert_count: int
    water_usage_m3: Optional[float] = None


class TenantOverview(BaseModel):
    """Tenant-wide analytics overview."""
    total_fields: int
    total_area_hectares: float
    avg_ndvi: Optional[float]
    health_distribution: Dict[str, int]
    crop_distribution: Dict[str, float]
    active_alerts: int
    fields_needing_attention: int


class NDVITrendPoint(BaseModel):
    """NDVI trend data point."""
    date: datetime
    value: float
    field_id: Optional[UUID] = None
    field_name: Optional[str] = None


class NDVITrendResponse(BaseModel):
    """NDVI trend response."""
    field_id: Optional[UUID]
    start_date: datetime
    end_date: datetime
    data_points: List[NDVITrendPoint]
    avg_ndvi: Optional[float]
    trend: str  # improving, declining, stable


class CropDistribution(BaseModel):
    """Crop distribution data."""
    crop_type: str
    field_count: int
    total_area_hectares: float
    percentage: float


class InsightItem(BaseModel):
    """AI-generated insight."""
    id: str
    type: str
    severity: str
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    field_id: Optional[UUID] = None
    recommendations: List[str]
    created_at: datetime


class InsightsResponse(BaseModel):
    """Insights response."""
    insights: List[InsightItem]
    total: int


class AnalyticsQueryRequest(BaseModel):
    """Custom analytics query request."""
    metric: str = PydanticField(..., description="Metric: ndvi, weather, yield, alerts")
    field_ids: Optional[List[UUID]] = None
    start_date: datetime
    end_date: datetime
    aggregation: str = PydanticField(default="daily", description="daily, weekly, monthly")


class AnalyticsQueryResponse(BaseModel):
    """Custom analytics query response."""
    metric: str
    aggregation: str
    data: List[DataPoint]
    summary: Dict[str, Any]


# =============================================================================
# Application Setup
# =============================================================================

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging(service_name="analytics-service")
    logger.info("analytics_service_starting", version="9.0.0")
    yield
    logger.info("analytics_service_stopping")


app = FastAPI(
    title="Sahool Analytics Service",
    description="خدمة التحليلات الزراعية",
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
    return HealthResponse(status="healthy", version="9.0.0", service="analytics-service")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


# =============================================================================
# Analytics Endpoints
# =============================================================================

@app.get("/api/v1/analytics/overview", response_model=TenantOverview)
async def get_tenant_overview(
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get tenant-wide analytics overview.
    نظرة عامة على تحليلات المستأجر
    """
    with REQUEST_LATENCY.labels(endpoint="overview").time():
        tenant_id = UUID(user.tenant_id)

        # Total fields and area
        fields_result = await db.execute(
            select(func.count(Field.id), func.sum(Field.area_hectares))
            .where(and_(Field.tenant_id == tenant_id, Field.status == "active"))
        )
        row = fields_result.one()
        total_fields = row[0] or 0
        total_area = float(row[1]) if row[1] else 0.0

        # Average NDVI from latest readings
        subquery = (
            select(NDVIResult.field_id, func.max(NDVIResult.acquisition_date).label("max_date"))
            .join(Field, NDVIResult.field_id == Field.id)
            .where(Field.tenant_id == tenant_id)
            .group_by(NDVIResult.field_id)
            .subquery()
        )

        ndvi_result = await db.execute(
            select(func.avg(NDVIResult.ndvi_value))
            .join(subquery, and_(
                NDVIResult.field_id == subquery.c.field_id,
                NDVIResult.acquisition_date == subquery.c.max_date
            ))
        )
        avg_ndvi = ndvi_result.scalar()
        avg_ndvi = float(avg_ndvi) if avg_ndvi else None

        # Health distribution based on NDVI
        health_distribution = {"excellent": 0, "good": 0, "moderate": 0, "poor": 0, "unknown": 0}

        latest_ndvi_query = await db.execute(
            select(NDVIResult.ndvi_value)
            .join(subquery, and_(
                NDVIResult.field_id == subquery.c.field_id,
                NDVIResult.acquisition_date == subquery.c.max_date
            ))
        )
        for (ndvi_val,) in latest_ndvi_query:
            if ndvi_val >= 0.6:
                health_distribution["excellent"] += 1
            elif ndvi_val >= 0.4:
                health_distribution["good"] += 1
            elif ndvi_val >= 0.2:
                health_distribution["moderate"] += 1
            else:
                health_distribution["poor"] += 1

        fields_with_ndvi = sum(health_distribution.values())
        health_distribution["unknown"] = max(0, total_fields - fields_with_ndvi)

        # Crop distribution
        crop_result = await db.execute(
            select(Field.crop_type, func.sum(Field.area_hectares))
            .where(and_(Field.tenant_id == tenant_id, Field.status == "active", Field.crop_type.isnot(None)))
            .group_by(Field.crop_type)
        )
        crop_distribution = {row[0]: float(row[1]) for row in crop_result.all()}

        # Active alerts
        alerts_result = await db.execute(
            select(func.count(Alert.id))
            .where(and_(Alert.tenant_id == tenant_id, Alert.status == "active"))
        )
        active_alerts = alerts_result.scalar() or 0

        # Fields needing attention (low NDVI or critical alerts)
        attention_needed = health_distribution["poor"] + health_distribution["moderate"]

        REQUEST_COUNT.labels(method="GET", endpoint="overview", status="success").inc()

        return TenantOverview(
            total_fields=total_fields,
            total_area_hectares=total_area,
            avg_ndvi=avg_ndvi,
            health_distribution=health_distribution,
            crop_distribution=crop_distribution,
            active_alerts=active_alerts,
            fields_needing_attention=attention_needed,
        )


@app.get("/api/v1/analytics/fields/{field_id}/summary", response_model=FieldSummary)
async def get_field_summary(
    field_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get field analytics summary.
    ملخص تحليلات الحقل
    """
    with REQUEST_LATENCY.labels(endpoint="field_summary").time():
        # Get field
        result = await db.execute(
            select(Field).where(
                and_(Field.id == field_id, Field.tenant_id == UUID(user.tenant_id))
            )
        )
        field = result.scalar_one_or_none()

        if not field:
            raise HTTPException(status_code=404, detail="الحقل غير موجود")

        # Get latest NDVI
        ndvi_result = await db.execute(
            select(NDVIResult.ndvi_value)
            .where(NDVIResult.field_id == field_id)
            .order_by(desc(NDVIResult.acquisition_date))
            .limit(1)
        )
        latest_ndvi = ndvi_result.scalar()

        # Calculate health status
        if latest_ndvi is None:
            health_status = "unknown"
        elif latest_ndvi >= 0.6:
            health_status = "excellent"
        elif latest_ndvi >= 0.4:
            health_status = "good"
        elif latest_ndvi >= 0.2:
            health_status = "moderate"
        else:
            health_status = "poor"

        # Count active alerts for this field
        alert_result = await db.execute(
            select(func.count(Alert.id))
            .where(and_(Alert.field_id == field_id, Alert.status == "active"))
        )
        alert_count = alert_result.scalar() or 0

        REQUEST_COUNT.labels(method="GET", endpoint="field_summary", status="success").inc()

        return FieldSummary(
            field_id=field.id,
            name_ar=field.name_ar,
            name_en=field.name_en,
            area_hectares=float(field.area_hectares),
            crop_type=field.crop_type,
            latest_ndvi=float(latest_ndvi) if latest_ndvi else None,
            health_status=health_status,
            alert_count=alert_count,
        )


@app.get("/api/v1/analytics/ndvi-trends", response_model=NDVITrendResponse)
async def get_ndvi_trends(
    field_id: Optional[UUID] = Query(None),
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get NDVI trends over time.
    اتجاهات NDVI عبر الزمن
    """
    with REQUEST_LATENCY.labels(endpoint="ndvi_trends").time():
        tenant_id = UUID(user.tenant_id)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        query = (
            select(NDVIResult.acquisition_date, NDVIResult.ndvi_value, NDVIResult.field_id, Field.name_ar)
            .join(Field, NDVIResult.field_id == Field.id)
            .where(
                and_(
                    Field.tenant_id == tenant_id,
                    NDVIResult.acquisition_date >= start_date,
                    NDVIResult.acquisition_date <= end_date,
                )
            )
        )

        if field_id:
            query = query.where(NDVIResult.field_id == field_id)

        query = query.order_by(NDVIResult.acquisition_date)
        result = await db.execute(query)
        rows = result.all()

        data_points = [
            NDVITrendPoint(
                date=row[0],
                value=float(row[1]),
                field_id=row[2],
                field_name=row[3],
            )
            for row in rows
        ]

        # Calculate average and trend
        if data_points:
            avg_ndvi = sum(p.value for p in data_points) / len(data_points)

            # Simple trend calculation: compare first half to second half
            half = len(data_points) // 2
            if half > 0:
                first_half_avg = sum(p.value for p in data_points[:half]) / half
                second_half_avg = sum(p.value for p in data_points[half:]) / (len(data_points) - half)

                if second_half_avg > first_half_avg + 0.05:
                    trend = "improving"
                elif second_half_avg < first_half_avg - 0.05:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "stable"
        else:
            avg_ndvi = None
            trend = "unknown"

        REQUEST_COUNT.labels(method="GET", endpoint="ndvi_trends", status="success").inc()

        return NDVITrendResponse(
            field_id=field_id,
            start_date=start_date,
            end_date=end_date,
            data_points=data_points,
            avg_ndvi=avg_ndvi,
            trend=trend,
        )


@app.get("/api/v1/analytics/crops", response_model=List[CropDistribution])
async def get_crop_distribution(
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get crop distribution across fields.
    توزيع المحاصيل عبر الحقول
    """
    with REQUEST_LATENCY.labels(endpoint="crops").time():
        tenant_id = UUID(user.tenant_id)

        # Get total area first
        total_result = await db.execute(
            select(func.sum(Field.area_hectares))
            .where(and_(Field.tenant_id == tenant_id, Field.status == "active"))
        )
        total_area = float(total_result.scalar() or 0) or 1.0  # Avoid division by zero

        # Get crop distribution
        result = await db.execute(
            select(
                Field.crop_type,
                func.count(Field.id),
                func.sum(Field.area_hectares),
            )
            .where(and_(Field.tenant_id == tenant_id, Field.status == "active"))
            .group_by(Field.crop_type)
        )

        distributions = []
        for row in result.all():
            crop_type = row[0] or "غير محدد"
            field_count = row[1]
            area = float(row[2]) if row[2] else 0
            percentage = (area / total_area) * 100

            distributions.append(CropDistribution(
                crop_type=crop_type,
                field_count=field_count,
                total_area_hectares=area,
                percentage=round(percentage, 2),
            ))

        REQUEST_COUNT.labels(method="GET", endpoint="crops", status="success").inc()

        return sorted(distributions, key=lambda x: x.total_area_hectares, reverse=True)


@app.get("/api/v1/analytics/insights", response_model=InsightsResponse)
async def get_insights(
    field_id: Optional[UUID] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get AI-generated insights based on field data.
    الحصول على رؤى ذكية بناءً على بيانات الحقول
    """
    with REQUEST_LATENCY.labels(endpoint="insights").time():
        tenant_id = UUID(user.tenant_id)
        insights = []
        now = datetime.now(timezone.utc)

        # Get fields with low NDVI
        low_ndvi_query = (
            select(Field.id, Field.name_ar, NDVIResult.ndvi_value)
            .join(NDVIResult, Field.id == NDVIResult.field_id)
            .where(
                and_(
                    Field.tenant_id == tenant_id,
                    NDVIResult.ndvi_value < 0.3,
                    NDVIResult.acquisition_date >= now - timedelta(days=14),
                )
            )
        )
        if field_id:
            low_ndvi_query = low_ndvi_query.where(Field.id == field_id)

        result = await db.execute(low_ndvi_query.limit(5))
        for row in result.all():
            insights.append(InsightItem(
                id=f"low_ndvi_{row[0]}",
                type="vegetation_health",
                severity="high",
                title_ar="صحة نباتية منخفضة",
                title_en="Low Vegetation Health",
                description_ar=f"حقل {row[1]} يظهر قراءات NDVI منخفضة ({row[2]:.2f})",
                description_en=f"Field {row[1]} shows low NDVI readings ({row[2]:.2f})",
                field_id=row[0],
                recommendations=[
                    "فحص الحقل للآفات أو الأمراض",
                    "التحقق من مستويات الري",
                    "اختبار تغذية التربة",
                ],
                created_at=now,
            ))

        # Get fields with critical alerts
        alert_query = (
            select(Alert.id, Alert.title_ar, Alert.field_id, Field.name_ar)
            .join(Field, Alert.field_id == Field.id, isouter=True)
            .where(
                and_(
                    Alert.tenant_id == tenant_id,
                    Alert.status == "active",
                    Alert.severity == "critical",
                )
            )
        )
        if field_id:
            alert_query = alert_query.where(Alert.field_id == field_id)

        result = await db.execute(alert_query.limit(5))
        for row in result.all():
            insights.append(InsightItem(
                id=f"alert_{row[0]}",
                type="alert",
                severity="critical",
                title_ar=row[1],
                title_en="Critical Alert",
                description_ar=f"تنبيه حرج للحقل {row[3] or 'عام'}",
                description_en=f"Critical alert for field {row[3] or 'general'}",
                field_id=row[2],
                recommendations=["مراجعة التنبيه واتخاذ الإجراءات اللازمة"],
                created_at=now,
            ))

        REQUEST_COUNT.labels(method="GET", endpoint="insights", status="success").inc()

        return InsightsResponse(insights=insights[:limit], total=len(insights))


@app.post("/api/v1/analytics/query", response_model=AnalyticsQueryResponse)
async def custom_query(
    request: AnalyticsQueryRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Execute custom analytics query.
    تنفيذ استعلام تحليلات مخصص
    """
    with REQUEST_LATENCY.labels(endpoint="custom_query").time():
        tenant_id = UUID(user.tenant_id)
        data_points = []
        summary = {}

        if request.metric == "ndvi":
            query = (
                select(NDVIResult.acquisition_date, func.avg(NDVIResult.ndvi_value))
                .join(Field, NDVIResult.field_id == Field.id)
                .where(
                    and_(
                        Field.tenant_id == tenant_id,
                        NDVIResult.acquisition_date >= request.start_date,
                        NDVIResult.acquisition_date <= request.end_date,
                    )
                )
            )

            if request.field_ids:
                query = query.where(NDVIResult.field_id.in_(request.field_ids))

            query = query.group_by(NDVIResult.acquisition_date).order_by(NDVIResult.acquisition_date)
            result = await db.execute(query)

            for row in result.all():
                data_points.append(DataPoint(
                    timestamp=row[0],
                    value=float(row[1]),
                    unit="index",
                ))

            if data_points:
                values = [p.value for p in data_points]
                summary = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "count": len(values),
                }

        elif request.metric == "alerts":
            query = (
                select(func.date(Alert.created_at), func.count(Alert.id))
                .where(
                    and_(
                        Alert.tenant_id == tenant_id,
                        Alert.created_at >= request.start_date,
                        Alert.created_at <= request.end_date,
                    )
                )
                .group_by(func.date(Alert.created_at))
                .order_by(func.date(Alert.created_at))
            )

            if request.field_ids:
                query = query.where(Alert.field_id.in_(request.field_ids))

            result = await db.execute(query)
            for row in result.all():
                data_points.append(DataPoint(
                    timestamp=datetime.combine(row[0], datetime.min.time()),
                    value=float(row[1]),
                    unit="count",
                ))

            if data_points:
                values = [p.value for p in data_points]
                summary = {"total": sum(values), "avg_per_day": sum(values) / len(values)}

        REQUEST_COUNT.labels(method="POST", endpoint="custom_query", status="success").inc()

        return AnalyticsQueryResponse(
            metric=request.metric,
            aggregation=request.aggregation,
            data=data_points,
            summary=summary,
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
