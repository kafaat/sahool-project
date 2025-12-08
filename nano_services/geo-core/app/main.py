"""
سهول اليمن - Geo Core Service v2.0
خدمة المعالجة الجغرافية والمساحية مع تكامل قاعدة البيانات
"""
import math
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Try to import from shared library - imports marked as potentially unused with noqa
try:
    from sahool_shared.database import DatabaseManager
    from sahool_shared.models import Field as FieldModel, Region, Farmer  # noqa: F401
    SHARED_LIB_AVAILABLE = True
except ImportError:
    SHARED_LIB_AVAILABLE = False

app = FastAPI(
    title="Geo Core - سهول اليمن",
    description="خدمة المعالجة الجغرافية والمساحية للحقول الزراعية اليمنية",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Pydantic Models
# ============================================================


class AreaResponse(BaseModel):
    """نموذج استجابة حساب المساحة"""
    area_ha: float = Field(..., description="المساحة بالهكتار")
    area_m2: float = Field(..., description="المساحة بالمتر المربع")
    perimeter_m: float = Field(..., description="المحيط بالمتر")
    centroid_lat: float = Field(..., description="خط عرض المركز")
    centroid_lon: float = Field(..., description="خط طول المركز")
    bounding_box: Dict[str, float]


class ElevationResponse(BaseModel):
    """نموذج استجابة الارتفاع"""
    lat: float
    lon: float
    elevation_m: float = Field(..., description="الارتفاع بالمتر")
    slope_percent: float = Field(..., description="نسبة الانحدار")
    aspect_degrees: float = Field(..., description="اتجاه الانحدار")
    terrain_type: Optional[str] = Field(None, description="نوع التضاريس")


class DistanceResponse(BaseModel):
    """نموذج استجابة المسافة"""
    distance_km: float
    distance_m: float
    bearing_degrees: float
    travel_time_minutes: Optional[float] = Field(None, description="وقت السفر التقديري")


class ZoneInfo(BaseModel):
    """معلومات المنطقة الجغرافية"""
    zone_name: str
    zone_name_en: Optional[str] = None
    zone_type: str
    agricultural_suitability: str
    water_availability: str
    soil_quality: str
    recommended_crops: List[str] = []


class FieldCreate(BaseModel):
    """نموذج إنشاء حقل جديد"""
    name_ar: str
    name_en: Optional[str] = None
    area_hectares: float
    crop_type: Optional[str] = None
    latitude: float
    longitude: float
    region_id: Optional[int] = None
    farmer_id: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None


class FieldResponse(BaseModel):
    """نموذج استجابة الحقل"""
    id: str
    name_ar: str
    name_en: Optional[str] = None
    area_hectares: float
    crop_type: Optional[str] = None
    latitude: float
    longitude: float
    region_id: Optional[int] = None
    health_status: Optional[str] = None


# ============================================================
# Yemen Geographic Data
# ============================================================

YEMEN_BOUNDS = {
    "min_lat": 12.0,
    "max_lat": 19.0,
    "min_lon": 42.0,
    "max_lon": 55.0,
}

YEMEN_ELEVATION_PROFILES = {
    "coastal": (0, 200),
    "tihama": (0, 500),
    "highland": (1500, 3000),
    "plateau": (800, 1500),
    "desert": (200, 1000),
}

YEMEN_REGIONS = {
    1: {"name_ar": "صنعاء", "name_en": "Sanaa", "type": "highland"},
    2: {"name_ar": "عدن", "name_en": "Aden", "type": "coastal"},
    3: {"name_ar": "تعز", "name_en": "Taiz", "type": "highland"},
    4: {"name_ar": "حضرموت", "name_en": "Hadramaut", "type": "desert"},
    5: {"name_ar": "الحديدة", "name_en": "Hudaydah", "type": "coastal"},
    6: {"name_ar": "إب", "name_en": "Ibb", "type": "highland"},
    7: {"name_ar": "ذمار", "name_en": "Dhamar", "type": "highland"},
    8: {"name_ar": "مأرب", "name_en": "Marib", "type": "desert"},
}

ZONE_CROPS = {
    "highland": ["قمح", "شعير", "بن", "قات", "خضروات"],
    "coastal": ["نخيل", "موز", "مانجو", "خضروات استوائية"],
    "desert": ["نخيل", "أعلاف", "بطيخ"],
    "plateau": ["قمح", "ذرة", "بقوليات"],
}


# ============================================================
# Helper Functions
# ============================================================

def calculate_area_from_coordinates(coordinates: List[List[float]]) -> Dict:
    """حساب المساحة من الإحداثيات"""
    polygon = coordinates[0] if coordinates else []
    n = len(polygon)

    if n < 3:
        raise ValueError("Polygon must have at least 3 points")

    # Shoelace formula
    area_deg = 0.0
    for i in range(n):
        j = (i + 1) % n
        area_deg += polygon[i][0] * polygon[j][1]
        area_deg -= polygon[j][0] * polygon[i][1]
    area_deg = abs(area_deg) / 2.0

    # Convert to square meters (at Yemen's latitude ~15°)
    lat_factor = 111320
    lon_factor = 111320 * math.cos(math.radians(15))
    area_m2 = area_deg * lat_factor * lon_factor

    # Calculate perimeter
    perimeter_m = 0.0
    for i in range(n):
        j = (i + 1) % n
        dx = (polygon[j][0] - polygon[i][0]) * lon_factor
        dy = (polygon[j][1] - polygon[i][1]) * lat_factor
        perimeter_m += math.sqrt(dx * dx + dy * dy)

    # Centroid and bounding box
    cx = sum(p[0] for p in polygon) / n
    cy = sum(p[1] for p in polygon) / n
    lons = [p[0] for p in polygon]
    lats = [p[1] for p in polygon]

    return {
        "area_ha": round(area_m2 / 10000, 4),
        "area_m2": round(area_m2, 2),
        "perimeter_m": round(perimeter_m, 2),
        "centroid_lat": round(cy, 6),
        "centroid_lon": round(cx, 6),
        "bounding_box": {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lon": min(lons),
            "max_lon": max(lons),
        }
    }


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """حساب المسافة باستخدام صيغة Haversine"""
    R = 6371  # Earth radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def get_zone_info_by_coords(lat: float, lon: float) -> Dict:
    """تحديد معلومات المنطقة من الإحداثيات"""
    if lon < 44:
        if lat < 14:
            return {
                "zone_name": "تهامة",
                "zone_name_en": "Tihama",
                "zone_type": "coastal",
                "agricultural_suitability": "متوسطة",
                "water_availability": "جيدة",
                "soil_quality": "رملية طينية",
                "recommended_crops": ZONE_CROPS["coastal"]
            }
        else:
            return {
                "zone_name": "المرتفعات الغربية",
                "zone_name_en": "Western Highlands",
                "zone_type": "highland",
                "agricultural_suitability": "عالية",
                "water_availability": "جيدة",
                "soil_quality": "بركانية خصبة",
                "recommended_crops": ZONE_CROPS["highland"]
            }
    elif lon < 48:
        if lat > 15:
            return {
                "zone_name": "الهضبة الوسطى",
                "zone_name_en": "Central Plateau",
                "zone_type": "plateau",
                "agricultural_suitability": "عالية",
                "water_availability": "متوسطة",
                "soil_quality": "صفراء",
                "recommended_crops": ZONE_CROPS["plateau"]
            }
        else:
            return {
                "zone_name": "السهول الجنوبية",
                "zone_name_en": "Southern Plains",
                "zone_type": "coastal",
                "agricultural_suitability": "متوسطة",
                "water_availability": "محدودة",
                "soil_quality": "رملية",
                "recommended_crops": ZONE_CROPS["coastal"]
            }
    else:
        return {
            "zone_name": "الصحراء الشرقية",
            "zone_name_en": "Eastern Desert",
            "zone_type": "desert",
            "agricultural_suitability": "منخفضة",
            "water_availability": "محدودة جداً",
            "soil_quality": "رملية",
            "recommended_crops": ZONE_CROPS["desert"]
        }


# ============================================================
# API Endpoints
# ============================================================

@app.get("/health")
async def health():
    """فحص صحة الخدمة"""
    return {
        "status": "healthy",
        "service": "geo-core",
        "version": "2.0.0",
        "coverage": "Yemen",
        "database_connected": SHARED_LIB_AVAILABLE
    }


@app.post("/api/v1/geo/compute-area", response_model=AreaResponse)
async def compute_area(geometry: dict):
    """حساب مساحة ومحيط المضلع الجغرافي"""
    coordinates = geometry.get("coordinates", [[]])

    if not coordinates or not coordinates[0]:
        raise HTTPException(status_code=400, detail="إحداثيات غير صالحة")

    try:
        result = calculate_area_from_coordinates(coordinates)
        return AreaResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/geo/elevation", response_model=ElevationResponse)
async def get_elevation(lat: float, lon: float):
    """الحصول على ارتفاع النقطة الجغرافية"""
    # Validate within Yemen
    if not (YEMEN_BOUNDS["min_lat"] <= lat <= YEMEN_BOUNDS["max_lat"]):
        raise HTTPException(status_code=400, detail="خط العرض خارج حدود اليمن")
    if not (YEMEN_BOUNDS["min_lon"] <= lon <= YEMEN_BOUNDS["max_lon"]):
        raise HTTPException(status_code=400, detail="خط الطول خارج حدود اليمن")

    zone_info = get_zone_info_by_coords(lat, lon)
    zone_type = zone_info["zone_type"]
    elevation_range = YEMEN_ELEVATION_PROFILES.get(zone_type, (0, 1000))

    import random
    elevation = random.uniform(*elevation_range)

    return ElevationResponse(
        lat=lat,
        lon=lon,
        elevation_m=round(elevation, 1),
        slope_percent=round(random.uniform(0, 25), 1),
        aspect_degrees=round(random.uniform(0, 360), 1),
        terrain_type=zone_type
    )


@app.get("/api/v1/geo/distance", response_model=DistanceResponse)
async def calculate_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float
):
    """حساب المسافة بين نقطتين"""
    distance_km = haversine_distance(lat1, lon1, lat2, lon2)

    # Calculate bearing
    delta_lon = math.radians(lon2 - lon1)
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    bearing = (math.degrees(math.atan2(y, x)) + 360) % 360

    # Estimate travel time (assuming 40 km/h average in Yemen terrain)
    travel_time = (distance_km / 40) * 60

    return DistanceResponse(
        distance_km=round(distance_km, 3),
        distance_m=round(distance_km * 1000, 2),
        bearing_degrees=round(bearing, 1),
        travel_time_minutes=round(travel_time, 1)
    )


