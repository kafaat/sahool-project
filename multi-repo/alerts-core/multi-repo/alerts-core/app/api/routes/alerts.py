from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.alert import AlertCreate, AlertOut
from app.services.alert_service import (
    create_alert,
    list_recent_alerts,
    list_field_alerts,
    mark_alert_read,
)

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])

@router.post("", response_model=AlertOut, status_code=201)
def create_alert_endpoint(
    alert_in: AlertCreate,
    db: Session = Depends(get_db),
):
    return create_alert(db, alert_in)

@router.get("/recent", response_model=List[AlertOut])
def list_recent_alerts_endpoint(
    tenant_id: int = Query(...),
    hours: int = Query(72, ge=1, le=720),
    db: Session = Depends(get_db),
):
    return list_recent_alerts(db, tenant_id, hours=hours)

@router.get("/field/{field_id}", response_model=List[AlertOut])
def list_field_alerts_endpoint(
    field_id: int,
    tenant_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return list_field_alerts(db, tenant_id, field_id)

@router.post("/{alert_id}/read", response_model=AlertOut)
def mark_read_endpoint(
    alert_id: int,
    tenant_id: int = Query(...),
    db: Session = Depends(get_db),
):
    alert = mark_alert_read(db, tenant_id, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert