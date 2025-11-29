from datetime import datetime
from fastapi import APIRouter, Query
from app.services.ingest_service import ingest_field_sentinel2, IngestResult

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


@router.post("/field/{field_id}", response_model=IngestResult)
async def ingest_field(
    field_id: int,
    tenant_id: int = Query(...),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    """Trigger Sentinel-2 ingestion for a specific field + tenant.

    This will:
    - fetch the AOI (centroid) from geo-core via gateway-edge
    - search Sentinel-2 scenes from CDSE
    - notify imagery-core for each product (metadata only for now)
    """
    return await ingest_field_sentinel2(
        field_id=field_id,
        tenant_id=tenant_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
