from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Any


class SatelliteImageOut(BaseModel):
    id: int
    product_name: str
    timestamp: datetime
    cloudcover: float
    ndvi_preview_png: Optional[str] = None
    image_bounds: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)
