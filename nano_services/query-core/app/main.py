"""
سهول اليمن - Query Core Service v2.0
خدمة الاستعلامات المتقدمة وإدارة البيانات
Sahool Yemen - Advanced Query & Data Management Service
"""
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
import random

app = FastAPI(
    title="Query Core - سهول اليمن",
    description="خدمة الاستعلامات المتقدمة وإدارة البيانات للمنصة الزراعية اليمنية",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Enums ====================
class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class HealthStatus(str, Enum):
    EXCELLENT = "ممتاز"
    GOOD = "جيد"
    MODERATE = "متوسط"
    NEEDS_ATTENTION = "يحتاج متابعة"
    CRITICAL = "حرج"


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"


# ==================== Pydantic Models ====================
class FieldSummary(BaseModel):
    field_id: str = Field(..., description="معرف الحقل")
    name_ar: str = Field(..., description="اسم الحقل بالعربية")
    crop_type: str = Field(..., description="نوع المحصول")
    area_ha: float = Field(..., ge=0, description="المساحة بالهكتار")
    region_name: str = Field(..., description="اسم المحافظة")
    district_name: str = Field(..., description="اسم المديرية")
    last_ndvi_date: date = Field(..., description="تاريخ آخر قراءة NDVI")
    last_ndvi_value: float = Field(..., ge=-1, le=1, description="قيمة NDVI الأخيرة")
    health_status: str = Field(..., description="الحالة الصحية")
    trend: str = Field(..., description="اتجاه التغير")


class FarmerInfo(BaseModel):
    farmer_id: str = Field(..., description="معرف المزارع")
    name: str = Field(..., description="اسم المزارع")
    phone: str = Field(..., description="رقم الهاتف")
    region: str = Field(..., description="المحافظة")
    district: str = Field(..., description="المديرية")
    total_fields: int = Field(..., ge=0, description="إجمالي الحقول")
    total_area_ha: float = Field(..., ge=0, description="إجمالي المساحة")
    active_crops: List[str] = Field(..., description="المحاصيل الحالية")
    registration_date: date = Field(..., description="تاريخ التسجيل")
    verified: bool = Field(..., description="تم التحقق")


class FieldDetails(BaseModel):
    field_id: str
    farmer_id: str
    name_ar: str
    area_ha: float
    crop_type: str
    planting_date: Optional[date]
    expected_harvest: Optional[date]
    region_id: int
    region_name: str
    district_id: int
    district_name: str
    coordinates: Dict[str, float]
    polygon: List[List[float]]
    soil_type: str
    soil_ph: float
    irrigation_type: str
    water_source: str
    elevation_m: int
    slope_percent: float
    last_ndvi: float
    ndvi_history: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class SearchFilters(BaseModel):
    crop_types: Optional[List[str]] = None
    region_ids: Optional[List[int]] = None
    district_ids: Optional[List[int]] = None
    min_area: Optional[float] = Field(None, ge=0)
    max_area: Optional[float] = Field(None, ge=0)
    min_ndvi: Optional[float] = Field(None, ge=-1, le=1)
    max_ndvi: Optional[float] = Field(None, ge=-1, le=1)
    health_status: Optional[List[HealthStatus]] = None
    irrigation_types: Optional[List[str]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class SearchResult(BaseModel):
    total: int = Field(..., description="إجمالي النتائج")
    page: int = Field(..., description="الصفحة الحالية")
    page_size: int = Field(..., description="عدد النتائج بالصفحة")
    total_pages: int = Field(..., description="إجمالي الصفحات")
    has_next: bool = Field(..., description="يوجد صفحة تالية")
    has_prev: bool = Field(..., description="يوجد صفحة سابقة")
    results: List[Dict[str, Any]] = Field(..., description="النتائج")
    aggregations: Optional[Dict[str, Any]] = Field(None, description="التجميعات")


class AggregationResult(BaseModel):
    by_region: List[Dict[str, Any]]
    by_crop: List[Dict[str, Any]]
    by_health: List[Dict[str, Any]]
    by_irrigation: List[Dict[str, Any]]
    summary: Dict[str, Any]


class HistoricalQuery(BaseModel):
    field_id: str
    metric: str
    start_date: date
    end_date: date
    interval: str = "daily"


class HistoricalData(BaseModel):
    field_id: str
    metric: str
    start_date: date
    end_date: date
    data_points: List[Dict[str, Any]]
    statistics: Dict[str, float]


class BulkQueryRequest(BaseModel):
    field_ids: List[str] = Field(..., max_length=100)
    include_ndvi: bool = True
    include_weather: bool = False
    include_alerts: bool = True


class BulkQueryResult(BaseModel):
    total_requested: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, str]]


