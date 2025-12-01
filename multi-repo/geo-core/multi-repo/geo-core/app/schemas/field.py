from pydantic import BaseModel, ConfigDict, Field as PydanticField
from typing import Optional, Any


class FieldBase(BaseModel):
    name: str
    crop: Optional[str] = None


class FieldCreate(FieldBase):
    tenant_id: int
    geometry: dict = PydanticField(..., description="Polygon/MultiPolygon GeoJSON in EPSG:4326")


class FieldUpdate(BaseModel):
    name: Optional[str] = None
    crop: Optional[str] = None
    geometry: Optional[dict] = None


class FieldOut(FieldBase):
    id: int
    tenant_id: int
    area_ha: Optional[float] = None
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    bbox: Optional[list[float]] = None
    centroid_geojson: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)