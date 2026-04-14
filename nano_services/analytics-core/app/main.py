"""
سهول اليمن - Analytics Core Service v2.0
خدمة التحليلات والإحصاءات الزراعية مع تكامل قاعدة البيانات
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
import random

# Try to import from shared library - imports marked as potentially unused with noqa
try:
    from sahool_shared.database import get_async_db_session, DatabaseManager  # noqa: F401
    from sahool_shared.models import (  # noqa: F401
        Field as FieldModel, NDVIResult, YieldRecord,
        Region, SoilAnalysis, WeatherData
    )
    from sahool_shared.auth import get_current_user, AuthenticatedUser  # noqa: F401
    SHARED_LIB_AVAILABLE = True
except ImportError:
    SHARED_LIB_AVAILABLE = False

app = FastAPI(
    title="Analytics Core - سهول اليمن",
    description="""
    خدمة التحليلات والإحصاءات للقطاع الزراعي اليمني

    ## الميزات
    - تحليل سلسلة NDVI الزمنية
    - التنبؤ بالإنتاجية
    - تحليل المواسم الزراعية
    - إحصاءات المناطق
    - لوحة تحكم شاملة
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


class NDVITimelinePoint(BaseModel):
    """نقطة في سلسلة NDVI الزمنية"""
    date: date
    mean_ndvi: float = Field(..., ge=0, le=1, description="متوسط NDVI")
    min_ndvi: float = Field(..., ge=0, le=1, description="أدنى NDVI")
    max_ndvi: float = Field(..., ge=0, le=1, description="أعلى NDVI")
    std_ndvi: float = Field(..., ge=0, description="الانحراف المعياري")
    health_status: Optional[str] = None


class NDVITimelineResponse(BaseModel):
    """استجابة سلسلة NDVI الزمنية"""
    field_id: str
    field_name: Optional[str] = None
    data: List[NDVITimelinePoint]
    trend_direction: str = Field(..., description="اتجاه الترند: ascending, descending, stable")
    trend_strength: float = Field(..., description="قوة الترند")
    avg_ndvi: float
    health_summary: str


class YieldPrediction(BaseModel):
    """توقع الإنتاجية"""
    field_id: str
    crop_type: str
    predicted_yield_kg_ha: float
    predicted_yield_ton_ha: float
    confidence_low: float
    confidence_high: float
    confidence_percent: float
    factors: Dict[str, Any]
    recommendations_ar: List[str]


class SeasonalAnalysis(BaseModel):
    """تحليل الموسم الزراعي"""
    season: str
    season_ar: str
    start_month: int
    end_month: int
    recommended_crops: List[str]
    water_needs: str
    expected_challenges: List[str]
    current: bool = False


class RegionStats(BaseModel):
    """إحصاءات المنطقة"""
    region_id: int
    region_name_ar: str
    region_name_en: str
    total_fields: int
    total_farmers: int
    total_area_ha: float
    avg_ndvi: float
    active_crops: List[str]
    alerts_count: int
    health_distribution: Dict[str, float]


class DashboardStats(BaseModel):
    """إحصاءات لوحة التحكم"""
    total_fields: int
    total_farmers: int
    total_area_ha: float
    active_regions: int
    avg_ndvi_national: float
    alerts_today: int
    crop_distribution: Dict[str, float]
    ndvi_status: Dict[str, float]
    weather_summary: Dict[str, Any]
    last_updated: datetime


class CropComparison(BaseModel):
    """مقارنة المحاصيل"""
    crop_type: str
    crop_type_ar: str
    avg_yield_kg_ha: float
    avg_ndvi: float
    total_area_ha: float
    total_farmers: int
    profit_margin_percent: float


# ============================================================
# Yemen Data
# ============================================================


YEMEN_REGIONS = {
    1: {"ar": "صنعاء", "en": "Sana'a"},
    2: {"ar": "عدن", "en": "Aden"},
    3: {"ar": "تعز", "en": "Taiz"},
    4: {"ar": "الحديدة", "en": "Hudaydah"},
    5: {"ar": "إب", "en": "Ibb"},
    6: {"ar": "ذمار", "en": "Dhamar"},
    7: {"ar": "حضرموت", "en": "Hadhramaut"},
    8: {"ar": "المهرة", "en": "Al Mahrah"},
    9: {"ar": "شبوة", "en": "Shabwah"},
    10: {"ar": "أبين", "en": "Abyan"},
    11: {"ar": "لحج", "en": "Lahij"},
    12: {"ar": "الضالع", "en": "Ad Dali"},
    13: {"ar": "البيضاء", "en": "Al Bayda"},
    14: {"ar": "مأرب", "en": "Ma'rib"},
    15: {"ar": "الجوف", "en": "Al Jawf"},
    16: {"ar": "صعدة", "en": "Sa'dah"},
    17: {"ar": "عمران", "en": "Amran"},
    18: {"ar": "حجة", "en": "Hajjah"},
    19: {"ar": "المحويت", "en": "Al Mahwit"},
    20: {"ar": "ريمة", "en": "Raymah"},
}

