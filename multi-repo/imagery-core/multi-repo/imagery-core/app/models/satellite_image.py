
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.base import Base

class SatelliteImage(Base):
    __tablename__ = "satellite_images"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True)
    field_id = Column(Integer, index=True)
    scene_id = Column(String, index=True)
    product_name = Column(String)
    timestamp = Column(DateTime)
    cloudcover = Column(Float)
    ndvi_path = Column(String)
    raw_zip = Column(String)
