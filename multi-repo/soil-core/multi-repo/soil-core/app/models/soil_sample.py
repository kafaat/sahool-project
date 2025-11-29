from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey
from app.db.base import Base

class SoilSample(Base):
    __tablename__ = "soil_samples"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    field_id = Column(Integer, index=True, nullable=False)

    sample_date = Column(Date, nullable=False)

    depth_cm = Column(Integer, nullable=True)
    ph = Column(Float, nullable=True)
    ec_ds_m = Column(Float, nullable=True)  # Electrical conductivity (dS/m)
    moisture_pct = Column(Float, nullable=True)
    organic_matter_pct = Column(Float, nullable=True)

    lab_ref = Column(String(128), nullable=True)
    notes = Column(String(512), nullable=True)