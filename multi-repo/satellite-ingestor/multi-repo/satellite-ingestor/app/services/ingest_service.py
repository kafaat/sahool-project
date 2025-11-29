from datetime import datetime, timedelta
from typing import List

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.services.cdse_client import CDSEClient, CDSEProduct


class IngestResult(BaseModel):
    field_id: int
    products_count: int
    products: list[str]


async def _get_field_aoi_wkt(field_id: int, tenant_id: int) -> str:
    """Fetch field geometry from geo-core via gateway-edge and build WKT.

    For now we fallback to a POINT WKT using centroid_lat/centroid_lon.
    """
    url = f"{settings.GATEWAY_URL}/api/geo/fields/{field_id}"
    params = {"tenant_id": tenant_id}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    lat = data.get("centroid_lat")
    lon = data.get("centroid_lon")
    if lat is None or lon is None:
        raise ValueError("Field centroid is missing; cannot build AOI WKT.")
    return f"POINT({lon} {lat})"


async def ingest_field_sentinel2(
    field_id: int,
    tenant_id: int,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 10,
) -> IngestResult:
    if date_to is None:
        date_to = datetime.utcnow()
    if date_from is None:
        date_from = date_to - timedelta(days=7)

    aoi = await _get_field_aoi_wkt(field_id, tenant_id)

    client = CDSEClient(
        base_url=settings.CDSE_BASE_URL,
        username=settings.CDSE_USER,
        password=settings.CDSE_PASS,
    )
    products: List[CDSEProduct] = await client.search_sentinel2(
        aoi_wkt=aoi,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )

    notified: list[str] = []
    async with httpx.AsyncClient(timeout=20.0) as client:
        for prod in products:
            payload = {
                "tenant_id": tenant_id,
                "field_id": field_id,
                "external_id": prod.id,
                "product_name": prod.name,
                "source": "CDSE",
                "ingestion_ts": prod.ingestion_date.isoformat(),
            }
            try:
                resp = await client.post(
                    f"{settings.GATEWAY_URL}/api/imagery/api/v1/imagery/ingest",
                    json=payload,
                )
                if resp.status_code < 300:
                    notified.append(prod.id)
            except Exception:
                continue

    return IngestResult(
        field_id=field_id,
        products_count=len(products),
        products=notified,
    )
