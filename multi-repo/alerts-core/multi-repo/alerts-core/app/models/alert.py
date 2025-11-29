from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.base import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    field_id = Column(Integer, index=True, nullable=True)

    category = Column(String(64), nullable=False)   # ndvi, soil, weather, irrigation, ...
    severity = Column(String(32), nullable=False)   # low, medium, high, critical

    title = Column(String(255), nullable=False)
    message = Column(String(1024), nullable=False)

    is_read = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)