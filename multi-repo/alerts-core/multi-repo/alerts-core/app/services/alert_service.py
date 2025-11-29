from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.schemas.alert import AlertCreate

def create_alert(db: Session, alert_in: AlertCreate) -> Alert:
    alert = Alert(
        tenant_id=alert_in.tenant_id,
        field_id=alert_in.field_id,
        category=alert_in.category,
        severity=alert_in.severity,
        title=alert_in.title,
        message=alert_in.message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def list_recent_alerts(db: Session, tenant_id: int, hours: int = 72) -> List[Alert]:
    since = datetime.utcnow() - timedelta(hours=hours)
    return (
        db.query(Alert)
        .filter(Alert.tenant_id == tenant_id, Alert.created_at >= since)
        .order_by(Alert.created_at.desc())
        .all()
    )

def list_field_alerts(db: Session, tenant_id: int, field_id: int) -> List[Alert]:
    return (
        db.query(Alert)
        .filter(Alert.tenant_id == tenant_id, Alert.field_id == field_id)
        .order_by(Alert.created_at.desc())
        .all()
    )

def mark_alert_read(db: Session, tenant_id: int, alert_id: int) -> Optional[Alert]:
    alert = (
        db.query(Alert)
        .filter(Alert.tenant_id == tenant_id, Alert.id == alert_id)
        .first()
    )
    if not alert:
        return None
    alert.is_read = True
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert