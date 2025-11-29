from datetime import datetime
from typing import List, Optional

import httpx
from pydantic import BaseModel


class CDSEProduct(BaseModel):
    id: str
    name: str
    ingestion_date: datetime
    footprint: Optional[str] = None


class CDSEClient:
    """Minimal Copernicus Data Space Ecosystem client (OData-based search)."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password

    async def search_sentinel2(
        self,
        aoi_wkt: str,
        date_from: datetime,
        date_to: datetime,
        limit: int = 10,
    ) -> List[CDSEProduct]:
        """Search Sentinel-2 L2A scenes for an AOI + date range.

        NOTE: This is a baseline implementation following CDSE OData style.
        It may need adaptation to the final catalogue endpoint/filters used
        in production.
        """
        url = f"{self.base_url}/odata/v1/Products"

        filter_expr = (
            "Collection/Name eq 'SENTINEL-2' and "
            "OData.CSC.Intersects(area=geography'SRID=4326;{aoi}', footprint=Footprint) and "
            "ContentDate/Start ge {start} and ContentDate/Start le {end}"
        ).format(
            aoi=aoi_wkt,
            start=date_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
            end=date_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        params = {
            "$top": limit,
            "$filter": filter_expr,
            "$orderby": "ContentDate/Start desc",
        }

        async with httpx.AsyncClient(timeout=30.0, auth=(self.username, self.password)) as client:
            resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        values = data.get("value") or []
        products: list[CDSEProduct] = []
        for item in values:
            products.append(
                CDSEProduct(
                    id=item.get("Id") or item.get("id"),
                    name=item.get("Name") or item.get("name"),
                    ingestion_date=item.get("ContentDate", {}).get("Start") or datetime.utcnow(),
                    footprint=item.get("Footprint"),
                )
            )
        return products
