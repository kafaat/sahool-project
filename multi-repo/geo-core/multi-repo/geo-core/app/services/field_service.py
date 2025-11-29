from typing import List, Optional

from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.geo import geojson_area_ha, geojson_centroid_latlon, normalize_polygon_geojson
from app.core.config import get_settings

settings = get_settings()


def list_fields(db: Session, tenant_id: int) -> List[models.Field]:
    return (
        db.query(models.Field)
        .filter(models.Field.tenant_id == tenant_id)
        .order_by(models.Field.id.desc())
        .all()
    )


def get_field(db: Session, tenant_id: int, field_id: int) -> Optional[models.Field]:
    f = (
        db.query(models.Field)
        .filter(models.Field.tenant_id == tenant_id, models.Field.id == field_id)
        .first()
    )
    if not f:
        return None
    return _enrich_field_output(f)


def create_field(db: Session, field_in: schemas.FieldCreate) -> models.Field:
    # normalize geometry and compute area/centroid
    norm_geojson = normalize_polygon_geojson(field_in.geometry)
    area_ha = geojson_area_ha(norm_geojson)
    lat, lon = geojson_centroid_latlon(norm_geojson)

    geom_shape = shape(norm_geojson)
    geom = from_shape(geom_shape, srid=settings.SRID)

    field = models.Field(
        tenant_id=field_in.tenant_id,
        name=field_in.name,
        crop=field_in.crop,
        area_ha=area_ha,
        centroid_lat=lat,
        centroid_lon=lon,
        geometry=geom,
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


def update_field(db: Session, tenant_id: int, field_id: int, field_in: schemas.FieldUpdate) -> Optional[models.Field]:
    field = get_field(db, tenant_id, field_id)
    if not field:
        return None

    if field_in.name is not None:
        field.name = field_in.name
    if field_in.crop is not None:
        field.crop = field_in.crop
    if field_in.geometry is not None:
        norm_geojson = normalize_polygon_geojson(field_in.geometry)
        area_ha = geojson_area_ha(norm_geojson)
        lat, lon = geojson_centroid_latlon(norm_geojson)
        from geoalchemy2.shape import from_shape
        from shapely.geometry import shape
        geom_shape = shape(norm_geojson)
        field.geometry = from_shape(geom_shape, srid=settings.SRID)
        field.area_ha = area_ha
        field.centroid_lat = lat
        field.centroid_lon = lon

    db.add(field)
    db.commit()
    db.refresh(field)
    return field


def delete_field(db: Session, tenant_id: int, field_id: int) -> bool:
    q = db.query(models.Field).filter(models.Field.tenant_id == tenant_id, models.Field.id == field_id)
    if not q.first():
        return False
    q.delete()
    db.commit()
    return True
def _enrich_field_output(field: models.Field) -> models.Field:
    """Attach derived properties (bbox, centroid_geojson) on the fly.

    NOTE: These are not persisted columns; they are added dynamically for the
    API response models that expose them in FieldOut.
    """
    if not hasattr(field, "bbox"):
        # Simple bbox: [min_lon, min_lat, max_lon, max_lat]
        # For now, approximate using centroid + area if geometry is missing in ORM,
        # but if geometry is loaded, you can compute real bbox via shapely.
        try:
            from geoalchemy2.shape import to_shape

            if field.geometry is not None:
                geom = to_shape(field.geometry)
                minx, miny, maxx, maxy = geom.bounds
                field.bbox = [float(minx), float(miny), float(maxx), float(maxy)]
            else:
                field.bbox = None
        except Exception:
            field.bbox = None

    if not hasattr(field, "centroid_geojson"):
        if field.centroid_lat is not None and field.centroid_lon is not None:
            field.centroid_geojson = {
                "type": "Point",
                "coordinates": [field.centroid_lon, field.centroid_lat],
            }
        else:
            field.centroid_geojson = None

    return field
