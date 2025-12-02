from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from db import Base

class FieldModel(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    geometry_type = Column(String, nullable=False)
    geom_wkt = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)

    zones = relationship("FieldZoneModel", back_populates="field")


class FieldZoneModel(Base):
    __tablename__ = "field_zones"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    level = Column(Integer, nullable=False)
    min_ndvi = Column(Float, nullable=False)
    max_ndvi = Column(Float, nullable=False)
    geom_wkt = Column(Text, nullable=False)

    field = relationship("FieldModel", back_populates="zones")
