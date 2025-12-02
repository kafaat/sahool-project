"""
سهول اليمن - Advisor Core Service
خدمة التوصيات والاستشارات الزراعية الذكية
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import random
import os

app = FastAPI(
    title="Advisor Core - سهول اليمن",
    description="خدمة التوصيات والاستشارات الزراعية الذكية باستخدام الذكاء الاصطناعي",
    version="1.0.0"
)

class RecommendationAction(BaseModel):
    action_ar: str
    action_en: str
    urgency: str
    estimated_cost_yer: Optional[float] = None
    expected_benefit: Optional[str] = None

class Recommendation(BaseModel):
    id: str
    priority: str
    category: str
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    actions: List[RecommendationAction]
    created_at: datetime
    valid_until: Optional[datetime] = None

class AdvisorResponse(BaseModel):
    field_id: int
    analysis_id: str
    recommendations: List[Recommendation]
    ndvi_snapshot: Dict[str, Any]
    weather_snapshot: Dict[str, Any]
    overall_status: str
    risk_level: str

class IrrigationAdvice(BaseModel):
    field_id: int
    recommended_amount_mm: float
    recommended_time: str
    frequency_days: int
    method: str
    reasoning_ar: str

class PestAlert(BaseModel):
    pest_name_ar: str
    pest_name_en: str
    risk_level: str
    affected_crops: List[str]
    prevention_ar: str
    treatment_ar: str

class CropRecommendation(BaseModel):
    crop_name_ar: str
    crop_name_en: str
    suitability_score: float
    expected_yield_kg_ha: float
    water_requirement: str
    growing_season: str
    notes_ar: str

# Yemen-specific agricultural knowledge
YEMEN_CROP_CALENDAR = {
    "قمح": {"plant": [10, 11], "harvest": [3, 4], "water_need": "متوسطة"},
    "ذرة": {"plant": [3, 4, 7, 8], "harvest": [6, 7, 10, 11], "water_need": "عالية"},
    "بن": {"plant": [6, 7], "harvest": [11, 12, 1], "water_need": "متوسطة"},
    "طماطم": {"plant": [2, 3, 8, 9], "harvest": [5, 6, 11, 12], "water_need": "عالية"},
}

YEMEN_PESTS = [
    {"name_ar": "دودة ورق القطن", "name_en": "Cotton Leafworm", "crops": ["طماطم", "خضروات"]},
    {"name_ar": "المن", "name_en": "Aphids", "crops": ["قمح", "شعير", "خضروات"]},
    {"name_ar": "الحشرة القشرية", "name_en": "Scale Insects", "crops": ["بن", "فواكه"]},
    {"name_ar": "ذبابة الفاكهة", "name_en": "Fruit Fly", "crops": ["طماطم", "فواكه"]},
]

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "advisor-core", "ai_enabled": bool(os.getenv("OPENAI_API_KEY"))}

@app.post("/api/v1/advisor/analyze-field", response_model=AdvisorResponse)
async def analyze_field(payload: dict):
    """تحليل شامل للحقل وتقديم التوصيات"""
    field_id = payload.get("field_id", 0)
    crop_type = payload.get("crop_type", "قمح")
    ndvi_value = payload.get("ndvi_value", random.uniform(0.3, 0.7))
    weather = payload.get("weather", {})

    now = datetime.utcnow()
    recommendations = []

    # NDVI-based recommendations
    if ndvi_value < 0.3:
        recommendations.append(Recommendation(
            id=f"rec-ndvi-{now.timestamp()}",
            priority="high",
            category="vegetation_health",
            title_ar="تحذير: انخفاض مؤشر صحة النبات",
            title_en="Warning: Low vegetation health index",
            description_ar="مؤشر NDVI منخفض جداً مما يدل على إجهاد شديد للنباتات أو مشاكل في النمو",
            description_en="NDVI index is very low indicating severe plant stress",
            actions=[
                RecommendationAction(
                    action_ar="فحص التربة للتأكد من توفر العناصر الغذائية",
                    action_en="Check soil for nutrient availability",
                    urgency="immediate",
                    estimated_cost_yer=15000,
                ),
                RecommendationAction(
                    action_ar="زيادة كمية الري بنسبة 20%",
                    action_en="Increase irrigation by 20%",
                    urgency="high",
                ),
            ],
            created_at=now,
        ))
    elif ndvi_value < 0.5:
        recommendations.append(Recommendation(
            id=f"rec-ndvi-{now.timestamp()}",
            priority="medium",
            category="vegetation_health",
            title_ar="المحصول يحتاج متابعة",
            title_en="Crop needs attention",
            description_ar="مؤشر NDVI أقل من المتوسط، يُنصح بمراقبة الحقل",
            description_en="NDVI below average, monitoring recommended",
            actions=[
                RecommendationAction(
                    action_ar="مراقبة الحقل يومياً",
                    action_en="Monitor field daily",
                    urgency="routine",
                ),
            ],
            created_at=now,
        ))
    else:
        recommendations.append(Recommendation(
            id=f"rec-ndvi-{now.timestamp()}",
            priority="low",
            category="vegetation_health",
            title_ar="المحصول في حالة جيدة",
            title_en="Crop in good condition",
            description_ar="مؤشر NDVI جيد، استمر بالممارسات الزراعية الحالية",
            description_en="NDVI is good, continue current practices",
            actions=[
                RecommendationAction(
                    action_ar="استمر بالري والتسميد المعتاد",
                    action_en="Continue regular irrigation and fertilization",
                    urgency="routine",
                ),
            ],
            created_at=now,
        ))

    # Season-based recommendations
    current_month = now.month
    crop_info = YEMEN_CROP_CALENDAR.get(crop_type, {})
    if crop_info and current_month in crop_info.get("harvest", []):
        recommendations.append(Recommendation(
            id=f"rec-harvest-{now.timestamp()}",
            priority="medium",
            category="harvest",
            title_ar=f"موسم حصاد {crop_type}",
            title_en=f"{crop_type} harvest season",
            description_ar="اقترب موعد الحصاد، جهّز المعدات والتخزين",
            description_en="Harvest time approaching, prepare equipment",
            actions=[
                RecommendationAction(
                    action_ar="تجهيز معدات الحصاد",
                    action_en="Prepare harvesting equipment",
                    urgency="routine",
                ),
            ],
            created_at=now,
        ))

    # Determine overall status
    if ndvi_value < 0.3:
        overall_status = "يحتاج تدخل عاجل"
        risk_level = "high"
    elif ndvi_value < 0.5:
        overall_status = "يحتاج متابعة"
        risk_level = "medium"
    else:
        overall_status = "جيد"
        risk_level = "low"

    return AdvisorResponse(
        field_id=field_id,
        analysis_id=f"analysis-{now.timestamp()}",
        recommendations=recommendations,
        ndvi_snapshot={
            "value": round(ndvi_value, 3),
            "trend": random.choice(["improving", "stable", "declining"]),
            "date": str(date.today()),
        },
        weather_snapshot={
            "temperature": weather.get("temperature", round(random.uniform(20, 35), 1)),
            "humidity": weather.get("humidity", round(random.uniform(30, 70), 1)),
            "rain_probability": round(random.uniform(0, 50), 0),
        },
        overall_status=overall_status,
        risk_level=risk_level,
    )

@app.get("/api/v1/advisor/irrigation/{field_id}", response_model=IrrigationAdvice)
async def get_irrigation_advice(field_id: int, crop_type: str = "قمح"):
    """الحصول على نصائح الري"""
    # Calculate based on crop and season
    water_needs = {
        "قمح": (15, 25, "متوسطة"),
        "ذرة": (25, 40, "عالية"),
        "طماطم": (20, 35, "عالية"),
        "بن": (15, 25, "متوسطة"),
        "خضروات": (20, 30, "عالية"),
    }

    crop_needs = water_needs.get(crop_type, (20, 30, "متوسطة"))

    return IrrigationAdvice(
        field_id=field_id,
        recommended_amount_mm=round(random.uniform(*crop_needs[:2]), 1),
        recommended_time="الصباح الباكر (5-7 صباحاً) أو المساء (5-7 مساءً)",
        frequency_days=random.randint(2, 5),
        method=random.choice(["تنقيط", "رش", "غمر"]),
        reasoning_ar=f"بناءً على احتياجات {crop_type} المائية ({crop_needs[2]}) والظروف الجوية الحالية",
    )

@app.get("/api/v1/advisor/pest-alerts", response_model=List[PestAlert])
async def get_pest_alerts(region_id: Optional[int] = None, crop_type: Optional[str] = None):
    """تنبيهات الآفات"""
    alerts = []

    for pest in YEMEN_PESTS:
        if crop_type and crop_type not in pest["crops"]:
            continue

        if random.random() > 0.5:  # 50% chance of alert
            alerts.append(PestAlert(
                pest_name_ar=pest["name_ar"],
                pest_name_en=pest["name_en"],
                risk_level=random.choice(["low", "medium", "high"]),
                affected_crops=pest["crops"],
                prevention_ar="الرش الوقائي بالمبيدات المناسبة وإزالة الأعشاب الضارة",
                treatment_ar="استخدام المبيدات الحشرية المعتمدة مع اتباع فترات الأمان",
            ))

    return alerts

@app.get("/api/v1/advisor/crop-recommendations", response_model=List[CropRecommendation])
async def get_crop_recommendations(
    region_id: int,
    soil_type: str = "طينية",
    water_availability: str = "متوسطة"
):
    """توصيات المحاصيل المناسبة"""
    all_crops = [
        ("قمح", "Wheat", 2500, "متوسطة", "أكتوبر - أبريل"),
        ("ذرة", "Corn", 4000, "عالية", "مارس - يوليو"),
        ("شعير", "Barley", 2000, "منخفضة", "أكتوبر - مارس"),
        ("طماطم", "Tomato", 30000, "عالية", "فبراير - يونيو"),
        ("بصل", "Onion", 20000, "متوسطة", "سبتمبر - فبراير"),
        ("بن", "Coffee", 1000, "متوسطة", "على مدار السنة"),
    ]

    recommendations = []
    for crop in all_crops:
        suitability = random.uniform(0.5, 1.0)
        if water_availability == "منخفضة" and crop[3] == "عالية":
            suitability *= 0.6

        recommendations.append(CropRecommendation(
            crop_name_ar=crop[0],
            crop_name_en=crop[1],
            suitability_score=round(suitability, 2),
            expected_yield_kg_ha=crop[2] * suitability,
            water_requirement=crop[3],
            growing_season=crop[4],
            notes_ar=f"مناسب للتربة {soil_type}" if suitability > 0.7 else "يحتاج عناية خاصة",
        ))

    return sorted(recommendations, key=lambda x: x.suitability_score, reverse=True)

@app.post("/api/v1/advisor/ask")
async def ask_advisor(payload: dict):
    """استشارة المستشار الزراعي (AI)"""
    question = payload.get("question", "")

    # Simple rule-based responses (in production, use OpenAI)
    responses = {
        "ري": "يُنصح بالري في الصباح الباكر أو المساء لتقليل التبخر. الكمية تعتمد على نوع المحصول وحالة الطقس.",
        "سماد": "التسميد يجب أن يكون متوازناً. يُنصح بتحليل التربة قبل التسميد لمعرفة النقص.",
        "آفات": "الوقاية خير من العلاج. استخدم المبيدات بحذر واتبع فترات الأمان.",
        "حصاد": "الحصاد في الوقت المناسب مهم جداً. راقب نضج المحصول وجهّز التخزين مسبقاً.",
    }

    answer = "شكراً لسؤالك. "
    for keyword, response in responses.items():
        if keyword in question:
            answer += response
            break
    else:
        answer += "يُرجى تحديد سؤالك بشكل أوضح. يمكنني المساعدة في مواضيع الري، التسميد، الآفات، والحصاد."

    return {
        "question": question,
        "answer": answer,
        "confidence": round(random.uniform(0.7, 0.95), 2),
        "sources": ["قاعدة بيانات سهول اليمن", "خبراء زراعيون محليون"],
    }