class SavedQuery(BaseModel):
    query_id: str
    name: str
    description: Optional[str]
    filters: SearchFilters
    created_at: datetime
    last_run: Optional[datetime]
    run_count: int


# ==================== Reference Data ====================
CROP_TYPES = [
    {"id": "wheat", "name_ar": "قمح", "season": "شتوي"},
    {"id": "corn", "name_ar": "ذرة", "season": "صيفي"},
    {"id": "barley", "name_ar": "شعير", "season": "شتوي"},
    {"id": "coffee", "name_ar": "بن", "season": "معمر"},
    {"id": "tomato", "name_ar": "طماطم", "season": "متعدد"},
    {"id": "onion", "name_ar": "بصل", "season": "شتوي"},
    {"id": "potato", "name_ar": "بطاطس", "season": "متعدد"},
    {"id": "vegetables", "name_ar": "خضروات", "season": "متعدد"},
    {"id": "fodder", "name_ar": "أعلاف", "season": "متعدد"},
    {"id": "qat", "name_ar": "قات", "season": "معمر"},
    {"id": "mango", "name_ar": "مانجو", "season": "معمر"},
    {"id": "banana", "name_ar": "موز", "season": "معمر"},
    {"id": "grapes", "name_ar": "عنب", "season": "معمر"},
    {"id": "sesame", "name_ar": "سمسم", "season": "صيفي"},
    {"id": "cotton", "name_ar": "قطن", "season": "صيفي"},
]

SOIL_TYPES = ["طينية", "رملية", "طينية رملية", "سلتية", "بركانية", "جيرية"]
IRRIGATION_TYPES = ["تنقيط", "رش", "غمر", "بعلي", "آبار", "سيول"]
WATER_SOURCES = ["بئر", "نهر", "سد", "مطر", "ينابيع", "شبكة"]

REGIONS = {
    1: {"name": "صنعاء", "districts": ["بني حشيش", "همدان", "سنحان", "بني مطر"]},
    2: {"name": "عدن", "districts": ["كريتر", "المنصورة", "خور مكسر", "الشيخ عثمان"]},
    3: {"name": "تعز", "districts": ["القاهرة", "صالة", "المظفر", "شرعب"]},
    4: {"name": "حضرموت", "districts": ["المكلا", "سيئون", "تريم", "شبام"]},
    5: {"name": "الحديدة", "districts": ["الحالي", "الدريهمي", "بيت الفقيه", "زبيد"]},
    6: {"name": "إب", "districts": ["إب", "جبلة", "يريم", "العدين"]},
    7: {"name": "ذمار", "districts": ["ذمار", "جهران", "عنس", "المنار"]},
    8: {"name": "شبوة", "districts": ["عتق", "بيحان", "نصاب", "عزان"]},
    9: {"name": "لحج", "districts": ["الحوطة", "تبن", "طور الباحة", "يافع"]},
    10: {"name": "أبين", "districts": ["زنجبار", "جعار", "لودر", "أحور"]},
    11: {"name": "مأرب", "districts": ["مأرب", "صرواح", "الجوبة", "مدغل"]},
    12: {"name": "الجوف", "districts": ["الحزم", "برط العنان", "خب والشعف"]},
    13: {"name": "عمران", "districts": ["عمران", "ثلاء", "حبور", "خمر"]},
    14: {"name": "حجة", "districts": ["حجة", "حرض", "ميدي", "عبس"]},
    15: {"name": "المحويت", "districts": ["المحويت", "شبام كوكبان", "الطويلة"]},
    16: {"name": "ريمة", "districts": ["الجبين", "الجعفرية", "السلفية"]},
    17: {"name": "المهرة", "districts": ["الغيضة", "حوف", "سيحوت", "قشن"]},
    18: {"name": "سقطرى", "districts": ["حديبو", "قلنسية"]},
    19: {"name": "البيضاء", "districts": ["البيضاء", "رداع", "الصومعة"]},
    20: {"name": "صعدة", "districts": ["صعدة", "حيدان", "مجز", "ساقين"]},
}


