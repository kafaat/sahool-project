"""
Alerts Service - خدمة التنبيهات
Sahool Yemen Platform v9.0.0

Manages agricultural alerts and notifications with database persistence.
"""

import sys
sys.path.insert(0, "/app/libs-shared")

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field as PydanticField
from prometheus_client import Counter, Histogram, generate_latest
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from sahool_shared.models import Alert
from sahool_shared.models.alert import AlertSeverity, AlertType, AlertStatus
from sahool_shared.schemas.common import HealthResponse
from sahool_shared.auth import get_current_user, AuthenticatedUser
from sahool_shared.utils import get_db, setup_logging, get_logger

# Metrics
REQUEST_COUNT = Counter("alerts_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("alerts_request_latency_seconds", "Request latency", ["endpoint"])

logger = get_logger(__name__)


# =============================================================================
# Schemas
# =============================================================================

class AlertCreate(BaseModel):
    """Create alert request."""
    alert_type: str = PydanticField(..., description="Alert type: weather, ndvi, irrigation, pest, disease")
    severity: str = PydanticField(..., description="Severity: low, medium, high, critical")
    title_ar: str = PydanticField(..., min_length=2, max_length=200)
    title_en: Optional[str] = None
    message_ar: str = PydanticField(..., min_length=2)
    message_en: Optional[str] = None
    field_id: Optional[UUID] = None
    region_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    extra_data: Optional[dict] = None


class AlertResponse(BaseModel):
    """Alert response."""
    id: UUID
    tenant_id: UUID
    alert_type: str
    severity: str
    status: str
    title_ar: str
    title_en: Optional[str]
    message_ar: str
    message_en: Optional[str]
    field_id: Optional[UUID]
    region_id: Optional[int]
    expires_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    source: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Alert list response."""
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int


class AlertStats(BaseModel):
    """Alert statistics."""
    total: int
    active: int
    acknowledged: int
    resolved: int
    by_severity: dict
    by_type: dict


# =============================================================================
# Application Setup
# =============================================================================

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging(service_name="alerts-service")
    logger.info("alerts_service_starting", version="9.0.0")
    yield
    logger.info("alerts_service_stopping")


app = FastAPI(
    title="Sahool Alerts Service",
    description="خدمة التنبيهات الزراعية",
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
    return HealthResponse(status="healthy", version="9.0.0", service="alerts-service")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


# =============================================================================
# Alert Endpoints
# =============================================================================

@app.get("/api/v1/alerts", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    field_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    List alerts with optional filters.
    عرض التنبيهات مع فلاتر اختيارية
    """
    with REQUEST_LATENCY.labels(endpoint="list_alerts").time():
        query = select(Alert).where(Alert.tenant_id == UUID(user.tenant_id))

        if severity:
            query = query.where(Alert.severity == severity)
        if alert_type:
            query = query.where(Alert.alert_type == alert_type)
        if status_filter:
            query = query.where(Alert.status == status_filter)
        if field_id:
            query = query.where(Alert.field_id == field_id)

        # Count total
        count_query = select(func.count(Alert.id)).where(Alert.tenant_id == UUID(user.tenant_id))
        if severity:
            count_query = count_query.where(Alert.severity == severity)
        if alert_type:
            count_query = count_query.where(Alert.alert_type == alert_type)
        if status_filter:
            count_query = count_query.where(Alert.status == status_filter)
        if field_id:
            count_query = count_query.where(Alert.field_id == field_id)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate and order
        query = query.order_by(Alert.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        alerts = result.scalars().all()

        items = [
            AlertResponse(
                id=alert.id,
                tenant_id=alert.tenant_id,
                alert_type=alert.alert_type,
                severity=alert.severity,
                status=alert.status,
                title_ar=alert.title_ar,
                title_en=alert.title_en,
                message_ar=alert.message_ar,
                message_en=alert.message_en,
                field_id=alert.field_id,
                region_id=alert.region_id,
                expires_at=alert.expires_at,
                acknowledged_at=alert.acknowledged_at,
                resolved_at=alert.resolved_at,
                source=alert.source,
                created_at=alert.created_at,
                is_active=alert.is_active,
            )
            for alert in alerts
        ]

        REQUEST_COUNT.labels(method="GET", endpoint="list_alerts", status="success").inc()

        return AlertListResponse(items=items, total=total, page=page, page_size=page_size)


@app.post("/api/v1/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Create a new alert.
    إنشاء تنبيه جديد
    """
    with REQUEST_LATENCY.labels(endpoint="create_alert").time():
        alert = Alert(
            tenant_id=UUID(user.tenant_id),
            alert_type=data.alert_type,
            severity=data.severity,
            status=AlertStatus.ACTIVE.value,
            title_ar=data.title_ar,
            title_en=data.title_en,
            message_ar=data.message_ar,
            message_en=data.message_en,
            field_id=data.field_id,
            region_id=data.region_id,
            expires_at=data.expires_at,
            extra_data=data.extra_data,
            source="api",
        )

        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        logger.info("alert_created", alert_id=str(alert.id), type=alert.alert_type, severity=alert.severity)
        REQUEST_COUNT.labels(method="POST", endpoint="create_alert", status="success").inc()

        return AlertResponse(
            id=alert.id,
            tenant_id=alert.tenant_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            status=alert.status,
            title_ar=alert.title_ar,
            title_en=alert.title_en,
            message_ar=alert.message_ar,
            message_en=alert.message_en,
            field_id=alert.field_id,
            region_id=alert.region_id,
            expires_at=alert.expires_at,
            acknowledged_at=alert.acknowledged_at,
            resolved_at=alert.resolved_at,
            source=alert.source,
            created_at=alert.created_at,
            is_active=alert.is_active,
        )


@app.get("/api/v1/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get alert by ID.
    الحصول على تنبيه بالمعرف
    """
    result = await db.execute(
        select(Alert).where(
            and_(Alert.id == alert_id, Alert.tenant_id == UUID(user.tenant_id))
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="التنبيه غير موجود")

    return AlertResponse(
        id=alert.id,
        tenant_id=alert.tenant_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        status=alert.status,
        title_ar=alert.title_ar,
        title_en=alert.title_en,
        message_ar=alert.message_ar,
        message_en=alert.message_en,
        field_id=alert.field_id,
        region_id=alert.region_id,
        expires_at=alert.expires_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
        source=alert.source,
        created_at=alert.created_at,
        is_active=alert.is_active,
    )


@app.patch("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Acknowledge an alert.
    تأكيد استلام التنبيه
    """
    result = await db.execute(
        select(Alert).where(
            and_(Alert.id == alert_id, Alert.tenant_id == UUID(user.tenant_id))
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="التنبيه غير موجود")

    alert.acknowledge()
    await db.commit()

    logger.info("alert_acknowledged", alert_id=str(alert_id))

    return {"success": True, "message": "تم تأكيد استلام التنبيه"}


@app.patch("/api/v1/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Resolve an alert.
    حل التنبيه
    """
    result = await db.execute(
        select(Alert).where(
            and_(Alert.id == alert_id, Alert.tenant_id == UUID(user.tenant_id))
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="التنبيه غير موجود")

    alert.resolve()
    await db.commit()

    logger.info("alert_resolved", alert_id=str(alert_id))

    return {"success": True, "message": "تم حل التنبيه"}


@app.get("/api/v1/alerts/stats", response_model=AlertStats)
async def get_alert_stats(
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get alert statistics.
    إحصائيات التنبيهات
    """
    tenant_id = UUID(user.tenant_id)

    # Count by status
    total_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.tenant_id == tenant_id)
    )
    total = total_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(Alert.id)).where(
            and_(Alert.tenant_id == tenant_id, Alert.status == AlertStatus.ACTIVE.value)
        )
    )
    active = active_result.scalar() or 0

    ack_result = await db.execute(
        select(func.count(Alert.id)).where(
            and_(Alert.tenant_id == tenant_id, Alert.status == AlertStatus.ACKNOWLEDGED.value)
        )
    )
    acknowledged = ack_result.scalar() or 0

    resolved_result = await db.execute(
        select(func.count(Alert.id)).where(
            and_(Alert.tenant_id == tenant_id, Alert.status == AlertStatus.RESOLVED.value)
        )
    )
    resolved = resolved_result.scalar() or 0

    # By severity
    severity_result = await db.execute(
        select(Alert.severity, func.count(Alert.id))
        .where(Alert.tenant_id == tenant_id)
        .group_by(Alert.severity)
    )
    by_severity = {row[0]: row[1] for row in severity_result.all()}

    # By type
    type_result = await db.execute(
        select(Alert.alert_type, func.count(Alert.id))
        .where(Alert.tenant_id == tenant_id)
        .group_by(Alert.alert_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

    return AlertStats(
        total=total,
        active=active,
        acknowledged=acknowledged,
        resolved=resolved,
        by_severity=by_severity,
        by_type=by_type,
    )


@app.get("/api/v1/alerts/field/{field_id}", response_model=AlertListResponse)
async def get_field_alerts(
    field_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get alerts for a specific field.
    الحصول على تنبيهات حقل معين
    """
    query = select(Alert).where(
        and_(
            Alert.tenant_id == UUID(user.tenant_id),
            Alert.field_id == field_id,
            Alert.status == AlertStatus.ACTIVE.value,
        )
    ).order_by(Alert.severity.desc(), Alert.created_at.desc())

    count_result = await db.execute(
        select(func.count(Alert.id)).where(
            and_(
                Alert.tenant_id == UUID(user.tenant_id),
                Alert.field_id == field_id,
                Alert.status == AlertStatus.ACTIVE.value,
            )
        )
    )
    total = count_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    alerts = result.scalars().all()

    items = [
        AlertResponse(
            id=alert.id,
            tenant_id=alert.tenant_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            status=alert.status,
            title_ar=alert.title_ar,
            title_en=alert.title_en,
            message_ar=alert.message_ar,
            message_en=alert.message_en,
            field_id=alert.field_id,
            region_id=alert.region_id,
            expires_at=alert.expires_at,
            acknowledged_at=alert.acknowledged_at,
            resolved_at=alert.resolved_at,
            source=alert.source,
            created_at=alert.created_at,
            is_active=alert.is_active,
        )
        for alert in alerts
    ]

    return AlertListResponse(items=items, total=total, page=page, page_size=page_size)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
