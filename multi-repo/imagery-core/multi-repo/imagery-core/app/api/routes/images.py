
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.satellite import SatelliteImageOut, SatelliteIngestRequest
from app.services.imagery_service import list_images, create_image

router = APIRouter(prefix="/api/v1/imagery", tags=["imagery"])

@router.get("/list", response_model=list[SatelliteImageOut])
def list_satellite_images(
    tenant_id: int = Query(...),
    field_id: int = Query(...),
    db: Session = Depends(get_db)
):
    return list_images(db, tenant_id, field_id)


@router.post("/ingest", response_model=SatelliteImageOut)
def ingest_satellite_image(
    payload: SatelliteIngestRequest,
    db: Session = Depends(get_db),
):
    """Register a new satellite image metadata entry.

    This endpoint is called by satellite-ingestor after discovering
    scenes from external catalogues (e.g. CDSE). For now we store
    minimal metadata (scene_id/product_name/timestamp).
    """
    obj = create_image(
        db=db,
        tenant_id=payload.tenant_id,
        field_id=payload.field_id,
        scene_id=payload.external_id,
        product_name=payload.product_name,
        timestamp=payload.ingestion_ts,
        cloudcover=payload.cloudcover,
        ndvi_path=payload.ndvi_path,
        raw_zip=payload.raw_zip,
    )
    return obj
