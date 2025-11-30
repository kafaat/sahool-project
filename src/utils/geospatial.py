"""
Geospatial Utilities - Sahool Agricultural Platform
Advanced geospatial operations for field management
Includes area calculation, polygon operations, coordinate transformations
"""

import math
from typing import List, Tuple, Optional, Dict, Any
from shapely.geometry import Point, Polygon, MultiPolygon, shape, mapping
from shapely.ops import transform, unary_union
from pyproj import Transformer, CRS
import geojson
import logging

logger = logging.getLogger(__name__)


class CoordinateSystem:
    """Coordinate system transformations"""
    
    @staticmethod
    def wgs84_to_utm(lon: float, lat: float) -> Tuple[int, float, float]:
        """
        Convert WGS84 (lat/lon) to UTM coordinates
        
        Args:
            lon: Longitude in degrees
            lat: Latitude in degrees
        
        Returns:
            Tuple of (utm_zone, easting, northing)
        """
        # Calculate UTM zone
        utm_zone = int((lon + 180) / 6) + 1
        
        # Create transformer
        utm_crs = CRS.from_epsg(32600 + utm_zone if lat >= 0 else 32700 + utm_zone)
        wgs84_crs = CRS.from_epsg(4326)
        
        transformer = Transformer.from_crs(wgs84_crs, utm_crs, always_xy=True)
        easting, northing = transformer.transform(lon, lat)
        
        return (utm_zone, easting, northing)
    
    @staticmethod
    def utm_to_wgs84(zone: int, easting: float, northing: float, northern: bool = True) -> Tuple[float, float]:
        """
        Convert UTM to WGS84 (lat/lon)
        
        Args:
            zone: UTM zone number
            easting: Easting coordinate
            northing: Northing coordinate
            northern: True for northern hemisphere
        
        Returns:
            Tuple of (longitude, latitude)
        """
        epsg_code = 32600 + zone if northern else 32700 + zone
        utm_crs = CRS.from_epsg(epsg_code)
        wgs84_crs = CRS.from_epsg(4326)
        
        transformer = Transformer.from_crs(utm_crs, wgs84_crs, always_xy=True)
        lon, lat = transformer.transform(easting, northing)
        
        return (lon, lat)
    
    @staticmethod
    def transform_geometry(geom: Any, from_epsg: int, to_epsg: int) -> Any:
        """Transform geometry between coordinate systems"""
        from_crs = CRS.from_epsg(from_epsg)
        to_crs = CRS.from_epsg(to_epsg)
        
        transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
        
        return transform(transformer.transform, geom)