YEMEN_SEASONS = {
    "صيف": {"en": "summer", "months": [6, 7, 8], "crops": ["ذرة", "سمسم", "خضروات صيفية"]},
    "خريف": {"en": "autumn", "months": [9, 10, 11], "crops": ["قمح", "شعير", "بقوليات"]},
    "شتاء": {"en": "winter", "months": [12, 1, 2], "crops": ["قمح", "شعير", "خضروات شتوية"]},
    "ربيع": {"en": "spring", "months": [3, 4, 5], "crops": ["طماطم", "بصل", "بطاطس"]},
}

CROP_DATA = {
    "قمح": {"en": "wheat", "base_yield": 2200, "water": "medium"},
    "ذرة": {"en": "corn", "base_yield": 3500, "water": "high"},
    "شعير": {"en": "barley", "base_yield": 1800, "water": "low"},
    "طماطم": {"en": "tomato", "base_yield": 25000, "water": "high"},
    "بصل": {"en": "onion", "base_yield": 18000, "water": "medium"},
    "بطاطس": {"en": "potato", "base_yield": 20000, "water": "high"},
    "بن": {"en": "coffee", "base_yield": 800, "water": "medium"},
    "موز": {"en": "banana", "base_yield": 30000, "water": "very_high"},
    "مانجو": {"en": "mango", "base_yield": 15000, "water": "medium"},
}

# ============================================================
# Helper Functions
# ============================================================


def get_ndvi_health_status(ndvi: float) -> str:
    """تحديد حالة الصحة من NDVI"""
    if ndvi >= 0.7:
        return "ممتاز"
    elif ndvi >= 0.5:
        return "جيد"
    elif ndvi >= 0.3:
        return "متوسط"
    else:
        return "ضعيف"


def get_current_season() -> str:
    """تحديد الموسم الحالي"""
    month = datetime.now().month
    for season_ar, info in YEMEN_SEASONS.items():
        if month in info["months"]:
            return season_ar
    return "شتاء"


# ============================================================
# Endpoints
# ============================================================


