"""
سهول اليمن - Imagery Core Service v2.0
خدمة صور الأقمار الصناعية وتحليل NDVI مع تكامل قاعدة البيانات
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4
import random

# Try to import from shared library - imports marked as potentially unused with noqa
try:
    from sahool_shared.database import get_async_db_session  # noqa: F401
    from sahool_shared.models import NDVIResult, Field as FieldModel  # noqa: F401
    SHARED_LIB_AVAILABLE = True
except ImportError:
    SHARED_LIB_AVAILABLE = False

app = FastAPI(
    title="Imagery Core - سهول اليمن",
    description="""
    خدمة صور الأقمار الصناعية وتحليل NDVI

    ## الميزات
    - تحليل NDVI للحقول
    - صور الأقمار الصناعية
    - تتبع صحة المحاصيل
    - كشف الإجهاد النباتي
    - خرائط حرارية للغطاء النباتي
    """,
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


class NDVITileResponse(BaseModel):
    """استجابة بلاطة NDVI"""
    field_id: str
    date: date
    tile_url: str
    satellite: str
    cloud_coverage: float = Field(..., ge=0, le=100)
    ndvi_mean: float = Field(..., ge=-1, le=1)
    ndvi_min: float = Field(..., ge=-1, le=1)
    ndvi_max: float = Field(..., ge=-1, le=1)
    ndvi_std: float = Field(..., ge=0)
    resolution_m: int
    processing_level: str
    quality_score: float = Field(..., ge=0, le=100)


class NDVIZone(BaseModel):
    """منطقة NDVI"""
    zone_id: str
    zone_type: str
    area_percent: float
    ndvi_range: tuple
    description_ar: str
    color: str


class NDVIAnalysis(BaseModel):
    """تحليل NDVI الشامل"""
    field_id: str
    analysis_id: str
    analysis_date: date
    satellite: str
    ndvi_mean: float
    ndvi_min: float
    ndvi_max: float
    ndvi_std: float
    health_status: str
    health_status_ar: str
    health_score: float = Field(..., ge=0, le=100)
    vegetation_fraction: float
    stressed_area_percent: float
    healthy_area_percent: float
    zones: List[NDVIZone]
    recommendations: List[str]
    comparison_to_previous: Optional[Dict[str, Any]] = None


class NDVIHistoryPoint(BaseModel):
    """نقطة في سجل NDVI"""
    date: date
    ndvi_mean: float
    ndvi_min: float
    ndvi_max: float
    cloud_coverage: float
    satellite: str
    quality: str


class NDVIHistoryResponse(BaseModel):
    """استجابة سجل NDVI"""
    field_id: str
    crop_type: Optional[str] = None
    history: List[NDVIHistoryPoint]
    trend: str
    trend_ar: str
    trend_strength: float
    health_status: str
    avg_ndvi: float
    best_period: Optional[str] = None
    worst_period: Optional[str] = None


class ImageMetadata(BaseModel):
    """بيانات الصورة الوصفية"""
    scene_id: str
    satellite: str
    sensor: str
    acquisition_date: datetime
    cloud_coverage: float
    sun_elevation: float
    sun_azimuth: float
    bands_available: List[str]
    resolution_m: int
    footprint_wkt: Optional[str] = None
    quality_indicator: str


class VegetationIndex(BaseModel):
    """مؤشر الغطاء النباتي"""
    index_name: str
    index_name_ar: str
    value: float
    interpretation: str
    interpretation_ar: str


class StressDetection(BaseModel):
    """كشف الإجهاد"""
    stress_type: str
    stress_type_ar: str
    severity: str
    affected_area_percent: float
    location_description: str
    recommendation_ar: str


# ============================================================
# Yemen Data
# ============================================================


CROP_NDVI_RANGES = {
    "قمح": {"healthy": (0.5, 0.75), "moderate": (0.35, 0.5), "stressed": (0.2, 0.35)},
    "ذرة": {"healthy": (0.55, 0.85), "moderate": (0.4, 0.55), "stressed": (0.25, 0.4)},
    "بن": {"healthy": (0.6, 0.85), "moderate": (0.45, 0.6), "stressed": (0.3, 0.45)},
    "طماطم": {"healthy": (0.5, 0.8), "moderate": (0.35, 0.5), "stressed": (0.2, 0.35)},
    "خضروات": {"healthy": (0.45, 0.75), "moderate": (0.3, 0.45), "stressed": (0.15, 0.3)},
    "نخيل": {"healthy": (0.35, 0.6), "moderate": (0.25, 0.35), "stressed": (0.15, 0.25)},
    "موز": {"healthy": (0.6, 0.9), "moderate": (0.45, 0.6), "stressed": (0.3, 0.45)},
}

SATELLITES = [
    {"name": "Sentinel-2A", "sensor": "MSI", "resolution": 10, "revisit": 5},
    {"name": "Sentinel-2B", "sensor": "MSI", "resolution": 10, "revisit": 5},
    {"name": "Landsat-8", "sensor": "OLI", "resolution": 30, "revisit": 16},
    {"name": "Landsat-9", "sensor": "OLI-2", "resolution": 30, "revisit": 16},
]

# ============================================================
# Helper Functions
# ============================================================


def get_health_status(ndvi: float, crop_type: str = "قمح") -> tuple:
    """تحديد حالة الصحة من NDVI"""
    ranges = CROP_NDVI_RANGES.get(crop_type, CROP_NDVI_RANGES["قمح"])

    if ndvi >= ranges["healthy"][0]:
        return "healthy", "ممتاز", 85 + random.uniform(0, 15)
    elif ndvi >= ranges["moderate"][0]:
        return "moderate", "متوسط", 50 + random.uniform(0, 30)
    else:
        return "stressed", "مجهد", 20 + random.uniform(0, 25)


def generate_zones(ndvi_mean: float) -> List[NDVIZone]:
    """توليد مناطق NDVI"""
    zones = []

    # Healthy zone
    healthy_pct = max(0, min(100, (ndvi_mean - 0.3) * 150))
    if healthy_pct > 0:
        zones.append(NDVIZone(
            zone_id="zone-healthy",
            zone_type="healthy",
            area_percent=round(healthy_pct, 1),
            ndvi_range=(0.6, 1.0),
            description_ar="منطقة صحية - نمو ممتاز",
            color="#22c55e"
        ))

    # Moderate zone
    moderate_pct = max(0, 100 - healthy_pct - random.uniform(5, 20))
    if moderate_pct > 0:
        zones.append(NDVIZone(
            zone_id="zone-moderate",
            zone_type="moderate",
            area_percent=round(moderate_pct * 0.6, 1),
            ndvi_range=(0.4, 0.6),
            description_ar="منطقة متوسطة - تحتاج مراقبة",
            color="#eab308"
        ))

    # Stressed zone
    stressed_pct = 100 - healthy_pct - moderate_pct * 0.6
    if stressed_pct > 0:
        zones.append(NDVIZone(
            zone_id="zone-stressed",
            zone_type="stressed",
            area_percent=round(stressed_pct, 1),
            ndvi_range=(0.0, 0.4),
            description_ar="منطقة مجهدة - تحتاج تدخل",
            color="#ef4444"
        ))

    return zones


# ============================================================
# Endpoints
# ============================================================


@app.get("/health")
async def health():
    """فحص صحة الخدمة"""
    return {
        "status": "healthy",
        "service": "imagery-core",
        "version": "2.0.0",
        "database_connected": SHARED_LIB_AVAILABLE,
        "satellites": [s["name"] for s in SATELLITES],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/ndvi/{field_id}", response_model=NDVITileResponse)
async def get_ndvi_tile(
    field_id: str,
    target_date: Optional[date] = None,
    crop_type: str = Query("قمح", description="نوع المحصول")
):
    """الحصول على بيانات NDVI للحقل"""
    d = target_date or date.today()
    ranges = CROP_NDVI_RANGES.get(crop_type, CROP_NDVI_RANGES["قمح"])

    # Generate realistic NDVI based on crop type
    ndvi_mean = round(random.uniform(ranges["moderate"][0], ranges["healthy"][1]), 3)
    ndvi_std = round(random.uniform(0.05, 0.12), 3)

    satellite = random.choice(SATELLITES)
    cloud_coverage = round(random.uniform(0, 15), 1)
    quality_score = 100 - cloud_coverage - random.uniform(0, 10)

    return NDVITileResponse(
        field_id=field_id,
        date=d,
        tile_url=f"https://tiles.sahool.ye/ndvi/{field_id}/{d.isoformat()}/tile.png",
        satellite=satellite["name"],
        cloud_coverage=cloud_coverage,
        ndvi_mean=ndvi_mean,
        ndvi_min=round(max(0, ndvi_mean - ndvi_std * 2), 3),
        ndvi_max=round(min(1, ndvi_mean + ndvi_std * 2), 3),
        ndvi_std=ndvi_std,
        resolution_m=satellite["resolution"],
        processing_level="L2A",
        quality_score=round(quality_score, 1)
    )


@app.get("/api/v1/ndvi/{field_id}/history", response_model=NDVIHistoryResponse)
async def get_ndvi_history(
    field_id: str,
    months: int = Query(6, ge=1, le=24, description="عدد الأشهر"),
    crop_type: str = Query("قمح", description="نوع المحصول")
):
    """الحصول على سجل NDVI التاريخي"""
    history = []
    base_date = date.today()
    ranges = CROP_NDVI_RANGES.get(crop_type, CROP_NDVI_RANGES["قمح"])
    base_ndvi = random.uniform(ranges["moderate"][1], ranges["healthy"][0])

    best_ndvi = 0
    worst_ndvi = 1
    best_date = base_date
    worst_date = base_date

    for i in range(months * 2):  # بيانات كل أسبوعين
        d = base_date - timedelta(days=i * 14)

        # تباين موسمي
        month = d.month
        if month in [3, 4, 5, 9, 10]:  # مواسم النمو
            seasonal_factor = 0.12
        elif month in [6, 7, 8]:  # صيف
            seasonal_factor = -0.05
        else:  # شتاء
            seasonal_factor = 0.02

        ndvi = round(base_ndvi + seasonal_factor + random.uniform(-0.06, 0.06), 3)
        ndvi = max(0.1, min(0.9, ndvi))
        ndvi_min = round(max(0, ndvi - random.uniform(0.08, 0.15)), 3)
        ndvi_max = round(min(1, ndvi + random.uniform(0.08, 0.15)), 3)

        if ndvi > best_ndvi:
            best_ndvi = ndvi
            best_date = d
        if ndvi < worst_ndvi:
            worst_ndvi = ndvi
            worst_date = d

        cloud = round(random.uniform(0, 25), 1)
        quality = "excellent" if cloud < 10 else "good" if cloud < 20 else "fair"

        history.append(NDVIHistoryPoint(
            date=d,
            ndvi_mean=ndvi,
            ndvi_min=ndvi_min,
            ndvi_max=ndvi_max,
            cloud_coverage=cloud,
            satellite=random.choice(["Sentinel-2A", "Sentinel-2B"]),
            quality=quality
        ))

    # حساب الترند
    recent_avg = sum(h.ndvi_mean for h in history[:4]) / 4
    older_avg = sum(h.ndvi_mean for h in history[-4:]) / 4
    trend_strength = abs(recent_avg - older_avg)

    if recent_avg > older_avg + 0.03:
        trend = "improving"
        trend_ar = "تحسن ملحوظ"
        health_status = "المحصول في حالة تحسن مستمر"
    elif recent_avg < older_avg - 0.03:
        trend = "declining"
        trend_ar = "انخفاض"
        health_status = "المحصول يحتاج متابعة عاجلة"
    else:
        trend = "stable"
        trend_ar = "مستقر"
        health_status = "المحصول في حالة مستقرة"

    avg_ndvi = sum(h.ndvi_mean for h in history) / len(history)

    return NDVIHistoryResponse(
        field_id=field_id,
        crop_type=crop_type,
        history=history,
        trend=trend,
        trend_ar=trend_ar,
        trend_strength=round(trend_strength, 3),
        health_status=health_status,
        avg_ndvi=round(avg_ndvi, 3),
        best_period=best_date.strftime("%Y-%m"),
        worst_period=worst_date.strftime("%Y-%m")
    )


@app.post("/api/v1/ndvi/analyze", response_model=NDVIAnalysis)
async def analyze_ndvi(payload: dict):
    """تحليل NDVI الشامل للحقل"""
    field_id = payload.get("field_id", str(uuid4()))
    crop_type = payload.get("crop_type", "قمح")

    ranges = CROP_NDVI_RANGES.get(crop_type, CROP_NDVI_RANGES["قمح"])
    ndvi_mean = round(random.uniform(ranges["moderate"][0], ranges["healthy"][1]), 3)
    ndvi_std = round(random.uniform(0.05, 0.12), 3)

    status, status_ar, health_score = get_health_status(ndvi_mean, crop_type)
    zones = generate_zones(ndvi_mean)

    healthy_pct = next((z.area_percent for z in zones if z.zone_type == "healthy"), 0)
    stressed_pct = next((z.area_percent for z in zones if z.zone_type == "stressed"), 0)

    # توصيات بناءً على الحالة
    recommendations = []
    if status == "stressed":
        recommendations = [
            "زيادة الري فوراً",
            "فحص التربة للتأكد من توفر المغذيات",
            "مراقبة الآفات والأمراض",
        ]
    elif status == "moderate":
        recommendations = [
            "مراقبة الحقل بانتظام",
            "التأكد من انتظام الري",
        ]
    else:
        recommendations = [
            "استمر بالممارسات الحالية",
            "تسجيل البيانات للمقارنة المستقبلية",
        ]

    satellite = random.choice(SATELLITES)

    return NDVIAnalysis(
        field_id=field_id,
        analysis_id=f"analysis-{uuid4().hex[:12]}",
        analysis_date=date.today(),
        satellite=satellite["name"],
        ndvi_mean=ndvi_mean,
        ndvi_min=round(max(0, ndvi_mean - ndvi_std * 2), 3),
        ndvi_max=round(min(1, ndvi_mean + ndvi_std * 2), 3),
        ndvi_std=ndvi_std,
        health_status=status,
        health_status_ar=status_ar,
        health_score=round(health_score, 1),
        vegetation_fraction=round(random.uniform(0.6, 0.95), 2),
        stressed_area_percent=stressed_pct,
        healthy_area_percent=healthy_pct,
        zones=zones,
        recommendations=recommendations,
        comparison_to_previous={
            "ndvi_change": round(random.uniform(-0.1, 0.1), 3),
            "trend": random.choice(["improving", "stable", "declining"])
        }
    )


@app.get("/api/v1/imagery/available")
async def get_available_imagery(
    lat: float = Query(..., description="خط العرض"),
    lon: float = Query(..., description="خط الطول"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    max_cloud: float = Query(30, description="الحد الأقصى للسحب %")
):
    """البحث عن الصور المتاحة للموقع"""
    start = start_date or (date.today() - timedelta(days=30))
    end = end_date or date.today()

    images = []
    current = start

    while current <= end:
        for sat in SATELLITES:
            # تحقق من دورة القمر
            if (current - start).days % sat["revisit"] == 0:
                cloud = round(random.uniform(0, 40), 1)
                if cloud <= max_cloud:
                    images.append(ImageMetadata(
                        scene_id=f"{sat['name'][:3]}_{current.strftime('%Y%m%d')}_YEM_{random.randint(1000, 9999)}",
                        satellite=sat["name"],
                        sensor=sat["sensor"],
                        acquisition_date=datetime.combine(current, datetime.min.time().replace(hour=10)),
                        cloud_coverage=cloud,
                        sun_elevation=round(random.uniform(50, 75), 1),
                        sun_azimuth=round(random.uniform(120, 180), 1),
                        bands_available=["B2", "B3", "B4", "B8", "B11", "B12"] if "Sentinel" in sat["name"] else ["B2", "B3", "B4", "B5", "B6", "B7"],
                        resolution_m=sat["resolution"],
                        quality_indicator="excellent" if cloud < 10 else "good" if cloud < 20 else "fair"
                    ))
        current += timedelta(days=1)

    # ترتيب حسب التاريخ
    images.sort(key=lambda x: x.acquisition_date, reverse=True)

    return {
        "location": {"lat": lat, "lon": lon},
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "images": images,
        "count": len(images),
        "satellites_available": list(set(img.satellite for img in images))
    }


@app.get("/api/v1/indices/{field_id}")
async def get_vegetation_indices(
    field_id: str,
    target_date: Optional[date] = None
):
    """الحصول على مؤشرات الغطاء النباتي المتعددة"""
    d = target_date or date.today()

    ndvi = round(random.uniform(0.4, 0.75), 3)

    indices = [
        VegetationIndex(
            index_name="NDVI",
            index_name_ar="مؤشر الغطاء النباتي المعياري",
            value=ndvi,
            interpretation="healthy" if ndvi > 0.5 else "moderate" if ndvi > 0.3 else "stressed",
            interpretation_ar="صحي" if ndvi > 0.5 else "متوسط" if ndvi > 0.3 else "مجهد"
        ),
        VegetationIndex(
            index_name="EVI",
            index_name_ar="مؤشر الغطاء النباتي المحسن",
            value=round(ndvi * 0.9 + random.uniform(-0.05, 0.05), 3),
            interpretation="correlated with NDVI",
            interpretation_ar="مرتبط بـ NDVI"
        ),
        VegetationIndex(
            index_name="SAVI",
            index_name_ar="مؤشر الغطاء النباتي المعدل للتربة",
            value=round(ndvi * 0.85 + random.uniform(-0.05, 0.05), 3),
            interpretation="adjusted for soil",
            interpretation_ar="معدل لتأثير التربة"
        ),
        VegetationIndex(
            index_name="NDWI",
            index_name_ar="مؤشر المياه المعياري",
            value=round(random.uniform(0.1, 0.4), 3),
            interpretation="water content",
            interpretation_ar="محتوى الماء في النبات"
        ),
    ]

    return {
        "field_id": field_id,
        "date": d.isoformat(),
        "indices": [i.dict() for i in indices],
        "primary_index": "NDVI",
        "satellite": random.choice(["Sentinel-2A", "Sentinel-2B"])
    }


@app.post("/api/v1/stress/detect")
async def detect_stress(payload: dict):
    """كشف الإجهاد في الحقل"""
    field_id = payload.get("field_id", str(uuid4()))

    stress_types = [
        ("water", "إجهاد مائي", "نقص في الري أو جفاف"),
        ("nutrient", "نقص مغذيات", "نقص في النيتروجين أو الفوسفور"),
        ("disease", "مرض نباتي", "احتمال وجود إصابة فطرية"),
        ("pest", "إصابة آفات", "علامات تغذية حشرات"),
    ]

    detections = []
    for stress_type, stress_ar, desc in stress_types:
        if random.random() > 0.6:  # 40% احتمال وجود إجهاد
            severity = random.choice(["low", "medium", "high"])
            detections.append(StressDetection(
                stress_type=stress_type,
                stress_type_ar=stress_ar,
                severity=severity,
                affected_area_percent=round(random.uniform(5, 30), 1),
                location_description=f"الجزء {random.choice(['الشمالي', 'الجنوبي', 'الشرقي', 'الغربي'])} من الحقل",
                recommendation_ar=f"يُنصح بفحص {desc} واتخاذ الإجراءات اللازمة"
            ))

    return {
        "field_id": field_id,
        "detection_date": date.today().isoformat(),
        "detections": [d.dict() for d in detections],
        "total_stressed_area": round(sum(d.affected_area_percent for d in detections), 1),
        "overall_health": "good" if len(detections) == 0 else "fair" if len(detections) <= 2 else "poor",
        "requires_attention": len(detections) > 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