class FieldGeometry:
    """Field geometry operations"""
    
    @staticmethod
    def calculate_area(coordinates: List[Tuple[float, float]], unit: str = "hectares") -> float:
        """
        Calculate area of a polygon
        
        Args:
            coordinates: List of (lon, lat) tuples
            unit: Output unit (hectares, acres, sqm)
        
        Returns:
            Area in specified unit
        """
        # Create polygon
        polygon = Polygon(coordinates)
        
        # Transform to UTM for accurate area calculation
        centroid = polygon.centroid
        utm_zone = int((centroid.x + 180) / 6) + 1
        utm_epsg = 32600 + utm_zone if centroid.y >= 0 else 32700 + utm_zone
        
        polygon_utm = CoordinateSystem.transform_geometry(polygon, 4326, utm_epsg)
        
        # Calculate area in square meters
        area_sqm = polygon_utm.area
        
        # Convert to requested unit
        if unit == "hectares":
            return area_sqm / 10000
        elif unit == "acres":
            return area_sqm / 4046.86
        elif unit == "sqm":
            return area_sqm
        else:
            raise ValueError(f"Unknown unit: {unit}")
    
    @staticmethod
    def calculate_perimeter(coordinates: List[Tuple[float, float]], unit: str = "meters") -> float:
        """Calculate perimeter of a polygon"""
        polygon = Polygon(coordinates)
        
        # Transform to UTM
        centroid = polygon.centroid
        utm_zone = int((centroid.x + 180) / 6) + 1
        utm_epsg = 32600 + utm_zone if centroid.y >= 0 else 32700 + utm_zone
        
        polygon_utm = CoordinateSystem.transform_geometry(polygon, 4326, utm_epsg)
        
        perimeter_m = polygon_utm.length
        
        if unit == "meters":
            return perimeter_m
        elif unit == "kilometers":
            return perimeter_m / 1000
        elif unit == "feet":
            return perimeter_m * 3.28084
        else:
            raise ValueError(f"Unknown unit: {unit}")
    
    @staticmethod
    def get_centroid(coordinates: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Get centroid of polygon"""
        polygon = Polygon(coordinates)
        centroid = polygon.centroid
        return (centroid.x, centroid.y)
    
    @staticmethod
    def get_bounding_box(coordinates: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
        """Get bounding box (minx, miny, maxx, maxy)"""
        polygon = Polygon(coordinates)
        return polygon.bounds
    
    @staticmethod
    def simplify_polygon(
        coordinates: List[Tuple[float, float]],
        tolerance: float = 0.0001
    ) -> List[Tuple[float, float]]:
        """Simplify polygon by removing unnecessary points"""
        polygon = Polygon(coordinates)
        simplified = polygon.simplify(tolerance, preserve_topology=True)
        return list(simplified.exterior.coords)
    
    @staticmethod
    def buffer_polygon(
        coordinates: List[Tuple[float, float]],
        distance: float,
        unit: str = "meters"
    ) -> List[Tuple[float, float]]:
        """
        Create buffer around polygon
        
        Args:
            coordinates: Polygon coordinates
            distance: Buffer distance
            unit: Distance unit (meters, feet)
        
        Returns:
            Buffered polygon coordinates
        """
        polygon = Polygon(coordinates)
        
        # Transform to UTM
        centroid = polygon.centroid
        utm_zone = int((centroid.x + 180) / 6) + 1
        utm_epsg = 32600 + utm_zone if centroid.y >= 0 else 32700 + utm_zone
        
        polygon_utm = CoordinateSystem.transform_geometry(polygon, 4326, utm_epsg)
        
        # Convert distance to meters
        if unit == "feet":
            distance = distance * 0.3048
        elif unit != "meters":
            raise ValueError(f"Unknown unit: {unit}")
        
        # Buffer
        buffered_utm = polygon_utm.buffer(distance)
        
        # Transform back to WGS84
        buffered = CoordinateSystem.transform_geometry(buffered_utm, utm_epsg, 4326)
        
        return list(buffered.exterior.coords)
    
    @staticmethod
    def intersects(
        coords1: List[Tuple[float, float]],
        coords2: List[Tuple[float, float]]
    ) -> bool:
        """Check if two polygons intersect"""
        poly1 = Polygon(coords1)
        poly2 = Polygon(coords2)
        return poly1.intersects(poly2)
    
    @staticmethod
    def intersection_area(
        coords1: List[Tuple[float, float]],
        coords2: List[Tuple[float, float]],
        unit: str = "hectares"
    ) -> float:
        """Calculate intersection area between two polygons"""
        poly1 = Polygon(coords1)
        poly2 = Polygon(coords2)
        
        intersection = poly1.intersection(poly2)
        
        if intersection.is_empty:
            return 0.0
        
        # Transform to UTM
        centroid = intersection.centroid
        utm_zone = int((centroid.x + 180) / 6) + 1
        utm_epsg = 32600 + utm_zone if centroid.y >= 0 else 32700 + utm_zone
        
        intersection_utm = CoordinateSystem.transform_geometry(intersection, 4326, utm_epsg)
        
        area_sqm = intersection_utm.area
        
        if unit == "hectares":
            return area_sqm / 10000
        elif unit == "acres":
            return area_sqm / 4046.86
        else:
            return area_sqm
    
    @staticmethod
    def point_in_polygon(point: Tuple[float, float], coordinates: List[Tuple[float, float]]) -> bool:
        """Check if point is inside polygon"""
        pt = Point(point)
        poly = Polygon(coordinates)
        return poly.contains(pt)


class GeoJSONUtils:
    """GeoJSON utilities"""
    
    @staticmethod
    def create_feature(
        geometry: Dict[str, Any],
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create GeoJSON feature"""
        return {
            "type": "Feature",
            "geometry": geometry,
            "properties": properties or {}
        }
    
    @staticmethod
    def create_polygon_feature(
        coordinates: List[Tuple[float, float]],
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create polygon GeoJSON feature"""
        geometry = {
            "type": "Polygon",
            "coordinates": [coordinates]
        }
        return GeoJSONUtils.create_feature(geometry, properties)
    
    @staticmethod
    def create_feature_collection(features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create GeoJSON feature collection"""
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    @staticmethod
    def validate_geojson(data: Dict[str, Any]) -> bool:
        """Validate GeoJSON"""
        try:
            geojson.loads(geojson.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Invalid GeoJSON: {e}")
            return False
    
    @staticmethod
    def extract_coordinates(feature: Dict[str, Any]) -> List[Tuple[float, float]]:
        """Extract coordinates from GeoJSON feature"""
        geom = shape(feature["geometry"])
        if isinstance(geom, Polygon):
            return list(geom.exterior.coords)
        else:
            raise ValueError("Only Polygon geometries supported")


class DistanceCalculator:
    """Distance calculation utilities"""
    
    @staticmethod
    def haversine_distance(
        point1: Tuple[float, float],
        point2: Tuple[float, float],
        unit: str = "meters"
    ) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Args:
            point1: (lon, lat) of first point
            point2: (lon, lat) of second point
            unit: Output unit (meters, kilometers, miles)
        
        Returns:
            Distance in specified unit
        """
        lon1, lat1 = point1
        lon2, lat2 = point2
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in meters
        r = 6371000
        
        distance_m = c * r
        
        if unit == "meters":
            return distance_m
        elif unit == "kilometers":
            return distance_m / 1000
        elif unit == "miles":
            return distance_m / 1609.34
        else:
            raise ValueError(f"Unknown unit: {unit}")


__all__ = [
    "CoordinateSystem",
    "FieldGeometry",
    "GeoJSONUtils",
    "DistanceCalculator"
]
