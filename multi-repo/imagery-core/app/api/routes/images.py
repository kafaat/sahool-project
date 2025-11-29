from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.satellite import SatelliteImageOut
from app.services.imagery_service import list_images, get_latest_ndvi

router = APIRouter(prefix="/api/v1/imagery", tags=["imagery"])

@router.get("/list", response_model=List[SatelliteImageOut])
def list_satellite_images(
    tenant_id: int = Query(...),
    field_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return list_images(db, tenant_id, field_id)

@router.get("/fields/{field_id}/ndvi-latest", response_model=SatelliteImageOut)
def latest_ndvi(
    field_id: int,
    tenant_id: int = Query(...),
    db: Session = Depends(get_db),
):
    img = get_latest_ndvi(db, tenant_id, field_id)
    if not img:
        raise HTTPException(status_code=404, detail="No NDVI available")
    return img
