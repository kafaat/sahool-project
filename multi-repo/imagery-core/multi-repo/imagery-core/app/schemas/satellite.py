
from pydantic import BaseModel
from datetime import datetime

class SatelliteImageOut(BaseModel):
    id: int
    product_name: str
    timestamp: datetime
    cloudcover: float
    ndvi_path: str | None = None

    class Config:
        orm_mode = True


class SatelliteIngestRequest(BaseModel):
    tenant_id: int
    field_id: int
    external_id: str
    product_name: str
    source: str
    ingestion_ts: datetime
    cloudcover: float | None = None
    ndvi_path: str | None = None
    raw_zip: str | None = None
