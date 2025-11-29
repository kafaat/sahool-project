
from sqlalchemy.orm import Session
from app.models.satellite_image import SatelliteImage

def list_images(db: Session, tenant_id: int, field_id: int):
    return (
        db.query(SatelliteImage)
        .filter(SatelliteImage.tenant_id == tenant_id, SatelliteImage.field_id == field_id)
        .all()
    )


def create_image(
    db: Session,
    tenant_id: int,
    field_id: int,
    scene_id: str,
    product_name: str,
    timestamp,
    cloudcover: float | None = None,
    ndvi_path: str | None = None,
    raw_zip: str | None = None,
):
    obj = SatelliteImage(
        tenant_id=tenant_id,
        field_id=field_id,
        scene_id=scene_id,
        product_name=product_name,
        timestamp=timestamp,
        cloudcover=cloudcover or 0.0,
        ndvi_path=ndvi_path or "",
        raw_zip=raw_zip or "",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
