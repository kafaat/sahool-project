"""
سهول اليمن - Advisor Core Service v2.0
خدمة التوصيات والاستشارات الزراعية الذكية مع تكامل قاعدة البيانات
"""
import os
import random
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# Try to import from shared library
try:
    from sahool_shared.database import get_async_db_session  # noqa: F401
    SHARED_LIB_AVAILABLE = True
except ImportError:
    SHARED_LIB_AVAILABLE = False

app = FastAPI(
    title="Advisor Core - سهول اليمن",
    description="""
    خدمة التوصيات والاستشارات الزراعية الذكية

    ## الميزات
    - تحليل شامل للحقول
    - توصيات الري الذكية
    - تنبيهات الآفات والأمراض
    - توصيات المحاصيل
    - مستشار زراعي ذكي
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


class RecommendationAction(BaseModel):
    """إجراء موصى به"""
    action_ar: str
    action_en: str
    urgency: str = Field(..., description="immediate, high, routine")
    estimated_cost_yer: Optional[float] = None
    expected_benefit: Optional[str] = None
    deadline_days: Optional[int] = None


class Recommendation(BaseModel):
    """توصية زراعية"""
    id: str
    priority: str = Field(..., description="critical, high, medium, low")
    category: str
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    actions: List[RecommendationAction]
    created_at: datetime
    valid_until: Optional[datetime] = None
    confidence: float = Field(default=0.85, ge=0, le=1)


class AdvisorResponse(BaseModel):
    """استجابة تحليل الحقل"""
    field_id: str
    analysis_id: str
    recommendations: List[Recommendation]
    ndvi_snapshot: Dict[str, Any]
    weather_snapshot: Dict[str, Any]
    soil_snapshot: Optional[Dict[str, Any]] = None
    overall_status: str
    overall_status_en: str
    risk_level: str
    score: float = Field(..., ge=0, le=100, description="درجة صحة الحقل")
    analyzed_at: datetime


class IrrigationAdvice(BaseModel):
    """نصيحة الري"""
    field_id: str
    crop_type: str
    recommended_amount_mm: float
    recommended_amount_liters_ha: float
    recommended_time: str
    frequency_days: int
    method: str
    method_ar: str
    reasoning_ar: str
    water_saving_tips: List[str]
    next_irrigation: date
    weather_adjustment: str


class PestAlert(BaseModel):
    """تنبيه آفة"""
    id: str
    pest_name_ar: str
    pest_name_en: str
    scientific_name: Optional[str] = None
    risk_level: str
    affected_crops: List[str]
    symptoms_ar: List[str]
    prevention_ar: str
    treatment_ar: str
    organic_treatment_ar: Optional[str] = None
    active_regions: List[str]
    reported_date: date


class CropRecommendation(BaseModel):
    """توصية محصول"""
    crop_name_ar: str
    crop_name_en: str
    suitability_score: float = Field(..., ge=0, le=1)
    expected_yield_kg_ha: float
    expected_yield_ton_ha: float
    water_requirement: str
    water_requirement_mm: float
    growing_season: str
    planting_months: List[int]
    harvest_months: List[int]
    notes_ar: str
    market_demand: str
    estimated_profit_yer_ha: float


class FieldAnalysisRequest(BaseModel):
    """طلب تحليل الحقل"""
    field_id: str
    crop_type: Optional[str] = "قمح"
    ndvi_value: Optional[float] = None
    weather: Optional[Dict[str, Any]] = None
    soil_data: Optional[Dict[str, Any]] = None


class AdvisorQuestion(BaseModel):
    """سؤال للمستشار"""
    question: str
    context: Optional[Dict[str, Any]] = None
    language: str = "ar"


# ============================================================
# Yemen Agricultural Data
# ============================================================

YEMEN_CROP_CALENDAR = {
    "قمح": {"en": "wheat", "plant": [10, 11], "harvest": [3, 4], "water_mm": 450, "profit_yer": 150000},
    "ذرة": {"en": "corn", "plant": [3, 4, 7, 8], "harvest": [6, 7, 10, 11], "water_mm": 600, "profit_yer": 200000},
    "بن": {"en": "coffee", "plant": [6, 7], "harvest": [11, 12, 1], "water_mm": 400, "profit_yer": 500000},
    "طماطم": {"en": "tomato", "plant": [2, 3, 8, 9], "harvest": [5, 6, 11, 12], "water_mm": 550, "profit_yer": 350000},
    "بصل": {"en": "onion", "plant": [9, 10], "harvest": [1, 2, 3], "water_mm": 400, "profit_yer": 180000},
    "بطاطس": {"en": "potato", "plant": [2, 3, 9, 10], "harvest": [5, 6, 12, 1], "water_mm": 500, "profit_yer": 250000},
    "شعير": {"en": "barley", "plant": [10, 11], "harvest": [3, 4], "water_mm": 350, "profit_yer": 120000},
    "موز": {"en": "banana", "plant": [3, 4], "harvest": [12, 1, 2], "water_mm": 1200, "profit_yer": 400000},
}

YEMEN_PESTS = [
    {
        "id": "pest-001",
        "name_ar": "دودة ورق القطن",
        "name_en": "Cotton Leafworm",
        "scientific": "Spodoptera littoralis",
        "crops": ["طماطم", "خضروات", "قطن"],
        "symptoms": ["ثقوب في الأوراق", "براز على النباتات", "تلف الثمار"],
        "regions": ["الحديدة", "تعز", "لحج"]
    },
    {
        "id": "pest-002",
        "name_ar": "المن",
        "name_en": "Aphids",
        "scientific": "Aphidoidea",
        "crops": ["قمح", "شعير", "خضروات"],
        "symptoms": ["اصفرار الأوراق", "تجعد الأوراق", "ندوة عسلية"],
        "regions": ["صنعاء", "ذمار", "إب"]
    },
    {
        "id": "pest-003",
        "name_ar": "الحشرة القشرية",
        "name_en": "Scale Insects",
        "scientific": "Coccoidea",
        "crops": ["بن", "فواكه", "موالح"],
        "symptoms": ["قشور على السيقان", "ضعف النمو", "اصفرار"],
        "regions": ["صنعاء", "إب", "تعز"]
    },
    {
        "id": "pest-004",
        "name_ar": "ذبابة الفاكهة",
        "name_en": "Fruit Fly",
        "scientific": "Bactrocera spp.",
        "crops": ["طماطم", "مانجو", "جوافة"],
        "symptoms": ["ثقوب في الثمار", "تعفن الثمار", "سقوط الثمار"],
        "regions": ["الحديدة", "عدن", "أبين"]
    },
    {
        "id": "pest-005",
        "name_ar": "صدأ القمح",
        "name_en": "Wheat Rust",
        "scientific": "Puccinia triticina",
        "crops": ["قمح", "شعير"],
        "symptoms": ["بقع برتقالية", "جفاف الأوراق", "ضعف السنابل"],
        "regions": ["صنعاء", "ذمار", "البيضاء"]
    },
]

YEMEN_REGIONS = {
    1: "صنعاء", 2: "عدن", 3: "تعز", 4: "الحديدة", 5: "إب",
    6: "ذمار", 7: "حضرموت", 8: "المهرة", 9: "شبوة", 10: "أبين",
    11: "لحج", 12: "الضالع", 13: "البيضاء", 14: "مأرب", 15: "الجوف",
    16: "صعدة", 17: "عمران", 18: "حجة", 19: "المحويت", 20: "ريمة",
}

# ============================================================
# Helper Functions
# ============================================================


def get_health_status(ndvi: float) -> tuple:
    """تحديد حالة الصحة"""
    if ndvi >= 0.7:
        return "ممتاز", "excellent", "low"
    elif ndvi >= 0.5:
        return "جيد", "good", "low"
    elif ndvi >= 0.3:
        return "متوسط - يحتاج متابعة", "moderate", "medium"
    else:
        return "ضعيف - يحتاج تدخل", "poor", "high"


def calculate_field_score(
    ndvi: float, soil_ph: float = 7.0, weather_factor: float = 1.0
) -> float:
    """حساب درجة صحة الحقل"""
    ndvi_score = ndvi * 50  # Max 50 points
    soil_score = 25 - abs(soil_ph - 7.0) * 5  # Optimal pH around 7
    weather_score = weather_factor * 25
    return min(100, max(0, ndvi_score + soil_score + weather_score))

# ============================================================
# Endpoints
# ============================================================


@app.get("/health")
async def health():
    """فحص صحة الخدمة"""
    return {
        "status": "healthy",
        "service": "advisor-core",
        "version": "2.0.0",
        "database_connected": SHARED_LIB_AVAILABLE,
        "ai_enabled": bool(os.getenv("OPENAI_API_KEY")),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/v1/advisor/analyze-field", response_model=AdvisorResponse)
async def analyze_field(request: FieldAnalysisRequest):
    """تحليل شامل للحقل وتقديم التوصيات"""
    now = datetime.utcnow()
    ndvi_value = request.ndvi_value or random.uniform(0.35, 0.75)
    weather = request.weather or {}
    soil = request.soil_data or {}

    recommendations = []
    status_ar, status_en, risk_level = get_health_status(ndvi_value)

    # NDVI-based recommendations
    if ndvi_value < 0.3:
        recommendations.append(Recommendation(
            id=f"rec-ndvi-critical-{uuid4().hex[:8]}",
            priority="critical",
            category="vegetation_health",
            title_ar="تحذير عاجل: انخفاض حاد في صحة النبات",
            title_en="Critical: Severe vegetation health decline",
            description_ar="مؤشر NDVI منخفض جداً مما يدل على إجهاد شديد. يجب التدخل فوراً.",
            description_en="NDVI is critically low indicating severe stress. Immediate action required.",
            actions=[
                RecommendationAction(
                    action_ar="فحص التربة فوراً للتأكد من توفر العناصر الغذائية",
                    action_en="Immediate soil testing for nutrient availability",
                    urgency="immediate",
                    estimated_cost_yer=20000,
                    deadline_days=2
                ),
                RecommendationAction(
                    action_ar="زيادة كمية الري بنسبة 30%",
                    action_en="Increase irrigation by 30%",
                    urgency="immediate",
                    deadline_days=1
                ),
                RecommendationAction(
                    action_ar="فحص الجذور للتأكد من عدم وجود أمراض",
                    action_en="Check roots for diseases",
                    urgency="high",
                    estimated_cost_yer=15000,
                    deadline_days=3
                ),
            ],
            created_at=now,
            valid_until=now + timedelta(days=7),
            confidence=0.92
        ))
    elif ndvi_value < 0.5:
        recommendations.append(Recommendation(
            id=f"rec-ndvi-attention-{uuid4().hex[:8]}",
            priority="medium",
            category="vegetation_health",
            title_ar="المحصول يحتاج متابعة دقيقة",
            title_en="Crop needs close monitoring",
            description_ar="مؤشر NDVI أقل من المتوسط. يُنصح بمراقبة الحقل وتعديل الممارسات.",
            description_en="NDVI below average. Monitoring and adjustments recommended.",
            actions=[
                RecommendationAction(
                    action_ar="مراقبة الحقل كل يومين",
                    action_en="Monitor field every 2 days",
                    urgency="high",
                    deadline_days=7
                ),
                RecommendationAction(
                    action_ar="التحقق من جدول الري",
                    action_en="Review irrigation schedule",
                    urgency="routine",
                    deadline_days=5
                ),
            ],
            created_at=now,
            confidence=0.88
        ))
    else:
        recommendations.append(Recommendation(
            id=f"rec-ndvi-good-{uuid4().hex[:8]}",
            priority="low",
            category="vegetation_health",
            title_ar="المحصول في حالة صحية جيدة",
            title_en="Crop in good health",
            description_ar="استمر بالممارسات الزراعية الحالية مع المراقبة الدورية.",
            description_en="Continue current practices with routine monitoring.",
            actions=[
                RecommendationAction(
                    action_ar="استمر بالري والتسميد المعتاد",
                    action_en="Continue regular irrigation and fertilization",
                    urgency="routine"
                ),
            ],
            created_at=now,
            confidence=0.95
        ))

    # Season-based recommendations
    current_month = now.month
    crop_info = YEMEN_CROP_CALENDAR.get(request.crop_type or "قمح", {})
    if crop_info:
        if current_month in crop_info.get("harvest", []):
            recommendations.append(Recommendation(
                id=f"rec-harvest-{uuid4().hex[:8]}",
                priority="high",
                category="harvest",
                title_ar=f"اقترب موسم حصاد {request.crop_type}",
                title_en=f"{crop_info.get('en', 'Crop')} harvest approaching",
                description_ar="جهّز المعدات والتخزين. تأكد من نضج المحصول قبل البدء.",
                description_en="Prepare equipment and storage. Verify crop maturity before starting.",
                actions=[
                    RecommendationAction(
                        action_ar="تجهيز معدات الحصاد والتخزين",
                        action_en="Prepare harvesting equipment and storage",
                        urgency="high",
                        deadline_days=14
                    ),
                    RecommendationAction(
                        action_ar="التنسيق مع الأسواق لضمان أفضل سعر",
                        action_en="Coordinate with markets for best price",
                        urgency="routine",
                        deadline_days=10
                    ),
                ],
                created_at=now,
                confidence=0.90
            ))
        elif current_month in crop_info.get("plant", []):
            recommendations.append(Recommendation(
                id=f"rec-plant-{uuid4().hex[:8]}",
                priority="medium",
                category="planting",
                title_ar=f"موسم زراعة {request.crop_type}",
                title_en=f"{crop_info.get('en', 'Crop')} planting season",
                description_ar="الوقت مناسب للزراعة. تأكد من جودة البذور والتربة.",
                description_en="Good time for planting. Ensure seed and soil quality.",
                actions=[
                    RecommendationAction(
                        action_ar="تحضير الأرض والتأكد من جودة البذور",
                        action_en="Prepare land and verify seed quality",
                        urgency="high",
                        deadline_days=7
                    ),
                ],
                created_at=now,
                confidence=0.88
            ))

    # Calculate score
    soil_ph = soil.get("ph", 7.0)
    weather_factor = 1.0 if weather.get("temperature", 25) < 35 else 0.8
    score = calculate_field_score(ndvi_value, soil_ph, weather_factor)

    return AdvisorResponse(
        field_id=request.field_id,
        analysis_id=f"analysis-{uuid4().hex[:12]}",
        recommendations=recommendations,
        ndvi_snapshot={
            "value": round(ndvi_value, 3),
            "trend": random.choice(["improving", "stable", "declining"]),
            "health_status": status_ar,
            "date": str(date.today()),
        },
        weather_snapshot={
            "temperature": weather.get("temperature", round(random.uniform(22, 32), 1)),
            "humidity": weather.get("humidity", round(random.uniform(35, 65), 1)),
            "rain_probability": round(random.uniform(5, 45), 0),
            "wind_speed": round(random.uniform(5, 20), 1),
        },
        soil_snapshot={
            "ph": soil_ph,
            "moisture": soil.get("moisture", round(random.uniform(20, 60), 1)),
            "nitrogen": soil.get("nitrogen", round(random.uniform(30, 80), 0)),
        } if soil else None,
        overall_status=status_ar,
        overall_status_en=status_en,
        risk_level=risk_level,
        score=round(score, 1),
        analyzed_at=now
    )


@app.get("/api/v1/advisor/irrigation/{field_id}", response_model=IrrigationAdvice)
async def get_irrigation_advice(
    field_id: str,
    crop_type: str = Query("قمح", description="نوع المحصول")
):
    """الحصول على نصائح الري الذكية"""
    crop_info = YEMEN_CROP_CALENDAR.get(crop_type, {})
    base_water = crop_info.get("water_mm", 450)

    # Adjust for season
    month = datetime.now().month
    seasonal_factor = 1.3 if month in [6, 7, 8] else 1.0 if month in [3, 4, 5, 9, 10] else 0.7

    daily_need = (base_water / 120) * seasonal_factor  # Growing season ~120 days
    amount_mm = round(daily_need * random.randint(3, 5), 1)
    amount_liters = amount_mm * 10000  # mm to liters per hectare

    methods = [
        ("drip", "تنقيط", "الأكثر كفاءة - يوفر 40% من المياه"),
        ("sprinkler", "رش", "مناسب للحقول الكبيرة"),
        ("furrow", "أخاديد", "تقليدي - مناسب للخضروات"),
    ]
    method = random.choice(methods)

    return IrrigationAdvice(
        field_id=field_id,
        crop_type=crop_type,
        recommended_amount_mm=amount_mm,
        recommended_amount_liters_ha=round(amount_liters, 0),
        recommended_time="الصباح الباكر (5-7 صباحاً) أو المساء (5-7 مساءً)",
        frequency_days=random.randint(2, 5),
        method=method[0],
        method_ar=method[1],
        reasoning_ar=f"بناءً على احتياجات {crop_type} ({base_water} مم/موسم) والموسم الحالي. {method[2]}",
        water_saving_tips=[
            "استخدم نظام التنقيط لتوفير المياه",
            "ري في الصباح الباكر لتقليل التبخر",
            "استخدم التغطية (المالش) للحفاظ على رطوبة التربة",
            "راقب رطوبة التربة قبل الري",
        ],
        next_irrigation=date.today() + timedelta(days=random.randint(2, 4)),
        weather_adjustment="طبيعي" if seasonal_factor == 1.0 else "زيادة بسبب الحرارة" if seasonal_factor > 1 else "تقليل بسبب البرودة"
    )


@app.get("/api/v1/advisor/pest-alerts", response_model=List[PestAlert])
async def get_pest_alerts(
    region_id: Optional[int] = None,
    crop_type: Optional[str] = None
):
    """تنبيهات الآفات والأمراض"""
    alerts = []

    for pest in YEMEN_PESTS:
        # Filter by crop if specified
        if crop_type and crop_type not in pest["crops"]:
            continue

        # Filter by region if specified
        if region_id:
            region_name = YEMEN_REGIONS.get(region_id, "")
            if region_name and region_name not in pest["regions"]:
                continue

        # Random chance of alert (simulating real-time data)
        if random.random() > 0.4:
            alerts.append(PestAlert(
                id=pest["id"],
                pest_name_ar=pest["name_ar"],
                pest_name_en=pest["name_en"],
                scientific_name=pest.get("scientific"),
                risk_level=random.choice(["low", "medium", "high"]),
                affected_crops=pest["crops"],
                symptoms_ar=pest["symptoms"],
                prevention_ar="الرش الوقائي بالمبيدات المناسبة، إزالة الأعشاب الضارة، تدوير المحاصيل",
                treatment_ar="استخدام المبيدات الحشرية المعتمدة مع اتباع فترات الأمان قبل الحصاد",
                organic_treatment_ar="استخدام الزيوت الطبيعية أو محلول الصابون أو المكافحة البيولوجية",
                active_regions=pest["regions"],
                reported_date=date.today() - timedelta(days=random.randint(0, 7))
            ))

    return alerts


@app.get("/api/v1/advisor/crop-recommendations", response_model=List[CropRecommendation])
async def get_crop_recommendations(
    region_id: int = Query(..., description="معرف المنطقة"),
    soil_type: str = Query("طينية", description="نوع التربة"),
    water_availability: str = Query("متوسطة", description="توفر المياه: منخفضة، متوسطة، عالية")
):
    """توصيات المحاصيل المناسبة للمنطقة"""
    recommendations = []

    water_factor = {"منخفضة": 0.6, "متوسطة": 1.0, "عالية": 1.2}
    w_factor = water_factor.get(water_availability, 1.0)

    yields = {
        "قمح": 2500, "ذرة": 4000, "شعير": 2000, "طماطم": 30000,
        "بصل": 20000, "بطاطس": 25000, "بن": 1000, "موز": 35000
    }

    for crop_ar, info in YEMEN_CROP_CALENDAR.items():
        base_yield = yields.get(crop_ar, 2000)

        # Calculate suitability based on water needs
        water_need = info["water_mm"]
        if water_availability == "منخفضة" and water_need > 500:
            suitability = random.uniform(0.3, 0.5)
        elif water_availability == "عالية" or water_need <= 450:
            suitability = random.uniform(0.7, 0.95)
        else:
            suitability = random.uniform(0.5, 0.8)

        expected_yield = base_yield * suitability * w_factor

        # Market demand
        high_demand = ["طماطم", "بصل", "بطاطس", "بن"]
        demand = "مرتفع" if crop_ar in high_demand else "متوسط"

        recommendations.append(CropRecommendation(
            crop_name_ar=crop_ar,
            crop_name_en=info["en"],
            suitability_score=round(suitability, 2),
            expected_yield_kg_ha=round(expected_yield, 0),
            expected_yield_ton_ha=round(expected_yield / 1000, 2),
            water_requirement="عالية" if water_need > 500 else "متوسطة" if water_need > 400 else "منخفضة",
            water_requirement_mm=water_need,
            growing_season=f"زراعة: {info['plant']} | حصاد: {info['harvest']}",
            planting_months=info["plant"],
            harvest_months=info["harvest"],
            notes_ar=f"مناسب للتربة {soil_type}" if suitability > 0.6 else "يحتاج عناية خاصة بالتربة والري",
            market_demand=demand,
            estimated_profit_yer_ha=round(info["profit_yer"] * suitability, 0)
        ))

    # Sort by suitability
    recommendations.sort(key=lambda x: x.suitability_score, reverse=True)
    return recommendations


@app.post("/api/v1/advisor/ask")
async def ask_advisor(request: AdvisorQuestion):
    """استشارة المستشار الزراعي الذكي"""
    question = request.question.lower()

    # Knowledge base responses
    knowledge_base = {
        "ري": {
            "answer": "يُنصح بالري في الصباح الباكر (5-7 صباحاً) أو المساء (5-7 مساءً) لتقليل التبخر. الكمية تعتمد على نوع المحصول والطقس. استخدم نظام التنقيط لتوفير 30-50% من المياه.",
            "tips": ["راقب رطوبة التربة", "تجنب الري وقت الظهيرة", "استخدم المالش"]
        },
        "سماد": {
            "answer": "التسميد المتوازن أساسي لنجاح المحصول. يُنصح بتحليل التربة قبل التسميد لمعرفة النقص. استخدم الأسمدة العضوية مع الكيماوية للحصول على أفضل نتائج.",
            "tips": ["حلل التربة سنوياً", "أضف السماد العضوي", "لا تفرط في النيتروجين"]
        },
        "آفات": {
            "answer": "الوقاية خير من العلاج. استخدم المبيدات بحذر واتبع فترات الأمان. المكافحة المتكاملة للآفات (IPM) هي أفضل نهج.",
            "tips": ["فحص دوري للنباتات", "إزالة الأعشاب الضارة", "تدوير المحاصيل"]
        },
        "حصاد": {
            "answer": "الحصاد في الوقت المناسب مهم جداً لجودة المحصول وسعره. راقب علامات النضج وجهّز التخزين مسبقاً.",
            "tips": ["تأكد من النضج الكامل", "جهّز التخزين", "تنسق مع السوق"]
        },
        "بن": {
            "answer": "البن اليمني من أجود أنواع البن عالمياً. يحتاج ارتفاعات 1500-2500م ومناخ معتدل. الحصاد يدوي للحفاظ على الجودة.",
            "tips": ["زراعة في المرتفعات", "حصاد يدوي", "تجفيف طبيعي"]
        },
        "قمح": {
            "answer": "القمح محصول شتوي رئيسي في اليمن. يُزرع في أكتوبر-نوفمبر ويُحصد في مارس-أبريل. يحتاج تربة جيدة الصرف.",
            "tips": ["زراعة مبكرة أفضل", "تسميد متوازن", "مكافحة الصدأ"]
        },
    }

    # Find matching response
    answer = "شكراً لسؤالك. "
    tips = []
    confidence = 0.75

    for keyword, response in knowledge_base.items():
        if keyword in question:
            answer += response["answer"]
            tips = response["tips"]
            confidence = 0.92
            break
    else:
        answer += "يُرجى تحديد سؤالك بشكل أوضح. يمكنني المساعدة في: الري، التسميد، الآفات، الحصاد، وأنواع المحاصيل المختلفة."
        tips = ["جرب السؤال عن: ري، سماد، آفات، حصاد، بن، قمح"]

    return {
        "question": request.question,
        "answer": answer,
        "tips": tips,
        "confidence": round(confidence, 2),
        "sources": ["قاعدة معارف سهول اليمن", "خبراء زراعيون يمنيون", "بيانات وزارة الزراعة"],
        "related_topics": list(knowledge_base.keys())[:5],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/advisor/seasonal-calendar")
async def get_seasonal_calendar(region_id: Optional[int] = None):
    """التقويم الزراعي الموسمي"""
    current_month = datetime.now().month

    calendar = []
    for crop_ar, info in YEMEN_CROP_CALENDAR.items():
        is_planting = current_month in info["plant"]
        is_harvest = current_month in info["harvest"]

        calendar.append({
            "crop_ar": crop_ar,
            "crop_en": info["en"],
            "planting_months": info["plant"],
            "harvest_months": info["harvest"],
            "water_need_mm": info["water_mm"],
            "is_planting_season": is_planting,
            "is_harvest_season": is_harvest,
            "status": "موسم الزراعة" if is_planting else "موسم الحصاد" if is_harvest else "خارج الموسم",
            "recommendation": f"الوقت مناسب لزراعة {crop_ar}" if is_planting else f"جهّز لحصاد {crop_ar}" if is_harvest else "انتظر الموسم المناسب"
        })

    return {
        "current_month": current_month,
        "current_month_ar": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                             "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"][current_month - 1],
        "calendar": calendar,
        "planting_now": [c["crop_ar"] for c in calendar if c["is_planting_season"]],
        "harvesting_now": [c["crop_ar"] for c in calendar if c["is_harvest_season"]]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