# ==================== Helper Functions ====================
def get_health_status(ndvi: float) -> str:
    if ndvi > 0.7:
        return HealthStatus.EXCELLENT.value
    elif ndvi > 0.5:
        return HealthStatus.GOOD.value
    elif ndvi > 0.35:
        return HealthStatus.MODERATE.value
    elif ndvi > 0.2:
        return HealthStatus.NEEDS_ATTENTION.value
    else:
        return HealthStatus.CRITICAL.value


def get_trend(values: List[float]) -> str:
    if len(values) < 2:
        return "مستقر"
    diff = values[-1] - values[0]
    if diff > 0.05:
        return "تحسن ↑"
    elif diff < -0.05:
        return "تراجع ↓"
    return "مستقر →"


def generate_ndvi_history(days: int = 30) -> List[Dict[str, Any]]:
    history = []
    base_ndvi = random.uniform(0.4, 0.7)
    for i in range(days):
        d = date.today() - timedelta(days=days - i - 1)
        ndvi = base_ndvi + random.uniform(-0.1, 0.1)
        ndvi = max(0.1, min(0.9, ndvi))
        history.append({
            "date": d.isoformat(),
            "ndvi": round(ndvi, 3),
            "source": random.choice(["Sentinel-2", "Landsat-8"]),
        })
        base_ndvi = ndvi
    return history


