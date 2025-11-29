from sqlalchemy.orm import Session
from app.models.satellite_image import SatelliteImage

def list_images(db: Session, tenant_id: int, field_id: int):
    return (
        db.query(SatelliteImage)
        .filter(SatelliteImage.tenant_id == tenant_id, SatelliteImage.field_id == field_id)
        .order_by(SatelliteImage.timestamp.desc())
        .all()
    )

def get_latest_ndvi(db: Session, tenant_id: int, field_id: int):
    return (
        db.query(SatelliteImage)
        .filter(
            SatelliteImage.tenant_id == tenant_id,
            SatelliteImage.field_id == field_id,
            SatelliteImage.ndvi_path.isnot(None),
        )
        .order_by(SatelliteImage.timestamp.desc())
        .first()
    )
