"""
سهول اليمن - Query Core Service
خدمة الاستعلامات وإدارة البيانات
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import random

app = FastAPI(
    title="Query Core - سهول اليمن",
    description="خدمة الاستعلامات وإدارة البيانات للمنصة الزراعية",
    version="1.0.0"
)

class FieldSummary(BaseModel):
    field_id: str
    name_ar: str
    crop_type: str
    area_ha: float
    region_name: str
    last_ndvi_date: date
    last_ndvi_value: float
    health_status: str

class FarmerInfo(BaseModel):
    farmer_id: str
    name: str
    phone: str
    region: str
    total_fields: int
    total_area_ha: float
    registration_date: date

class FieldDetails(BaseModel):
    field_id: str
    farmer_id: str
    name_ar: str
    area_ha: float
    crop_type: str
    region_id: int
    region_name: str
    coordinates: Dict[str, float]
    soil_type: str
    irrigation_type: str
    elevation_m: int
    last_ndvi: float
    created_at: datetime

class SearchResult(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[Dict[str, Any]]

# Sample data generators
CROP_TYPES = ["قمح", "ذرة", "شعير", "بن", "طماطم", "بصل", "بطاطس", "خضروات", "أعلاف"]
SOIL_TYPES = ["طينية", "رملية", "طينية رملية", "سلتية", "بركانية"]
IRRIGATION_TYPES = ["تنقيط", "رش", "غمر", "بعلي", "آبار"]
REGIONS = {
    1: "صنعاء", 2: "عدن", 3: "تعز", 4: "حضرموت", 5: "الحديدة",
    6: "إب", 7: "ذمار", 8: "شبوة", 9: "لحج", 10: "أبين",
    11: "مأرب", 12: "الجوف", 13: "عمران", 14: "حجة", 15: "المحويت",
    16: "ريمة", 17: "المهرة", 18: "سقطرى", 19: "البيضاء", 20: "صعدة",
}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "query-core"}

@app.get("/api/v1/fields/{field_id}/summary", response_model=FieldSummary)
async def get_field_summary(field_id: str):
    """الحصول على ملخص الحقل"""
    region_id = random.randint(1, 20)
    ndvi = round(random.uniform(0.3, 0.8), 2)

    if ndvi > 0.6:
        health = "ممتاز"
    elif ndvi > 0.4:
        health = "جيد"
    elif ndvi > 0.25:
        health = "متوسط"
    else:
        health = "يحتاج متابعة"

    return FieldSummary(
        field_id=field_id,
        name_ar=f"حقل {random.choice(['الخير', 'البركة', 'السلام', 'النور', 'الأمل'])} {random.randint(1, 100)}",
        crop_type=random.choice(CROP_TYPES),
        area_ha=round(random.uniform(0.5, 50), 2),
        region_name=REGIONS[region_id],
        last_ndvi_date=date.today(),
        last_ndvi_value=ndvi,
        health_status=health,
    )

@app.get("/api/v1/fields/{field_id}/details", response_model=FieldDetails)
async def get_field_details(field_id: str):
    """الحصول على تفاصيل الحقل الكاملة"""
    region_id = random.randint(1, 20)

    return FieldDetails(
        field_id=field_id,
        farmer_id=str(uuid4()),
        name_ar=f"حقل {random.choice(['الخير', 'البركة', 'السلام'])} {random.randint(1, 100)}",
        area_ha=round(random.uniform(0.5, 50), 2),
        crop_type=random.choice(CROP_TYPES),
        region_id=region_id,
        region_name=REGIONS[region_id],
        coordinates={
            "lat": round(random.uniform(12.5, 18.0), 6),
            "lon": round(random.uniform(42.5, 54.0), 6),
        },
        soil_type=random.choice(SOIL_TYPES),
        irrigation_type=random.choice(IRRIGATION_TYPES),
        elevation_m=random.randint(0, 2500),
        last_ndvi=round(random.uniform(0.3, 0.8), 3),
        created_at=datetime.utcnow(),
    )

@app.get("/api/v1/farmers/{farmer_id}", response_model=FarmerInfo)
async def get_farmer(farmer_id: str):
    """الحصول على معلومات المزارع"""
    region_id = random.randint(1, 20)
    names = ["أحمد محمد", "علي عبدالله", "محمد صالح", "عبدالرحمن أحمد", "خالد علي"]

    return FarmerInfo(
        farmer_id=farmer_id,
        name=random.choice(names),
        phone=f"+967{random.randint(700000000, 799999999)}",
        region=REGIONS[region_id],
        total_fields=random.randint(1, 10),
        total_area_ha=round(random.uniform(1, 100), 2),
        registration_date=date(random.randint(2020, 2024), random.randint(1, 12), random.randint(1, 28)),
    )

@app.get("/api/v1/fields/search", response_model=SearchResult)
async def search_fields(
    crop_type: Optional[str] = None,
    region_id: Optional[int] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    min_ndvi: Optional[float] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """البحث في الحقول"""
    # Generate mock results
    total = random.randint(50, 500)
    results = []

    for i in range(min(page_size, total - (page - 1) * page_size)):
        rid = region_id or random.randint(1, 20)
        results.append({
            "field_id": str(uuid4()),
            "name_ar": f"حقل {i + 1}",
            "crop_type": crop_type or random.choice(CROP_TYPES),
            "area_ha": round(random.uniform(min_area or 0.5, max_area or 50), 2),
            "region_name": REGIONS[rid],
            "ndvi": round(random.uniform(min_ndvi or 0.2, 0.8), 3),
        })

    return SearchResult(
        total=total,
        page=page,
        page_size=page_size,
        results=results,
    )

@app.get("/api/v1/regions")
async def list_regions():
    """قائمة المحافظات"""
    return {
        "regions": [
            {"id": k, "name_ar": v, "fields_count": random.randint(100, 5000)}
            for k, v in REGIONS.items()
        ]
    }

@app.get("/api/v1/crops")
async def list_crops():
    """قائمة المحاصيل"""
    return {
        "crops": [
            {"name_ar": crop, "fields_count": random.randint(500, 10000)}
            for crop in CROP_TYPES
        ]
    }

@app.get("/api/v1/stats/overview")
async def get_overview_stats():
    """إحصاءات عامة"""
    return {
        "total_farmers": random.randint(10000, 50000),
        "total_fields": random.randint(30000, 100000),
        "total_area_ha": round(random.uniform(200000, 800000), 0),
        "regions_count": 20,
        "crops_types": len(CROP_TYPES),
        "avg_field_size_ha": round(random.uniform(2, 8), 2),
        "last_updated": datetime.utcnow().isoformat(),
    }