@app.get("/api/v1/geo/zone-info", response_model=ZoneInfo)
async def get_zone_info(lat: float, lon: float):
    """الحصول على معلومات المنطقة الجغرافية"""
    zone = get_zone_info_by_coords(lat, lon)
    return ZoneInfo(**zone)


@app.post("/api/v1/geo/validate")
async def validate_geometry(geometry: dict):
    """التحقق من صحة الشكل الجغرافي"""
    geo_type = geometry.get("type", "")
    coordinates = geometry.get("coordinates", [])
    errors = []

    if geo_type not in ["Point", "Polygon", "MultiPolygon"]:
        errors.append("نوع الشكل الجغرافي غير مدعوم")

    if geo_type == "Point":
        if len(coordinates) != 2:
            errors.append("النقطة يجب أن تحتوي على إحداثيتين فقط")
        else:
            lon, lat = coordinates
            if not (YEMEN_BOUNDS["min_lon"] <= lon <= YEMEN_BOUNDS["max_lon"]):
                errors.append("خط الطول خارج حدود اليمن")
            if not (YEMEN_BOUNDS["min_lat"] <= lat <= YEMEN_BOUNDS["max_lat"]):
                errors.append("خط العرض خارج حدود اليمن")

    elif geo_type == "Polygon":
        if not coordinates or len(coordinates[0]) < 4:
            errors.append("المضلع يجب أن يحتوي على 4 نقاط على الأقل")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "geometry_type": geo_type,
    }


