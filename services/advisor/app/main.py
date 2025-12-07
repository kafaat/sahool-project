"""
Sahool Yemen - Advisor Service (خدمة المستشار الزراعي)
Agricultural advisory recommendations based on NDVI, weather, and field data.
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
import httpx
import asyncio
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

# =============================================================================
# Configuration
# =============================================================================

app = FastAPI(
    title="Sahool Advisor Service",
    description="خدمة المستشار الزراعي - توصيات ذكية للمزارعين اليمنيين",
    version="9.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

import os

# CORS Configuration - use specific origins in production
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
CORS_ALLOW_CREDENTIALS = bool(CORS_ORIGINS)  # Only allow credentials with specific origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=CORS_ALLOW_CREDENTIALS,  # False when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter('sahool_advisor_requests_total', 'Total advisor requests', ['endpoint', 'status'])
REQUEST_LATENCY = Histogram('sahool_advisor_request_duration_seconds', 'Request latency', ['endpoint'])
RECOMMENDATIONS_GENERATED = Counter('sahool_advisor_recommendations_total', 'Total recommendations generated', ['type', 'severity'])

# =============================================================================
# Models
# =============================================================================

class RecommendationType(str, Enum):
    IRRIGATION = "irrigation"
    FERTILIZATION = "fertilization"
    PEST_CONTROL = "pest_control"
    HARVEST = "harvest"
    PLANTING = "planting"
    WEATHER_ALERT = "weather_alert"
    CROP_HEALTH = "crop_health"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Recommendation(BaseModel):
    id: str
    field_id: str
    type: RecommendationType
    severity: Severity
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    action_ar: str
    action_en: str
    valid_from: datetime
    valid_until: datetime
    metadata: dict = {}

class FieldAdvisory(BaseModel):
    field_id: str
    field_name: str
    ndvi_score: Optional[float] = None
    health_status: str
    recommendations: List[Recommendation]
    generated_at: datetime

class CropCalendarEntry(BaseModel):
    crop_type: str
    region: str
    activity: str
    start_month: int
    end_month: int
    description_ar: str
    description_en: str

# =============================================================================
# Crop Knowledge Base (Yemen-specific)
# =============================================================================

YEMEN_CROPS = {
    "qat": {
        "name_ar": "القات",
        "optimal_ndvi": (0.4, 0.7),
        "water_needs": "medium",
        "harvest_months": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    },
    "coffee": {
        "name_ar": "البن",
        "optimal_ndvi": (0.5, 0.8),
        "water_needs": "medium",
        "harvest_months": [10, 11, 12, 1]
    },
    "mango": {
        "name_ar": "المانجو",
        "optimal_ndvi": (0.5, 0.75),
        "water_needs": "high",
        "harvest_months": [5, 6, 7, 8]
    },
    "grapes": {
        "name_ar": "العنب",
        "optimal_ndvi": (0.45, 0.7),
        "water_needs": "medium",
        "harvest_months": [6, 7, 8, 9]
    },
    "wheat": {
        "name_ar": "القمح",
        "optimal_ndvi": (0.4, 0.65),
        "water_needs": "medium",
        "harvest_months": [4, 5]
    },
    "sorghum": {
        "name_ar": "الذرة الرفيعة",
        "optimal_ndvi": (0.35, 0.6),
        "water_needs": "low",
        "harvest_months": [9, 10, 11]
    },
    "tomato": {
        "name_ar": "الطماطم",
        "optimal_ndvi": (0.4, 0.65),
        "water_needs": "high",
        "harvest_months": [3, 4, 5, 10, 11]
    },
    "potato": {
        "name_ar": "البطاطس",
        "optimal_ndvi": (0.35, 0.6),
        "water_needs": "medium",
        "harvest_months": [3, 4, 9, 10]
    }
}

# =============================================================================
# Advisory Logic
# =============================================================================

def generate_ndvi_recommendations(
    ndvi_value: float,
    crop_type: str,
    region: str
) -> List[Recommendation]:
    """Generate recommendations based on NDVI value."""
    recommendations = []
    crop_info = YEMEN_CROPS.get(crop_type, {})
    optimal_range = crop_info.get("optimal_ndvi", (0.4, 0.7))
    now = datetime.utcnow()

    if ndvi_value < 0.2:
        rec = Recommendation(
            id=f"ndvi-critical-{now.timestamp()}",
            field_id="",
            type=RecommendationType.CROP_HEALTH,
            severity=Severity.CRITICAL,
            title_ar="تحذير: صحة المحصول حرجة",
            title_en="Warning: Critical Crop Health",
            description_ar=f"قيمة NDVI منخفضة جداً ({ndvi_value:.2f}). المحصول في حالة إجهاد شديد.",
            description_en=f"NDVI value is very low ({ndvi_value:.2f}). Crop is under severe stress.",
            action_ar="تحقق فوراً من الري والآفات. قد يكون المحصول يحتضر.",
            action_en="Immediately check irrigation and pests. Crop may be dying.",
            valid_from=now,
            valid_until=datetime(now.year, now.month, now.day + 3),
            metadata={"ndvi": ndvi_value, "threshold": 0.2}
        )
        recommendations.append(rec)
        RECOMMENDATIONS_GENERATED.labels(type="crop_health", severity="critical").inc()

    elif ndvi_value < optimal_range[0]:
        rec = Recommendation(
            id=f"ndvi-low-{now.timestamp()}",
            field_id="",
            type=RecommendationType.CROP_HEALTH,
            severity=Severity.HIGH,
            title_ar="صحة المحصول دون المستوى المطلوب",
            title_en="Crop Health Below Optimal",
            description_ar=f"قيمة NDVI ({ndvi_value:.2f}) أقل من النطاق الأمثل لـ{crop_info.get('name_ar', crop_type)}.",
            description_en=f"NDVI value ({ndvi_value:.2f}) is below optimal range for {crop_type}.",
            action_ar="زيادة الري وفحص التربة للتسميد.",
            action_en="Increase irrigation and check soil for fertilization needs.",
            valid_from=now,
            valid_until=datetime(now.year, now.month, now.day + 7),
            metadata={"ndvi": ndvi_value, "optimal_min": optimal_range[0]}
        )
        recommendations.append(rec)
        RECOMMENDATIONS_GENERATED.labels(type="crop_health", severity="high").inc()

    elif ndvi_value > optimal_range[1]:
        rec = Recommendation(
            id=f"ndvi-high-{now.timestamp()}",
            field_id="",
            type=RecommendationType.CROP_HEALTH,
            severity=Severity.LOW,
            title_ar="نمو نباتي ممتاز",
            title_en="Excellent Vegetation Growth",
            description_ar=f"قيمة NDVI ({ndvi_value:.2f}) تشير إلى نمو ممتاز.",
            description_en=f"NDVI value ({ndvi_value:.2f}) indicates excellent growth.",
            action_ar="حافظ على نظام الري الحالي. راقب للآفات.",
            action_en="Maintain current irrigation. Monitor for pests.",
            valid_from=now,
            valid_until=datetime(now.year, now.month, now.day + 14),
            metadata={"ndvi": ndvi_value}
        )
        recommendations.append(rec)
        RECOMMENDATIONS_GENERATED.labels(type="crop_health", severity="low").inc()

    return recommendations

def generate_weather_recommendations(
    temperature: float,
    humidity: float,
    rainfall: float,
    wind_speed: float,
    crop_type: str
) -> List[Recommendation]:
    """Generate recommendations based on weather conditions."""
    recommendations = []
    crop_info = YEMEN_CROPS.get(crop_type, {})
    water_needs = crop_info.get("water_needs", "medium")
    now = datetime.utcnow()

    # High temperature alert
    if temperature > 40:
        rec = Recommendation(
            id=f"temp-high-{now.timestamp()}",
            field_id="",
            type=RecommendationType.WEATHER_ALERT,
            severity=Severity.HIGH,
            title_ar="تحذير: درجة حرارة مرتفعة",
            title_en="Warning: High Temperature",
            description_ar=f"درجة الحرارة {temperature}°C. خطر إجهاد حراري للمحاصيل.",
            description_en=f"Temperature {temperature}°C. Risk of heat stress for crops.",
            action_ar="زيادة الري في الصباح الباكر أو المساء. تجنب الري وقت الظهيرة.",
            action_en="Increase irrigation in early morning or evening. Avoid midday watering.",
            valid_from=now,
            valid_until=datetime(now.year, now.month, now.day + 2),
            metadata={"temperature": temperature}
        )
        recommendations.append(rec)
        RECOMMENDATIONS_GENERATED.labels(type="weather_alert", severity="high").inc()

    # Low humidity with irrigation advice
    if humidity < 30 and water_needs in ["medium", "high"]:
        rec = Recommendation(
            id=f"humidity-low-{now.timestamp()}",
            field_id="",
            type=RecommendationType.IRRIGATION,
            severity=Severity.MEDIUM,
            title_ar="رطوبة منخفضة - زيادة الري",
            title_en="Low Humidity - Increase Irrigation",
            description_ar=f"الرطوبة {humidity}% منخفضة. المحصول يحتاج ري إضافي.",
            description_en=f"Humidity {humidity}% is low. Crop needs additional irrigation.",
            action_ar="زيادة تردد الري. استخدم الري بالتنقيط إن أمكن.",
            action_en="Increase irrigation frequency. Use drip irrigation if possible.",
            valid_from=now,
            valid_until=datetime(now.year, now.month, now.day + 3),
            metadata={"humidity": humidity}
        )
        recommendations.append(rec)
        RECOMMENDATIONS_GENERATED.labels(type="irrigation", severity="medium").inc()

    # Heavy rainfall
    if rainfall > 50:
        rec = Recommendation(
            id=f"rain-heavy-{now.timestamp()}",
            field_id="",
            type=RecommendationType.WEATHER_ALERT,
            severity=Severity.HIGH,
            title_ar="تحذير: أمطار غزيرة متوقعة",
            title_en="Warning: Heavy Rainfall Expected",
            description_ar=f"متوقع {rainfall}mm أمطار. خطر فيضان وتعفن الجذور.",
            description_en=f"Expected {rainfall}mm rainfall. Risk of flooding and root rot.",
            action_ar="تأكد من صرف المياه الزائدة. أوقف الري مؤقتاً.",
            action_en="Ensure proper drainage. Stop irrigation temporarily.",
            valid_from=now,
            valid_until=datetime(now.year, now.month, now.day + 1),
            metadata={"rainfall": rainfall}
        )
        recommendations.append(rec)
        RECOMMENDATIONS_GENERATED.labels(type="weather_alert", severity="high").inc()

    # High winds
    if wind_speed > 40:
        rec = Recommendation(
            id=f"wind-high-{now.timestamp()}",
            field_id="",
            type=RecommendationType.WEATHER_ALERT,
            severity=Severity.MEDIUM,
            title_ar="تحذير: رياح قوية",
            title_en="Warning: Strong Winds",
            description_ar=f"سرعة الرياح {wind_speed} كم/ساعة. خطر على المحاصيل.",
            description_en=f"Wind speed {wind_speed} km/h. Risk to crops.",
            action_ar="ثبت النباتات الطويلة. أجّل رش المبيدات.",
            action_en="Support tall plants. Postpone pesticide spraying.",
            valid_from=now,
            valid_until=datetime(now.year, now.month, now.day + 1),
            metadata={"wind_speed": wind_speed}
        )
        recommendations.append(rec)
        RECOMMENDATIONS_GENERATED.labels(type="weather_alert", severity="medium").inc()

    return recommendations

def get_seasonal_recommendations(
    crop_type: str,
    region: str,
    current_month: int
) -> List[Recommendation]:
    """Get seasonal recommendations based on crop calendar."""
    recommendations = []
    crop_info = YEMEN_CROPS.get(crop_type, {})
    harvest_months = crop_info.get("harvest_months", [])
    now = datetime.utcnow()

    if current_month in harvest_months:
        rec = Recommendation(
            id=f"harvest-{now.timestamp()}",
            field_id="",
            type=RecommendationType.HARVEST,
            severity=Severity.MEDIUM,
            title_ar=f"موسم حصاد {crop_info.get('name_ar', crop_type)}",
            title_en=f"{crop_type.title()} Harvest Season",
            description_ar="هذا الشهر مناسب للحصاد. راقب علامات النضج.",
            description_en="This month is suitable for harvest. Monitor for maturity signs.",
            action_ar="تحقق من نضج المحصول يومياً. جهز معدات الحصاد.",
            action_en="Check crop maturity daily. Prepare harvesting equipment.",
            valid_from=now,
            valid_until=datetime(now.year, now.month + 1, 1) if now.month < 12 else datetime(now.year + 1, 1, 1),
            metadata={"harvest_month": True}
        )
        recommendations.append(rec)
        RECOMMENDATIONS_GENERATED.labels(type="harvest", severity="medium").inc()

    return recommendations

# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "advisor", "version": "9.0.0"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")

@app.get("/api/v1/advisor/field/{field_id}", response_model=FieldAdvisory)
async def get_field_advisory(
    field_id: str,
    crop_type: str = Query("wheat", description="Crop type"),
    region: str = Query("صنعاء", description="Region name")
):
    """
    Get comprehensive advisory for a specific field.
    الحصول على توصيات شاملة لحقل معين.
    """
    with REQUEST_LATENCY.labels(endpoint="field_advisory").time():
        try:
            # In production, these would come from other services
            # Mock data for demonstration
            ndvi_value = 0.45
            temperature = 32
            humidity = 45
            rainfall = 5
            wind_speed = 15

            recommendations = []

            # NDVI recommendations
            recommendations.extend(
                generate_ndvi_recommendations(ndvi_value, crop_type, region)
            )

            # Weather recommendations
            recommendations.extend(
                generate_weather_recommendations(
                    temperature, humidity, rainfall, wind_speed, crop_type
                )
            )

            # Seasonal recommendations
            recommendations.extend(
                get_seasonal_recommendations(crop_type, region, datetime.now().month)
            )

            # Set field_id for all recommendations
            for rec in recommendations:
                rec.field_id = field_id

            REQUEST_COUNT.labels(endpoint="field_advisory", status="success").inc()

            return FieldAdvisory(
                field_id=field_id,
                field_name=f"Field {field_id}",
                ndvi_score=ndvi_value,
                health_status="good" if ndvi_value > 0.4 else "needs_attention",
                recommendations=recommendations,
                generated_at=datetime.utcnow()
            )

        except Exception as e:
            REQUEST_COUNT.labels(endpoint="field_advisory", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/advisor/crops")
async def get_supported_crops():
    """
    Get list of supported crops with Yemen-specific information.
    قائمة المحاصيل المدعومة مع معلومات خاصة باليمن.
    """
    return {
        "crops": [
            {
                "id": key,
                "name_ar": value["name_ar"],
                "name_en": key.title(),
                "optimal_ndvi_range": value["optimal_ndvi"],
                "water_needs": value["water_needs"],
                "harvest_months": value["harvest_months"]
            }
            for key, value in YEMEN_CROPS.items()
        ]
    }

@app.get("/api/v1/advisor/calendar")
async def get_crop_calendar(
    crop_type: str = Query(..., description="Crop type"),
    region: str = Query("صنعاء", description="Region")
):
    """
    Get crop calendar for a specific crop and region.
    تقويم زراعي لمحصول ومنطقة محددة.
    """
    crop_info = YEMEN_CROPS.get(crop_type)
    if not crop_info:
        raise HTTPException(status_code=404, detail=f"Crop {crop_type} not found")

    return {
        "crop": crop_type,
        "crop_name_ar": crop_info["name_ar"],
        "region": region,
        "harvest_months": crop_info["harvest_months"],
        "water_needs": crop_info["water_needs"],
        "calendar": [
            {
                "month": month,
                "activity": "harvest" if month in crop_info["harvest_months"] else "maintenance",
                "activity_ar": "حصاد" if month in crop_info["harvest_months"] else "رعاية"
            }
            for month in range(1, 13)
        ]
    }

@app.post("/api/v1/advisor/analyze")
async def analyze_conditions(
    ndvi: float = Query(..., ge=-1, le=1, description="NDVI value"),
    temperature: float = Query(..., description="Temperature in Celsius"),
    humidity: float = Query(..., ge=0, le=100, description="Humidity percentage"),
    rainfall: float = Query(0, ge=0, description="Rainfall in mm"),
    wind_speed: float = Query(0, ge=0, description="Wind speed in km/h"),
    crop_type: str = Query("wheat", description="Crop type"),
    region: str = Query("صنعاء", description="Region")
):
    """
    Analyze given conditions and return recommendations.
    تحليل الظروف المعطاة وإرجاع التوصيات.
    """
    with REQUEST_LATENCY.labels(endpoint="analyze").time():
        recommendations = []

        recommendations.extend(
            generate_ndvi_recommendations(ndvi, crop_type, region)
        )
        recommendations.extend(
            generate_weather_recommendations(
                temperature, humidity, rainfall, wind_speed, crop_type
            )
        )
        recommendations.extend(
            get_seasonal_recommendations(crop_type, region, datetime.now().month)
        )

        REQUEST_COUNT.labels(endpoint="analyze", status="success").inc()

        return {
            "analysis_date": datetime.utcnow().isoformat(),
            "conditions": {
                "ndvi": ndvi,
                "temperature": temperature,
                "humidity": humidity,
                "rainfall": rainfall,
                "wind_speed": wind_speed
            },
            "crop_type": crop_type,
            "region": region,
            "recommendations_count": len(recommendations),
            "recommendations": recommendations
        }

# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
