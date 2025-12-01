from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class AlertBase(BaseModel):
    category: str
    severity: str
    title: str
    message: str
    field_id: Optional[int] = None


class AlertCreate(AlertBase):
    tenant_id: int


class AlertOut(AlertBase):
    id: int
    tenant_id: int
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)