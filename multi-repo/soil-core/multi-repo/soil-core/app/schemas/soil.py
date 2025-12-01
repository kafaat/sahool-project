from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional


class SoilSampleBase(BaseModel):
    sample_date: date
    depth_cm: Optional[int] = None
    ph: Optional[float] = None
    ec_ds_m: Optional[float] = None
    moisture_pct: Optional[float] = None
    organic_matter_pct: Optional[float] = None
    lab_ref: Optional[str] = None
    notes: Optional[str] = None


class SoilSampleCreate(SoilSampleBase):
    tenant_id: int
    field_id: int


class SoilSampleOut(SoilSampleBase):
    id: int
    tenant_id: int
    field_id: int

    model_config = ConfigDict(from_attributes=True)

class SoilFieldSummary(BaseModel):
    field_id: int
    tenant_id: int
    samples_count: int
    ph_avg: Optional[float] = None
    ec_avg: Optional[float] = None
    moisture_avg: Optional[float] = None
    organic_matter_avg: Optional[float] = None