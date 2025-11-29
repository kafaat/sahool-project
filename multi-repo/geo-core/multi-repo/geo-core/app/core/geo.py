from typing import Tuple
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer


def geojson_area_ha(geojson: dict) -> float:
    """Approximate area in hectares for a GeoJSON polygon in EPSG:4326.

    We reproject to EPSG:3857 (meters) then compute area.
    """
    geom = shape(geojson)
    if geom.is_empty:
        return 0.0
    transformer = Transformer.from_crs(4326, 3857, always_xy=True)
    projected = transform(transformer.transform, geom)
    return projected.area / 10_000.0  # m² -> ha


def geojson_centroid_latlon(geojson: dict) -> Tuple[float, float]:
    geom = shape(geojson)
    c = geom.centroid
    return (float(c.y), float(c.x))


def normalize_polygon_geojson(geojson: dict) -> dict:
    """Return a cleaned polygon GeoJSON (useful for storage / validation)."""
    geom = shape(geojson)
    if geom.geom_type != "Polygon" and geom.geom_type != "MultiPolygon":
        raise ValueError("Geometry must be Polygon or MultiPolygon")
    return mapping(geom)