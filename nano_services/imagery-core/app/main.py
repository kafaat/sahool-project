"""
سهول اليمن - Imagery Core Service
خدمة صور الأقمار الصناعية وتحليل NDVI
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List
import random

app = FastAPI(
    title="Imagery Core - سهول اليمن",
    description="خدمة صور الأقمار الصناعية وتحليل NDVI للحقول الزراعية اليمنية",
    version="1.0.0"
)

class NDVITileResponse(BaseModel):
    field_id: int
    date: date
    tile_url: str
    satellite: str
    cloud_coverage: float
    ndvi_mean: float
    ndvi_min: float
    ndvi_max: float
    resolution_m: int
    processing_level: str

class NDVIHistoryPoint(BaseModel):
    date: date
    ndvi_mean: float
    cloud_coverage: float
    satellite: str

class NDVIHistoryResponse(BaseModel):
    field_id: int
    history: List[NDVIHistoryPoint]
    trend: str
    health_status: str

class ImageMetadata(BaseModel):
    scene_id: str
    satellite: str
    acquisition_date: datetime
    cloud_coverage: float
    sun_elevation: float
    bands_available: List[str]

# Yemen NDVI typical ranges by crop type
CROP_NDVI_RANGES = {
    "قمح": (0.3, 0.7),
    "ذرة": (0.4, 0.8),
    "بن": (0.5, 0.85),
    "خضروات": (0.35, 0.75),
    "نخيل": (0.25, 0.6),
    "أعلاف": (0.3, 0.65),
}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "imagery-core", "satellites": ["Sentinel-2", "Landsat-8"]}

@app.get("/api/v1/ndvi/{field_id}", response_model=NDVITileResponse)
async def get_ndvi_tile(
    field_id: int,
    target_date: Optional[date] = None,
    crop_type: str = "قمح"
):
    """الحصول على بيانات NDVI للحقل"""
    d = target_date or date.today()
    ndvi_range = CROP_NDVI_RANGES.get(crop_type, (0.3, 0.7))
    ndvi_mean = round(random.uniform(*ndvi_range), 3)

    return NDVITileResponse(
        field_id=field_id,
        date=d,
        tile_url=f"https://tiles.sahool.yemen/ndvi/{field_id}/{d.isoformat()}/tile.png",
        satellite=random.choice(["Sentinel-2A", "Sentinel-2B", "Landsat-8"]),
        cloud_coverage=round(random.uniform(0, 15), 1),
        ndvi_mean=ndvi_mean,
        ndvi_min=round(ndvi_mean - 0.1, 3),
        ndvi_max=round(ndvi_mean + 0.1, 3),
        resolution_m=10,
        processing_level="L2A",
    )

@app.get("/api/v1/ndvi/{field_id}/history", response_model=NDVIHistoryResponse)
async def get_ndvi_history(field_id: int, months: int = 6):
    """الحصول على سجل NDVI التاريخي"""
    from datetime import timedelta

    history = []
    base_date = date.today()
    base_ndvi = random.uniform(0.4, 0.6)

    for i in range(months * 2):  # Bi-weekly data
        d = base_date - timedelta(days=i * 14)
        # Simulate seasonal variation
        seasonal_factor = 0.1 * (1 if (d.month in [3, 4, 5, 9, 10, 11]) else -0.5)
        ndvi = round(base_ndvi + seasonal_factor + random.uniform(-0.05, 0.05), 3)
        ndvi = max(0.1, min(0.9, ndvi))

        history.append(NDVIHistoryPoint(
            date=d,
            ndvi_mean=ndvi,
            cloud_coverage=round(random.uniform(0, 20), 1),
            satellite=random.choice(["Sentinel-2A", "Sentinel-2B"]),
        ))

    # Determine trend
    recent_avg = sum(h.ndvi_mean for h in history[:4]) / 4
    older_avg = sum(h.ndvi_mean for h in history[-4:]) / 4

    if recent_avg > older_avg + 0.05:
        trend = "improving"
        health_status = "جيد - المحصول في تحسن"
    elif recent_avg < older_avg - 0.05:
        trend = "declining"
        health_status = "تحذير - يحتاج متابعة"
    else:
        trend = "stable"
        health_status = "مستقر - المحصول بحالة طبيعية"

    return NDVIHistoryResponse(
        field_id=field_id,
        history=history,
        trend=trend,
        health_status=health_status,
    )

@app.get("/api/v1/imagery/available")
async def get_available_imagery(
    lat: float,
    lon: float,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """البحث عن الصور المتاحة للموقع"""
    from datetime import timedelta

    start = start_date or (date.today() - timedelta(days=30))
    end = end_date or date.today()

    images = []
    current = start
    while current <= end:
        if random.random() > 0.3:  # ~70% availability
            images.append(ImageMetadata(
                scene_id=f"S2A_{current.strftime('%Y%m%d')}_YEM_{random.randint(1000, 9999)}",
                satellite=random.choice(["Sentinel-2A", "Sentinel-2B"]),
                acquisition_date=datetime.combine(current, datetime.min.time()),
                cloud_coverage=round(random.uniform(0, 30), 1),
                sun_elevation=round(random.uniform(45, 75), 1),
                bands_available=["B2", "B3", "B4", "B8", "B11", "B12"],
            ))
        current += timedelta(days=5)

    return {"images": images, "count": len(images)}

@app.post("/api/v1/ndvi/analyze")
async def analyze_ndvi(payload: dict):
    """تحليل صورة NDVI"""
    field_id = payload.get("field_id", 0)
    geometry = payload.get("geometry", {})

    return {
        "field_id": field_id,
        "analysis_id": f"analysis-{datetime.utcnow().timestamp()}",
        "status": "completed",
        "results": {
            "ndvi_mean": round(random.uniform(0.4, 0.7), 3),
            "ndvi_std": round(random.uniform(0.05, 0.15), 3),
            "vegetation_fraction": round(random.uniform(0.5, 0.9), 2),
            "stressed_area_percent": round(random.uniform(0, 20), 1),
            "healthy_area_percent": round(random.uniform(60, 95), 1),
        }
    }
