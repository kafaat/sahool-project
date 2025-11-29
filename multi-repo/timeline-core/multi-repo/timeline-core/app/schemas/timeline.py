from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class FieldTimelinePoint(BaseModel):
    timestamp: datetime
    ndvi: Optional[float] = None
    eto: Optional[float] = None
    rain_mm: Optional[float] = None

class FieldTimelineResponse(BaseModel):
    tenant_id: int
    field_id: int
    timeline: List[FieldTimelinePoint]
