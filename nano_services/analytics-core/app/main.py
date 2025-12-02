"""
سهول اليمن - Analytics Core Service
خدمة التحليلات والإحصاءات الزراعية
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List, Dict, Any
import random

app = FastAPI(
    title="Analytics Core - سهول اليمن",
    description="خدمة التحليلات والإحصاءات للقطاع الزراعي اليمني",
    version="1.0.0"
)

class NDVITimelinePoint(BaseModel):
    date: date
    mean_ndvi: float
    min_ndvi: float
    max_ndvi: float
    std_ndvi: float

class NDVITimelineResponse(BaseModel):
    field_id: int
    data: List[NDVITimelinePoint]
    trend_direction: str
    trend_strength: float

class YieldPrediction(BaseModel):
    field_id: int
    crop_type: str
    predicted_yield_kg_ha: float
    confidence_low: float
    confidence_high: float
    confidence_percent: float
    factors: Dict[str, str]

class SeasonalAnalysis(BaseModel):
    season: str
    season_ar: str
    start_month: int
    end_month: int
    recommended_crops: List[str]
    water_needs: str
    expected_challenges: List[str]

class RegionStats(BaseModel):
    region_id: int
    region_name_ar: str
    total_fields: int
    total_area_ha: float
    avg_ndvi: float
    active_crops: List[str]
    alerts_count: int

# Yemen agricultural seasons
YEMEN_SEASONS = {
    "صيف": {"months": [6, 7, 8], "crops": ["ذرة", "سمسم", "خضروات صيفية"]},
    "خريف": {"months": [9, 10, 11], "crops": ["قمح", "شعير", "بقوليات"]},
    "شتاء": {"months": [12, 1, 2], "crops": ["قمح", "شعير", "خضروات شتوية"]},
    "ربيع": {"months": [3, 4, 5], "crops": ["طماطم", "بصل", "بطاطس"]},
}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "analytics-core"}

@app.get("/api/v1/ndvi/{field_id}/timeline", response_model=NDVITimelineResponse)
async def get_ndvi_timeline(field_id: int, months: int = 6):
    """الحصول على سلسلة NDVI الزمنية"""
    from datetime import timedelta

    base_date = date.today()
    data = []
    base_ndvi = random.uniform(0.35, 0.55)

    for i in range(months * 4):  # Weekly data
        d = base_date - timedelta(days=i * 7)
        # Add seasonal variation
        month = d.month
        seasonal_boost = 0.1 if month in [3, 4, 5, 9, 10] else -0.05

        mean_val = base_ndvi + seasonal_boost + random.uniform(-0.03, 0.03)
        mean_val = max(0.1, min(0.9, mean_val))

        data.append(NDVITimelinePoint(
            date=d,
            mean_ndvi=round(mean_val, 3),
            min_ndvi=round(mean_val - random.uniform(0.05, 0.15), 3),
            max_ndvi=round(mean_val + random.uniform(0.05, 0.15), 3),
            std_ndvi=round(random.uniform(0.02, 0.08), 3),
        ))

    # Calculate trend
    recent = sum(d.mean_ndvi for d in data[:4]) / 4
    older = sum(d.mean_ndvi for d in data[-4:]) / 4
    trend_strength = abs(recent - older)

    if recent > older + 0.02:
        trend_direction = "ascending"
    elif recent < older - 0.02:
        trend_direction = "descending"
    else:
        trend_direction = "stable"

    return NDVITimelineResponse(
        field_id=field_id,
        data=data,
        trend_direction=trend_direction,
        trend_strength=round(trend_strength, 3),
    )

@app.get("/api/v1/analytics/yield-prediction", response_model=YieldPrediction)
async def predict_yield(field_id: int, crop_type: str = "قمح"):
    """التنبؤ بالإنتاج الزراعي"""
    # Yemen average yields by crop (kg/ha)
    base_yields = {
        "قمح": 2200,
        "ذرة": 3500,
        "شعير": 1800,
        "طماطم": 25000,
        "بصل": 18000,
        "بطاطس": 20000,
        "بن": 800,
    }

    base = base_yields.get(crop_type, 2000)
    variation = base * 0.2
    predicted = base + random.uniform(-variation, variation)

    confidence = random.uniform(70, 90)
    margin = predicted * (100 - confidence) / 100

    factors = {}
    if random.random() > 0.5:
        factors["water"] = "مستوى الري مناسب"
    else:
        factors["water"] = "يحتاج زيادة في الري"

    if random.random() > 0.5:
        factors["soil"] = "التربة بحالة جيدة"
    else:
        factors["soil"] = "يُنصح بتحسين التربة"

    factors["ndvi"] = f"مؤشر NDVI: {round(random.uniform(0.4, 0.7), 2)}"

    return YieldPrediction(
        field_id=field_id,
        crop_type=crop_type,
        predicted_yield_kg_ha=round(predicted, 0),
        confidence_low=round(predicted - margin, 0),
        confidence_high=round(predicted + margin, 0),
        confidence_percent=round(confidence, 1),
        factors=factors,
    )

@app.get("/api/v1/analytics/seasonal", response_model=List[SeasonalAnalysis])
async def get_seasonal_analysis(region_id: Optional[int] = None):
    """تحليل المواسم الزراعية"""
    analyses = []

    season_names = {
        "صيف": "Summer",
        "خريف": "Autumn",
        "شتاء": "Winter",
        "ربيع": "Spring",
    }

    challenges = {
        "صيف": ["ارتفاع درجات الحرارة", "نقص المياه", "الآفات الحشرية"],
        "خريف": ["أمطار غزيرة محتملة", "فطريات", "انجراف التربة"],
        "شتاء": ["برودة الليل", "صقيع محتمل", "ندرة الأمطار"],
        "ربيع": ["تقلب الطقس", "رياح قوية", "آفات موسمية"],
    }

    water_needs = {
        "صيف": "عالية جداً",
        "خريف": "متوسطة",
        "شتاء": "منخفضة",
        "ربيع": "متوسطة إلى عالية",
    }

    for season_ar, info in YEMEN_SEASONS.items():
        analyses.append(SeasonalAnalysis(
            season=season_names[season_ar].lower(),
            season_ar=season_ar,
            start_month=info["months"][0],
            end_month=info["months"][-1],
            recommended_crops=info["crops"],
            water_needs=water_needs[season_ar],
            expected_challenges=challenges[season_ar],
        ))

    return analyses

@app.get("/api/v1/analytics/region-stats", response_model=RegionStats)
async def get_region_stats(region_id: int):
    """إحصاءات المنطقة الزراعية"""
    region_names = {
        1: "صنعاء", 2: "عدن", 3: "تعز", 4: "حضرموت", 5: "الحديدة",
        6: "إب", 7: "ذمار", 8: "شبوة", 9: "لحج", 10: "أبين",
        11: "مأرب", 12: "الجوف", 13: "عمران", 14: "حجة", 15: "المحويت",
        16: "ريمة", 17: "المهرة", 18: "سقطرى", 19: "البيضاء", 20: "صعدة",
    }

    return RegionStats(
        region_id=region_id,
        region_name_ar=region_names.get(region_id, f"منطقة {region_id}"),
        total_fields=random.randint(100, 5000),
        total_area_ha=round(random.uniform(500, 50000), 2),
        avg_ndvi=round(random.uniform(0.35, 0.65), 3),
        active_crops=random.sample(["قمح", "ذرة", "خضروات", "بن", "أعلاف"], k=3),
        alerts_count=random.randint(0, 15),
    )

@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_stats():
    """إحصاءات لوحة التحكم"""
    return {
        "total_fields": random.randint(10000, 50000),
        "total_farmers": random.randint(5000, 20000),
        "total_area_ha": round(random.uniform(100000, 500000), 0),
        "active_regions": 20,
        "avg_ndvi_national": round(random.uniform(0.4, 0.55), 3),
        "alerts_today": random.randint(5, 50),
        "crop_distribution": {
            "قمح": 35,
            "ذرة": 25,
            "خضروات": 20,
            "بن": 10,
            "أخرى": 10,
        },
        "last_updated": datetime.utcnow().isoformat(),
    }
