"""
سهول اليمن - Geo Core Service
خدمة المعالجة الجغرافية والمساحية
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import math

app = FastAPI(
    title="Geo Core - سهول اليمن",
    description="خدمة المعالجة الجغرافية والمساحية للحقول الزراعية اليمنية",
    version="1.0.0"
)

class AreaResponse(BaseModel):
    area_ha: float
    area_m2: float
    perimeter_m: float
    centroid_lat: float
    centroid_lon: float
    bounding_box: Dict[str, float]

class ElevationResponse(BaseModel):
    lat: float
    lon: float
    elevation_m: float
    slope_percent: float
    aspect_degrees: float

class DistanceResponse(BaseModel):
    distance_km: float
    distance_m: float
    bearing_degrees: float

class ZoneInfo(BaseModel):
    zone_name: str
    zone_type: str
    agricultural_suitability: str
    water_availability: str
    soil_quality: str

# Yemen geographic boundaries
YEMEN_BOUNDS = {
    "min_lat": 12.0,
    "max_lat": 19.0,
    "min_lon": 42.0,
    "max_lon": 55.0,
}

# Elevation profiles for different Yemen regions
YEMEN_ELEVATION_PROFILES = {
    "coastal": (0, 200),
    "tihama": (0, 500),
    "highland": (1500, 3000),
    "plateau": (800, 1500),
    "desert": (200, 1000),
}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "geo-core", "coverage": "Yemen"}

@app.post("/api/v1/geo/compute-area", response_model=AreaResponse)
async def compute_area(geometry: dict):
    """حساب مساحة ومحيط المضلع الجغرافي"""
    coordinates = geometry.get("coordinates", [[]])

    if not coordinates or not coordinates[0]:
        raise HTTPException(status_code=400, detail="Invalid geometry")

    # Simplified area calculation (for demo purposes)
    # In production, use proper geodesic calculations
    polygon = coordinates[0]
    n = len(polygon)

    if n < 3:
        raise HTTPException(status_code=400, detail="Polygon must have at least 3 points")

    # Shoelace formula approximation
    area_deg = 0.0
    for i in range(n):
        j = (i + 1) % n
        area_deg += polygon[i][0] * polygon[j][1]
        area_deg -= polygon[j][0] * polygon[i][1]
    area_deg = abs(area_deg) / 2.0

    # Convert to square meters (approximate at Yemen's latitude)
    lat_factor = 111320  # meters per degree at equator
    lon_factor = 111320 * math.cos(math.radians(15))  # Yemen average lat ~15°
    area_m2 = area_deg * lat_factor * lon_factor

    # Calculate perimeter
    perimeter_m = 0.0
    for i in range(n):
        j = (i + 1) % n
        dx = (polygon[j][0] - polygon[i][0]) * lon_factor
        dy = (polygon[j][1] - polygon[i][1]) * lat_factor
        perimeter_m += math.sqrt(dx*dx + dy*dy)

    # Calculate centroid
    cx = sum(p[0] for p in polygon) / n
    cy = sum(p[1] for p in polygon) / n

    # Bounding box
    lons = [p[0] for p in polygon]
    lats = [p[1] for p in polygon]

    return AreaResponse(
        area_ha=round(area_m2 / 10000, 4),
        area_m2=round(area_m2, 2),
        perimeter_m=round(perimeter_m, 2),
        centroid_lat=round(cy, 6),
        centroid_lon=round(cx, 6),
        bounding_box={
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lon": min(lons),
            "max_lon": max(lons),
        }
    )

@app.get("/api/v1/geo/elevation", response_model=ElevationResponse)
async def get_elevation(lat: float, lon: float):
    """الحصول على ارتفاع النقطة الجغرافية"""
    # Validate within Yemen
    if not (YEMEN_BOUNDS["min_lat"] <= lat <= YEMEN_BOUNDS["max_lat"]):
        raise HTTPException(status_code=400, detail="Latitude outside Yemen bounds")
    if not (YEMEN_BOUNDS["min_lon"] <= lon <= YEMEN_BOUNDS["max_lon"]):
        raise HTTPException(status_code=400, detail="Longitude outside Yemen bounds")

    # Determine region type based on coordinates (simplified)
    if lon < 44:
        region = "coastal" if lat < 15 else "highland"
    elif lon < 48:
        region = "highland" if lat > 14 else "plateau"
    else:
        region = "desert"

    elevation_range = YEMEN_ELEVATION_PROFILES[region]
    import random
    elevation = random.uniform(*elevation_range)

    return ElevationResponse(
        lat=lat,
        lon=lon,
        elevation_m=round(elevation, 1),
        slope_percent=round(random.uniform(0, 25), 1),
        aspect_degrees=round(random.uniform(0, 360), 1),
    )

@app.get("/api/v1/geo/distance", response_model=DistanceResponse)
async def calculate_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float
):
    """حساب المسافة بين نقطتين"""
    # Haversine formula
    R = 6371  # Earth radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance_km = R * c

    # Calculate bearing
    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    bearing = math.degrees(math.atan2(y, x))
    bearing = (bearing + 360) % 360

    return DistanceResponse(
        distance_km=round(distance_km, 3),
        distance_m=round(distance_km * 1000, 2),
        bearing_degrees=round(bearing, 1),
    )

@app.get("/api/v1/geo/zone-info", response_model=ZoneInfo)
async def get_zone_info(lat: float, lon: float):
    """الحصول على معلومات المنطقة الجغرافية"""
    # Simplified zone determination
    if lon < 44:
        if lat < 14:
            zone = ("تهامة", "coastal", "متوسطة", "جيدة", "رملية طينية")
        else:
            zone = ("المرتفعات الغربية", "highland", "عالية", "جيدة", "بركانية خصبة")
    elif lon < 48:
        if lat > 15:
            zone = ("الهضبة الوسطى", "plateau", "عالية", "متوسطة", "صفراء")
        else:
            zone = ("الجنوب", "coastal", "متوسطة", "محدودة", "رملية")
    else:
        zone = ("الشرق", "desert", "منخفضة", "محدودة جداً", "رملية")

    return ZoneInfo(
        zone_name=zone[0],
        zone_type=zone[1],
        agricultural_suitability=zone[2],
        water_availability=zone[3],
        soil_quality=zone[4],
    )

@app.post("/api/v1/geo/validate")
async def validate_geometry(geometry: dict):
    """التحقق من صحة الشكل الجغرافي"""
    geo_type = geometry.get("type", "")
    coordinates = geometry.get("coordinates", [])

    errors = []

    if geo_type not in ["Point", "Polygon", "MultiPolygon"]:
        errors.append("Unsupported geometry type")

    if geo_type == "Point":
        if len(coordinates) != 2:
            errors.append("Point must have exactly 2 coordinates")
        else:
            lon, lat = coordinates
            if not (YEMEN_BOUNDS["min_lon"] <= lon <= YEMEN_BOUNDS["max_lon"]):
                errors.append("Longitude outside Yemen bounds")
            if not (YEMEN_BOUNDS["min_lat"] <= lat <= YEMEN_BOUNDS["max_lat"]):
                errors.append("Latitude outside Yemen bounds")

    elif geo_type == "Polygon":
        if not coordinates or len(coordinates[0]) < 4:
            errors.append("Polygon must have at least 4 points (including closing point)")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "geometry_type": geo_type,
    }