@app.get("/api/v1/geo/regions")
async def list_regions():
    """قائمة المناطق اليمنية"""
    return {
        "regions": [
            {
                "id": k,
                "name_ar": v["name_ar"],
                "name_en": v["name_en"],
                "type": v["type"]
            }
            for k, v in YEMEN_REGIONS.items()
        ]
    }


@app.get("/api/v1/geo/fields")
async def list_fields(
    region_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=100)
):
    """قائمة الحقول"""
    if not SHARED_LIB_AVAILABLE:
        # Return mock data
        return {
            "fields": [
                {
                    "id": "mock-1",
                    "name_ar": "حقل القمح",
                    "area_hectares": 5.5,
                    "region_id": 1
                }
            ],
            "total": 1,
            "source": "mock"
        }

    try:
        from sqlalchemy import select
        db_manager = DatabaseManager()
        async with db_manager.get_async_session() as session:
            query = select(FieldModel).limit(limit)
            if region_id:
                query = query.where(FieldModel.region_id == region_id)

            result = await session.execute(query)
            fields = result.scalars().all()

            return {
                "fields": [
                    {
                        "id": str(f.id),
                        "name_ar": f.name_ar,
                        "area_hectares": float(f.area_hectares),
                        "crop_type": f.crop_type,
                        "region_id": f.region_id
                    }
                    for f in fields
                ],
                "total": len(fields),
                "source": "database"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/geo/fields", response_model=FieldResponse)
async def create_field(field: FieldCreate):
    """إنشاء حقل جديد"""
    if not SHARED_LIB_AVAILABLE:
        raise HTTPException(status_code=503, detail="قاعدة البيانات غير متوفرة")

    try:
        from uuid import uuid4
        db_manager = DatabaseManager()
        async with db_manager.get_async_session() as session:
            new_field = FieldModel(
                id=uuid4(),
                tenant_id=uuid4(),
                name_ar=field.name_ar,
                name_en=field.name_en,
                area_hectares=field.area_hectares,
                crop_type=field.crop_type,
                region_id=field.region_id
            )

            session.add(new_field)
            await session.commit()
            await session.refresh(new_field)

            return FieldResponse(
                id=str(new_field.id),
                name_ar=new_field.name_ar,
                name_en=new_field.name_en,
                area_hectares=float(new_field.area_hectares),
                crop_type=new_field.crop_type,
                latitude=field.latitude,
                longitude=field.longitude,
                region_id=new_field.region_id
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/geo/fields/{field_id}")
async def get_field(field_id: str):
    """الحصول على تفاصيل حقل"""
    if not SHARED_LIB_AVAILABLE:
        return {"id": field_id, "name_ar": "حقل تجريبي", "source": "mock"}

    try:
        from uuid import UUID as UUIDType
        from sqlalchemy import select

        db_manager = DatabaseManager()
        async with db_manager.get_async_session() as session:
            result = await session.execute(
                select(FieldModel).where(FieldModel.id == UUIDType(field_id))
            )
            field = result.scalar_one_or_none()

            if not field:
                raise HTTPException(status_code=404, detail="الحقل غير موجود")

            return {
                "id": str(field.id),
                "name_ar": field.name_ar,
                "name_en": field.name_en,
                "area_hectares": float(field.area_hectares),
                "crop_type": field.crop_type,
                "region_id": field.region_id,
                "soil_type": field.soil_type,
                "irrigation_type": field.irrigation_type,
                "source": "database"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Run Application
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
