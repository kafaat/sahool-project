"""
Alerts Service - خدمة التنبيهات
Sahool Yemen Platform v9.0.0

Manages agricultural alerts and notifications.
"""

import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, "/app/libs-shared")

try:
    from sahool_shared.schemas.common import HealthResponse
    from sahool_shared.utils import setup_logging, get_logger
except ImportError:
    # Fallback for standalone operation
    from pydantic import BaseModel as HealthResponse
    import logging
    def setup_logging(service_name: str): pass
    def get_logger(name: str): return logging.getLogger(name)

logger = get_logger(__name__)


# ============================================================
# Models
# ============================================================

class Alert(BaseModel):
    """Alert model."""
    id: str
    type: str = Field(..., description="Alert type: weather, pest, irrigation, etc.")
    severity: str = Field(..., description="Severity: low, medium, high, critical")
    title: str
    message: str
    field_id: Optional[str] = None
    created_at: str
    acknowledged: bool = False


class AlertCreate(BaseModel):
    """Create alert request."""
    type: str
    severity: str
    title: str
    message: str
    field_id: Optional[str] = None


class AlertResponse(BaseModel):
    """Alert response."""
    success: bool
    alert: Optional[Alert] = None
    message: Optional[str] = None


class AlertListResponse(BaseModel):
    """Alert list response."""
    success: bool
    alerts: List[Alert]
    total: int


# ============================================================
# Application Setup
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging(service_name="alerts-service")
    logger.info("alerts_service_starting", version="9.0.0")
    yield
    logger.info("alerts_service_stopping")


app = FastAPI(
    title="Sahool Alerts Service",
    description="خدمة التنبيهات الزراعية - Agricultural Alerts Service",
    version="9.0.0",
    lifespan=lifespan,
)

# CORS Configuration
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=bool(CORS_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
async def health_check():
    """Service health check."""
    return {"status": "healthy", "service": "alerts-service", "version": "9.0.0"}


# ============================================================
# Alert Endpoints
# ============================================================

@app.get("/api/v1/alerts", response_model=AlertListResponse)
async def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    type: Optional[str] = Query(None, description="Filter by type"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List alerts with optional filters.
    عرض التنبيهات مع فلاتر اختيارية
    """
    # TODO: Implement database query
    logger.info("list_alerts", severity=severity, type=type, limit=limit)
    return AlertListResponse(success=True, alerts=[], total=0)


@app.post("/api/v1/alerts", response_model=AlertResponse)
async def create_alert(alert: AlertCreate):
    """
    Create a new alert.
    إنشاء تنبيه جديد
    """
    logger.info("create_alert", type=alert.type, severity=alert.severity)
    # TODO: Implement alert creation
    return AlertResponse(success=True, message="Alert creation not yet implemented")


@app.get("/api/v1/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str):
    """
    Get alert by ID.
    الحصول على تنبيه بالمعرف
    """
    logger.info("get_alert", alert_id=alert_id)
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Alert not found")


@app.patch("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """
    Acknowledge an alert.
    تأكيد استلام التنبيه
    """
    logger.info("acknowledge_alert", alert_id=alert_id)
    # TODO: Implement acknowledgement
    return {"success": True, "message": "Alert acknowledged"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