# ==================== API Endpoints ====================
@app.get("/health")
async def health():
    """فحص صحة الخدمة"""
    return {
        "status": "healthy",
        "service": "query-core",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v2/fields/{field_id}/summary", response_model=FieldSummary)
async def get_field_summary(
    field_id: str = Path(..., description="معرف الحقل")
):
    """الحصول على ملخص الحقل"""
    region_id = random.randint(1, 20)
    region_data = REGIONS[region_id]
    ndvi_history = [random.uniform(0.3, 0.8) for _ in range(5)]
    ndvi = ndvi_history[-1]

    return FieldSummary(
        field_id=field_id,
        name_ar=f"حقل {random.choice(['الخير', 'البركة', 'السلام', 'النور', 'الأمل'])} {random.randint(1, 100)}",
        crop_type=random.choice([c["name_ar"] for c in CROP_TYPES]),
        area_ha=round(random.uniform(0.5, 50), 2),
        region_name=region_data["name"],
        district_name=random.choice(region_data["districts"]),
        last_ndvi_date=date.today(),
        last_ndvi_value=round(ndvi, 3),
        health_status=get_health_status(ndvi),
        trend=get_trend(ndvi_history),
    )


@app.get("/api/v2/fields/{field_id}/details", response_model=FieldDetails)
async def get_field_details(field_id: str = Path(..., description="معرف الحقل")):
    """الحصول على تفاصيل الحقل الكاملة"""
    region_id = random.randint(1, 20)
    region_data = REGIONS[region_id]
    district_name = random.choice(region_data["districts"])
    ndvi_history = generate_ndvi_history(30)
    last_ndvi = float(ndvi_history[-1]["ndvi"])

    # Generate polygon coordinates
    base_lat = round(random.uniform(13.0, 17.0), 6)
    base_lon = round(random.uniform(43.0, 52.0), 6)
    polygon = [
        [base_lon, base_lat],
        [base_lon + 0.01, base_lat],
        [base_lon + 0.01, base_lat + 0.01],
        [base_lon, base_lat + 0.01],
        [base_lon, base_lat],
    ]

    alerts = []
    if last_ndvi < 0.4:
        alerts.append({
            "type": "vegetation_stress",
            "severity": "medium" if last_ndvi > 0.25 else "high",
            "message": "مؤشر الغطاء النباتي منخفض",
            "date": date.today().isoformat(),
        })

    return FieldDetails(
        field_id=field_id,
        farmer_id=str(uuid4()),
        name_ar=f"حقل {random.choice(['الخير', 'البركة', 'السلام'])} {random.randint(1, 100)}",
        area_ha=round(random.uniform(0.5, 50), 2),
        crop_type=random.choice([c["name_ar"] for c in CROP_TYPES]),
        planting_date=date.today() - timedelta(days=random.randint(30, 120)),
        expected_harvest=date.today() + timedelta(days=random.randint(30, 90)),
        region_id=region_id,
        region_name=region_data["name"],
        district_id=random.randint(1, 10),
        district_name=district_name,
        coordinates={"lat": base_lat, "lon": base_lon},
        polygon=polygon,
        soil_type=random.choice(SOIL_TYPES),
        soil_ph=round(random.uniform(5.5, 8.5), 1),
        irrigation_type=random.choice(IRRIGATION_TYPES),
        water_source=random.choice(WATER_SOURCES),
        elevation_m=random.randint(0, 2800),
        slope_percent=round(random.uniform(0, 15), 1),
        last_ndvi=last_ndvi,
        ndvi_history=ndvi_history[-7:],
        alerts=alerts,
        created_at=datetime.utcnow() - timedelta(days=random.randint(100, 500)),
        updated_at=datetime.utcnow(),
    )


@app.get("/api/v2/farmers/{farmer_id}", response_model=FarmerInfo)
async def get_farmer(farmer_id: str = Path(..., description="معرف المزارع")):
    """الحصول على معلومات المزارع"""
    region_id = random.randint(1, 20)
    region_data = REGIONS[region_id]
    names = ["أحمد محمد", "علي عبدالله", "محمد صالح", "عبدالرحمن أحمد", "خالد علي",
             "يحيى إبراهيم", "عبدالله حسن", "صالح أحمد", "فهد محمد", "ناصر علي"]

    return FarmerInfo(
        farmer_id=farmer_id,
        name=random.choice(names),
        phone=f"+967{random.randint(700000000, 799999999)}",
        region=region_data["name"],
        district=random.choice(region_data["districts"]),
        total_fields=random.randint(1, 15),
        total_area_ha=round(random.uniform(1, 150), 2),
        active_crops=random.sample([c["name_ar"] for c in CROP_TYPES], k=random.randint(1, 4)),
        registration_date=date(random.randint(2019, 2024), random.randint(1, 12), random.randint(1, 28)),
        verified=random.choice([True, True, True, False]),
    )


@app.get("/api/v2/fields/search", response_model=SearchResult)
async def search_fields(
    q: Optional[str] = Query(None, description="نص البحث"),
    crop_type: Optional[str] = Query(None, description="نوع المحصول"),
    region_id: Optional[int] = Query(None, ge=1, le=20, description="معرف المحافظة"),
    district: Optional[str] = Query(None, description="المديرية"),
    min_area: Optional[float] = Query(None, ge=0, description="الحد الأدنى للمساحة"),
    max_area: Optional[float] = Query(None, ge=0, description="الحد الأقصى للمساحة"),
    min_ndvi: Optional[float] = Query(None, ge=-1, le=1, description="الحد الأدنى NDVI"),
    max_ndvi: Optional[float] = Query(None, ge=-1, le=1, description="الحد الأقصى NDVI"),
    health_status: Optional[str] = Query(None, description="الحالة الصحية"),
    irrigation_type: Optional[str] = Query(None, description="نوع الري"),
    sort_by: str = Query("created_at", description="ترتيب حسب"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="اتجاه الترتيب"),
    page: int = Query(1, ge=1, description="رقم الصفحة"),
    page_size: int = Query(20, ge=1, le=100, description="عدد النتائج"),
    include_aggregations: bool = Query(False, description="تضمين التجميعات"),
):
    """البحث المتقدم في الحقول"""
    total = random.randint(100, 2000)
    total_pages = (total + page_size - 1) // page_size
    results = []

    for i in range(min(page_size, max(0, total - (page - 1) * page_size))):
        rid = region_id or random.randint(1, 20)
        region_data = REGIONS[rid]
        ndvi = round(random.uniform(min_ndvi or 0.15, max_ndvi or 0.85), 3)

        results.append({
            "field_id": str(uuid4()),
            "name_ar": f"حقل {random.choice(['الخير', 'البركة', 'السلام'])} {random.randint(1, 100)}",
            "crop_type": crop_type or random.choice([c["name_ar"] for c in CROP_TYPES]),
            "area_ha": round(random.uniform(min_area or 0.5, max_area or 50), 2),
            "region_name": region_data["name"],
            "district_name": district or random.choice(region_data["districts"]),
            "ndvi": ndvi,
            "health_status": get_health_status(ndvi),
            "irrigation_type": irrigation_type or random.choice(IRRIGATION_TYPES),
            "farmer_name": random.choice(["أحمد", "محمد", "علي", "خالد", "صالح"]),
        })

    aggregations = None
    if include_aggregations:
        aggregations = {
            "by_crop": [
                {"name": c["name_ar"], "count": random.randint(50, 500)}
                for c in random.sample(CROP_TYPES, 5)
            ],
            "by_region": [
                {"name": REGIONS[i]["name"], "count": random.randint(100, 1000)}
                for i in random.sample(list(REGIONS.keys()), 5)
            ],
            "by_health": [
                {"status": "ممتاز", "count": random.randint(100, 500)},
                {"status": "جيد", "count": random.randint(200, 800)},
                {"status": "متوسط", "count": random.randint(100, 400)},
                {"status": "يحتاج متابعة", "count": random.randint(50, 200)},
            ],
            "avg_area": round(random.uniform(3, 12), 2),
            "avg_ndvi": round(random.uniform(0.4, 0.6), 3),
        }

    return SearchResult(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        results=results,
        aggregations=aggregations,
    )


@app.post("/api/v2/fields/bulk-query", response_model=BulkQueryResult)
async def bulk_query_fields(request: BulkQueryRequest):
    """استعلام مجمع لعدة حقول"""
    results = []
    errors = []

    for field_id in request.field_ids:
        if random.random() > 0.95:  # 5% failure rate
            errors.append({
                "field_id": field_id,
                "error": "الحقل غير موجود",
            })
            continue

        region_id = random.randint(1, 20)
        region_data = REGIONS[region_id]
        ndvi = round(random.uniform(0.2, 0.8), 3)

        result = {
            "field_id": field_id,
            "name_ar": f"حقل {random.randint(1, 100)}",
            "region": region_data["name"],
            "area_ha": round(random.uniform(1, 30), 2),
            "crop_type": random.choice([c["name_ar"] for c in CROP_TYPES]),
        }

        if request.include_ndvi:
            result["ndvi"] = {
                "current": ndvi,
                "date": date.today().isoformat(),
                "health": get_health_status(ndvi),
            }

        if request.include_weather:
            result["weather"] = {
                "temp_c": random.randint(20, 40),
                "humidity": random.randint(30, 80),
                "precipitation_mm": round(random.uniform(0, 10), 1),
            }

        if request.include_alerts:
            alerts = []
            if ndvi < 0.35:
                alerts.append({
                    "type": "low_ndvi",
                    "message": "انخفاض في مؤشر الغطاء النباتي",
                })
            result["alerts"] = alerts

        results.append(result)

    return BulkQueryResult(
        total_requested=len(request.field_ids),
        successful=len(results),
        failed=len(errors),
        results=results,
        errors=errors,
    )


@app.get("/api/v2/fields/{field_id}/history", response_model=HistoricalData)
async def get_field_history(
    field_id: str = Path(..., description="معرف الحقل"),
    metric: str = Query("ndvi", description="المقياس المطلوب"),
    start_date: date = Query(..., description="تاريخ البداية"),
    end_date: date = Query(..., description="تاريخ النهاية"),
    interval: str = Query("daily", description="الفترة الزمنية"),
):
    """الحصول على البيانات التاريخية للحقل"""
    days = (end_date - start_date).days
    data_points = []

    if metric == "ndvi":
        base_value = random.uniform(0.4, 0.6)
        for i in range(min(days, 365)):
            d = start_date + timedelta(days=i)
            value = base_value + random.uniform(-0.1, 0.1)
            value = max(0.1, min(0.9, value))
            data_points.append({
                "date": d.isoformat(),
                "value": round(value, 3),
            })
            base_value = value
    elif metric == "temperature":
        for i in range(min(days, 365)):
            d = start_date + timedelta(days=i)
            data_points.append({
                "date": d.isoformat(),
                "value": random.randint(18, 38),
            })
    elif metric == "precipitation":
        for i in range(min(days, 365)):
            d = start_date + timedelta(days=i)
            data_points.append({
                "date": d.isoformat(),
                "value": round(random.uniform(0, 15), 1) if random.random() > 0.7 else 0,
            })

    values = [p["value"] for p in data_points]
    statistics = {
        "min": round(min(values), 3) if values else 0,
        "max": round(max(values), 3) if values else 0,
        "avg": round(sum(values) / len(values), 3) if values else 0,
        "count": len(values),
    }

    return HistoricalData(
        field_id=field_id,
        metric=metric,
        start_date=start_date,
        end_date=end_date,
        data_points=data_points,
        statistics=statistics,
    )


@app.get("/api/v2/aggregations", response_model=AggregationResult)
async def get_aggregations(
    region_id: Optional[int] = Query(None, description="تصفية حسب المحافظة"),
    crop_type: Optional[str] = Query(None, description="تصفية حسب المحصول"),
):
    """الحصول على تجميعات البيانات"""
    by_region = [
        {
            "region_id": rid,
            "region_name": data["name"],
            "fields_count": random.randint(500, 5000),
            "total_area_ha": round(random.uniform(5000, 50000), 0),
            "avg_ndvi": round(random.uniform(0.35, 0.65), 3),
        }
        for rid, data in REGIONS.items()
    ]

    by_crop = [
        {
            "crop_id": c["id"],
            "crop_name": c["name_ar"],
            "season": c["season"],
            "fields_count": random.randint(1000, 15000),
            "total_area_ha": round(random.uniform(10000, 100000), 0),
        }
        for c in CROP_TYPES
    ]

    by_health = [
        {"status": HealthStatus.EXCELLENT.value, "count": random.randint(5000, 15000), "percentage": 25},
        {"status": HealthStatus.GOOD.value, "count": random.randint(10000, 25000), "percentage": 35},
        {"status": HealthStatus.MODERATE.value, "count": random.randint(5000, 15000), "percentage": 25},
        {"status": HealthStatus.NEEDS_ATTENTION.value, "count": random.randint(2000, 8000), "percentage": 12},
        {"status": HealthStatus.CRITICAL.value, "count": random.randint(500, 2000), "percentage": 3},
    ]

    by_irrigation = [
        {"type": irr, "count": random.randint(2000, 20000)}
        for irr in IRRIGATION_TYPES
    ]

    summary = {
        "total_fields": random.randint(50000, 100000),
        "total_area_ha": round(random.uniform(300000, 800000), 0),
        "total_farmers": random.randint(15000, 40000),
        "avg_field_size_ha": round(random.uniform(3, 10), 2),
        "avg_ndvi": round(random.uniform(0.45, 0.55), 3),
    }

    return AggregationResult(
        by_region=by_region,
        by_crop=by_crop,
        by_health=by_health,
        by_irrigation=by_irrigation,
        summary=summary,
    )


@app.get("/api/v2/regions")
async def list_regions(
    include_stats: bool = Query(False, description="تضمين الإحصاءات"),
):
    """قائمة المحافظات مع المديريات"""
    regions = []
    for rid, data in REGIONS.items():
        region = {
            "id": rid,
            "name_ar": data["name"],
            "districts": [
                {"name_ar": d, "fields_count": random.randint(100, 2000)}
                for d in data["districts"]
            ],
        }
        if include_stats:
            region["stats"] = {
                "total_fields": random.randint(1000, 10000),
                "total_area_ha": round(random.uniform(10000, 80000), 0),
                "active_farmers": random.randint(500, 5000),
            }
        regions.append(region)

    return {"regions": regions, "total": len(regions)}


@app.get("/api/v2/crops")
async def list_crops():
    """قائمة المحاصيل مع التفاصيل"""
    crops = []
    for crop in CROP_TYPES:
        crops.append({
            **crop,
            "fields_count": random.randint(1000, 20000),
            "total_area_ha": round(random.uniform(5000, 100000), 0),
            "avg_yield_ton_ha": round(random.uniform(1, 10), 2),
        })

    return {"crops": crops, "total": len(crops)}


@app.get("/api/v2/stats/overview")
async def get_overview_stats():
    """إحصاءات عامة شاملة"""
    return {
        "summary": {
            "total_farmers": random.randint(25000, 45000),
            "total_fields": random.randint(60000, 120000),
            "total_area_ha": round(random.uniform(400000, 900000), 0),
            "regions_count": 20,
            "districts_count": sum(len(r["districts"]) for r in REGIONS.values()),
            "crops_count": len(CROP_TYPES),
        },
        "health_distribution": {
            "excellent": random.randint(15, 25),
            "good": random.randint(30, 40),
            "moderate": random.randint(20, 30),
            "needs_attention": random.randint(8, 15),
            "critical": random.randint(2, 5),
        },
        "top_regions": [
            {"name": REGIONS[i]["name"], "fields": random.randint(5000, 15000)}
            for i in [5, 3, 6, 1, 7]
        ],
        "top_crops": [
            {"name": c["name_ar"], "area_ha": random.randint(50000, 150000)}
            for c in random.sample(CROP_TYPES, 5)
        ],
        "recent_activity": {
            "new_fields_7d": random.randint(50, 200),
            "updated_fields_7d": random.randint(500, 2000),
            "alerts_generated_7d": random.randint(100, 500),
        },
        "last_updated": datetime.utcnow().isoformat(),
    }


@app.get("/api/v2/export/{format}")
async def export_data(
    format: ExportFormat = Path(..., description="صيغة التصدير"),
    region_id: Optional[int] = Query(None, description="تصفية حسب المحافظة"),
    crop_type: Optional[str] = Query(None, description="تصفية حسب المحصول"),
    limit: int = Query(1000, ge=1, le=10000, description="الحد الأقصى للسجلات"),
):
    """تصدير البيانات بصيغ مختلفة"""
    # In production, this would generate actual export files
    export_id = str(uuid4())

    return {
        "export_id": export_id,
        "format": format.value,
        "status": "processing",
        "estimated_records": random.randint(500, limit),
        "download_url": f"/api/v2/exports/{export_id}/download",
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        "message": "جاري تحضير الملف للتنزيل",
    }


@app.post("/api/v2/saved-queries")
async def create_saved_query(
    name: str = Query(..., description="اسم الاستعلام"),
    description: Optional[str] = Query(None, description="وصف الاستعلام"),
    filters: SearchFilters = None,
):
    """حفظ استعلام للاستخدام لاحقاً"""
    query_id = str(uuid4())

    return SavedQuery(
        query_id=query_id,
        name=name,
        description=description,
        filters=filters or SearchFilters(),
        created_at=datetime.utcnow(),
        last_run=None,
        run_count=0,
    )


@app.get("/api/v2/saved-queries")
async def list_saved_queries():
    """قائمة الاستعلامات المحفوظة"""
    queries = [
        {
            "query_id": str(uuid4()),
            "name": "حقول القمح في صنعاء",
            "description": "استعلام للحقول المزروعة بالقمح في محافظة صنعاء",
            "created_at": datetime.utcnow().isoformat(),
            "run_count": random.randint(5, 50),
        },
        {
            "query_id": str(uuid4()),
            "name": "حقول تحتاج متابعة",
            "description": "الحقول ذات مؤشر NDVI منخفض",
            "created_at": datetime.utcnow().isoformat(),
            "run_count": random.randint(10, 100),
        },
    ]

    return {"queries": queries, "total": len(queries)}
