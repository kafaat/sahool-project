from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.db.base import Base


class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=False)

    name = Column(String(255), nullable=False)
    crop = Column(String(255), nullable=True)

    area_ha = Column(Float, nullable=True)

    centroid_lat = Column(Float, nullable=True)
    centroid_lon = Column(Float, nullable=True)

    # PostGIS geometry column (Polygon / MultiPolygon) in EPSG:4326
    geometry = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True))