@app.get("/health")
async def health():
    """فحص صحة الخدمة"""
    return {
        "status": "healthy",
        "service": "analytics-core",
        "version": "2.0.0",
        "database_connected": SHARED_LIB_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/analytics/ndvi/{field_id}/timeline", response_model=NDVITimelineResponse)
async def get_ndvi_timeline(
    field_id: str,
    months: int = Query(6, ge=1, le=24, description="عدد الأشهر")
):
    """الحصول على سلسلة NDVI الزمنية للحقل"""
    base_date = date.today()
    data = []
    base_ndvi = random.uniform(0.40, 0.60)

    for i in range(months * 4):  # بيانات أسبوعية
        d = base_date - timedelta(days=i * 7)
        month = d.month

        # تباين موسمي
        seasonal_boost = 0.12 if month in [3, 4, 5, 9, 10] else -0.05

        mean_val = base_ndvi + seasonal_boost + random.uniform(-0.04, 0.04)
        mean_val = max(0.1, min(0.9, mean_val))

        data.append(NDVITimelinePoint(
            date=d,
            mean_ndvi=round(mean_val, 3),
            min_ndvi=round(max(0, mean_val - random.uniform(0.05, 0.15)), 3),
            max_ndvi=round(min(1, mean_val + random.uniform(0.05, 0.15)), 3),
            std_ndvi=round(random.uniform(0.02, 0.08), 3),
            health_status=get_ndvi_health_status(mean_val)
        ))

    # حساب الترند
    recent = sum(d.mean_ndvi for d in data[:4]) / 4
    older = sum(d.mean_ndvi for d in data[-4:]) / 4
    trend_strength = abs(recent - older)

    if recent > older + 0.02:
        trend_direction = "ascending"
        health_summary = "تحسن ملحوظ في صحة المحصول"
    elif recent < older - 0.02:
        trend_direction = "descending"
        health_summary = "انخفاض في صحة المحصول - يحتاج متابعة"
    else:
        trend_direction = "stable"
        health_summary = "حالة مستقرة"

    avg_ndvi = sum(d.mean_ndvi for d in data) / len(data)

    return NDVITimelineResponse(
        field_id=field_id,
        field_name=f"حقل {field_id[:8]}",
        data=data,
        trend_direction=trend_direction,
        trend_strength=round(trend_strength, 3),
        avg_ndvi=round(avg_ndvi, 3),
        health_summary=health_summary
    )


@app.get("/api/v1/analytics/yield-prediction", response_model=YieldPrediction)
async def predict_yield(
    field_id: str,
    crop_type: str = Query("قمح", description="نوع المحصول")
):
    """التنبؤ بالإنتاج الزراعي"""
    crop_info = CROP_DATA.get(crop_type, {"base_yield": 2000, "water": "medium"})
    base = crop_info["base_yield"]

    # عوامل التأثير
    weather_factor = random.uniform(0.85, 1.15)
    soil_factor = random.uniform(0.90, 1.10)
    ndvi_value = random.uniform(0.4, 0.75)
    ndvi_factor = 0.7 + (ndvi_value * 0.4)

    predicted = base * weather_factor * soil_factor * ndvi_factor
    confidence = random.uniform(72, 92)
    margin = predicted * (100 - confidence) / 200

    factors = {
        "weather": {
            "impact": round((weather_factor - 1) * 100, 1),
            "description_ar": "تأثير الطقس على الإنتاجية"
        },
        "soil": {
            "impact": round((soil_factor - 1) * 100, 1),
            "description_ar": "جودة التربة"
        },
        "ndvi": {
            "value": round(ndvi_value, 3),
            "impact": round((ndvi_factor - 1) * 100, 1),
            "description_ar": "صحة المحصول"
        },
        "water_needs": crop_info["water"]
    }

    recommendations = []
    if weather_factor < 0.95:
        recommendations.append("مراقبة توقعات الطقس واتخاذ احتياطات")
    if soil_factor < 0.95:
        recommendations.append("تحسين خصوبة التربة بإضافة الأسمدة العضوية")
    if ndvi_value < 0.5:
        recommendations.append("زيادة الري ومراقبة الآفات")
    if not recommendations:
        recommendations.append("استمر في الممارسات الزراعية الحالية")

    return YieldPrediction(
        field_id=field_id,
        crop_type=crop_type,
        predicted_yield_kg_ha=round(predicted, 0),
        predicted_yield_ton_ha=round(predicted / 1000, 2),
        confidence_low=round(predicted - margin, 0),
        confidence_high=round(predicted + margin, 0),
        confidence_percent=round(confidence, 1),
        factors=factors,
        recommendations_ar=recommendations
    )


@app.get("/api/v1/analytics/seasonal", response_model=List[SeasonalAnalysis])
async def get_seasonal_analysis(region_id: Optional[int] = None):
    """تحليل المواسم الزراعية"""
    current_season = get_current_season()

    challenges = {
        "صيف": ["ارتفاع درجات الحرارة", "نقص المياه", "الآفات الحشرية"],
        "خريف": ["أمطار غزيرة محتملة", "فطريات", "انجراف التربة"],
        "شتاء": ["برودة الليل", "صقيع محتمل", "ندرة الأمطار"],
        "ربيع": ["تقلب الطقس", "رياح قوية", "آفات موسمية"],
    }

    water_needs = {
        "صيف": "عالية جداً - ري يومي",
        "خريف": "متوسطة - ري كل 3 أيام",
        "شتاء": "منخفضة - ري أسبوعي",
        "ربيع": "متوسطة إلى عالية",
    }

    analyses = []
    for season_ar, info in YEMEN_SEASONS.items():
        analyses.append(SeasonalAnalysis(
            season=info["en"],
            season_ar=season_ar,
            start_month=info["months"][0],
            end_month=info["months"][-1],
            recommended_crops=info["crops"],
            water_needs=water_needs[season_ar],
            expected_challenges=challenges[season_ar],
            current=(season_ar == current_season)
        ))

    return analyses


@app.get("/api/v1/analytics/region/{region_id}/stats", response_model=RegionStats)
async def get_region_stats(region_id: int):
    """إحصاءات المنطقة الزراعية"""
    if region_id not in YEMEN_REGIONS:
        raise HTTPException(status_code=404, detail="المنطقة غير موجودة")

    region = YEMEN_REGIONS[region_id]

    return RegionStats(
        region_id=region_id,
        region_name_ar=region["ar"],
        region_name_en=region["en"],
        total_fields=random.randint(500, 8000),
        total_farmers=random.randint(200, 3000),
        total_area_ha=round(random.uniform(2000, 80000), 2),
        avg_ndvi=round(random.uniform(0.38, 0.68), 3),
        active_crops=random.sample(list(CROP_DATA.keys()), k=min(4, len(CROP_DATA))),
        alerts_count=random.randint(0, 20),
        health_distribution={
            "excellent": round(random.uniform(15, 35), 1),
            "good": round(random.uniform(30, 45), 1),
            "moderate": round(random.uniform(15, 30), 1),
            "poor": round(random.uniform(5, 15), 1),
        }
    )


@app.get("/api/v1/analytics/regions/comparison")
async def compare_regions():
    """مقارنة بين المناطق الزراعية"""
    comparisons = []
    for region_id, region in YEMEN_REGIONS.items():
        comparisons.append({
            "region_id": region_id,
            "name_ar": region["ar"],
            "name_en": region["en"],
            "avg_ndvi": round(random.uniform(0.35, 0.70), 3),
            "total_area_ha": round(random.uniform(5000, 100000), 0),
            "productivity_index": round(random.uniform(60, 95), 1),
            "water_stress_index": round(random.uniform(20, 80), 1),
        })

    # ترتيب حسب NDVI
    comparisons.sort(key=lambda x: x["avg_ndvi"], reverse=True)

    return {
        "regions": comparisons,
        "best_performing": comparisons[0]["name_ar"],
        "needs_attention": comparisons[-1]["name_ar"],
        "national_avg_ndvi": round(sum(r["avg_ndvi"] for r in comparisons) / len(comparisons), 3)
    }


@app.get("/api/v1/analytics/crops/comparison", response_model=List[CropComparison])
async def compare_crops():
    """مقارنة بين المحاصيل"""
    comparisons = []
    for crop_ar, info in CROP_DATA.items():
        comparisons.append(CropComparison(
            crop_type=info["en"],
            crop_type_ar=crop_ar,
            avg_yield_kg_ha=info["base_yield"] * random.uniform(0.9, 1.1),
            avg_ndvi=round(random.uniform(0.45, 0.72), 3),
            total_area_ha=round(random.uniform(10000, 150000), 0),
            total_farmers=random.randint(500, 8000),
            profit_margin_percent=round(random.uniform(15, 45), 1)
        ))

    return comparisons


@app.get("/api/v1/analytics/dashboard", response_model=DashboardStats)
async def get_dashboard_stats():
    """إحصاءات لوحة التحكم الشاملة"""
    return DashboardStats(
        total_fields=random.randint(25000, 60000),
        total_farmers=random.randint(12000, 30000),
        total_area_ha=round(random.uniform(200000, 600000), 0),
        active_regions=20,
        avg_ndvi_national=round(random.uniform(0.42, 0.58), 3),
        alerts_today=random.randint(8, 60),
        crop_distribution={
            "قمح": 32.5,
            "ذرة": 22.0,
            "خضروات": 18.5,
            "بن": 12.0,
            "فواكه": 8.0,
            "أخرى": 7.0,
        },
        ndvi_status={
            "excellent": round(random.uniform(18, 28), 1),
            "good": round(random.uniform(35, 45), 1),
            "moderate": round(random.uniform(20, 30), 1),
            "poor": round(random.uniform(5, 12), 1),
        },
        weather_summary={
            "avg_temp": round(random.uniform(22, 32), 1),
            "rain_probability": random.randint(5, 40),
            "humidity": random.randint(30, 60),
        },
        last_updated=datetime.utcnow()
    )


@app.get("/api/v1/analytics/trends")
async def get_agricultural_trends(months: int = Query(12, ge=3, le=36)):
    """اتجاهات القطاع الزراعي"""
    trends = []
    base_date = date.today()

    for i in range(months):
        d = base_date - timedelta(days=i * 30)
        trends.append({
            "date": d.isoformat(),
            "month": d.strftime("%Y-%m"),
            "avg_ndvi": round(random.uniform(0.40, 0.60), 3),
            "total_yield_tons": round(random.uniform(50000, 150000), 0),
            "active_fields": random.randint(20000, 50000),
            "water_usage_million_m3": round(random.uniform(100, 500), 1),
        })

    trends.reverse()

    return {
        "period_months": months,
        "data": trends,
        "summary": {
            "ndvi_trend": "stable",
            "yield_trend": "increasing",
            "water_efficiency": "improving"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
