from fastapi import APIRouter, Query
from app.services.ndvi_service import compute_ndvi_from_tif, NDVIStats

router = APIRouter(prefix="/api/v1/ndvi", tags=["ndvi"])


@router.post("/compute", response_model=NDVIStats)
def compute_ndvi(path: str = Query(..., description="Local path to GeoTIFF tile")):
    """Compute NDVI statistics for a local GeoTIFF tile."""
    return compute_ndvi_from_tif(path)
