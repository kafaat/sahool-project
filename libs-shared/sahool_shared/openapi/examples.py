"""
سهول اليمن - OpenAPI Examples
أمثلة على الطلبات والاستجابات
"""
from typing import Dict, Any


class WeatherExamples:
    """Weather API examples"""

    CURRENT_WEATHER = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "region_id": 1,
        "date": "2024-01-15",
        "temperature": 25.5,
        "tmax": 28.0,
        "tmin": 18.0,
        "humidity": 45.0,
        "rainfall": 0.0,
        "wind_speed": 12.5,
        "wind_direction": "شمال شرق",
        "pressure": 1013.25,
        "source": "محطة صنعاء الجوية",
    }

    FORECAST = {
        "region_id": 1,
        "forecasts": [
            {
                "date": "2024-01-16",
                "tmax": 27.0,
                "tmin": 17.0,
                "rain_probability": 10.0,
                "humidity": 40.0,
                "description_ar": "صحو مع بعض السحب",
            },
            {
                "date": "2024-01-17",
                "tmax": 26.0,
                "tmin": 16.0,
                "rain_probability": 30.0,
                "humidity": 55.0,
                "description_ar": "غائم جزئياً مع احتمال أمطار خفيفة",
            },
        ],
    }

    ALERT = {
        "id": "alert-001",
        "type": "heat_wave",
        "severity": "moderate",
        "title_ar": "موجة حارة متوقعة",
        "description_ar": "يتوقع ارتفاع درجات الحرارة خلال الأيام القادمة",
        "affected_regions": ["صنعاء", "عمران", "ذمار"],
        "valid_from": "2024-01-20",
        "valid_until": "2024-01-25",
        "recommendations_ar": [
            "زيادة الري في الصباح الباكر",
            "تغطية المحاصيل الحساسة",
        ],
    }


class GeoExamples:
    """Geographic API examples"""

    FIELD_POLYGON = {
        "type": "Polygon",
        "coordinates": [
            [
                [44.1750, 15.3556],
                [44.1800, 15.3556],
                [44.1800, 15.3600],
                [44.1750, 15.3600],
                [44.1750, 15.3556],
            ]
        ],
    }

    AREA_RESULT = {
        "area_ha": 5.75,
        "area_m2": 57500.0,
        "perimeter_m": 980.5,
        "centroid": {"lat": 15.3578, "lon": 44.1775},
    }

    ELEVATION_RESULT = {
        "elevation_m": 2250.5,
        "slope_percent": 8.5,
        "aspect_degrees": 180,
        "terrain_type": "مرتفعات",
        "suitability": {
            "coffee": "ممتاز",
            "qat": "جيد",
            "wheat": "جيد",
        },
    }

    ZONE_INFO = {
        "zone_name": "المرتفعات الوسطى",
        "zone_type": "highland",
        "governorate": "صنعاء",
        "altitude_range": "2000-2500م",
        "annual_rainfall": "300-500 مم",
        "recommended_crops": ["بن يمني", "قمح", "شعير", "عدس"],
        "irrigation_type": "مطري مع تكميلي",
    }

    DISTANCE_RESULT = {
        "distance_km": 45.8,
        "distance_m": 45800.0,
        "bearing_degrees": 125.5,
        "bearing_description": "جنوب شرق",
    }


class FieldExamples:
    """Field management API examples"""

    FIELD_CREATE = {
        "name": "حقل القمح الشمالي",
        "region_id": 1,
        "area_hectares": 5.5,
        "crop_type": "قمح",
        "geometry": GeoExamples.FIELD_POLYGON,
        "irrigation_type": "مطري",
        "soil_type": "طيني",
    }

    FIELD_RESPONSE = {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "حقل القمح الشمالي",
        "region_id": 1,
        "farmer_id": "550e8400-e29b-41d4-a716-446655440002",
        "area_hectares": 5.5,
        "crop_type": "قمح",
        "planting_date": "2024-01-01",
        "expected_harvest_date": "2024-05-15",
        "geometry": GeoExamples.FIELD_POLYGON,
        "irrigation_type": "مطري",
        "soil_type": "طيني",
        "health_status": "healthy",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-15T14:30:00Z",
    }

    NDVI_ANALYSIS = {
        "field_id": "550e8400-e29b-41d4-a716-446655440001",
        "analysis_date": "2024-01-15",
        "mean_ndvi": 0.72,
        "min_ndvi": 0.45,
        "max_ndvi": 0.85,
        "health_status": "healthy",
        "health_description_ar": "الحقل في حالة صحية جيدة",
        "stress_areas_percent": 5.2,
        "recommendation_ar": "استمر في الري الحالي مع مراقبة المناطق الشرقية",
    }

    SOIL_ANALYSIS = {
        "field_id": "550e8400-e29b-41d4-a716-446655440001",
        "sample_date": "2024-01-10",
        "ph_value": 7.2,
        "nitrogen_ppm": 45.0,
        "phosphorus_ppm": 25.0,
        "potassium_ppm": 180.0,
        "organic_matter_percent": 2.5,
        "salinity_ms_cm": 0.8,
        "fertility_status": "متوسطة",
        "recommendations_ar": [
            "إضافة سماد نيتروجيني",
            "تحسين المادة العضوية بالكمبوست",
        ],
    }

    IRRIGATION_SCHEDULE = {
        "field_id": "550e8400-e29b-41d4-a716-446655440001",
        "scheduled_date": "2024-01-16",
        "start_time": "06:00",
        "duration_minutes": 45,
        "water_amount_liters": 5000,
        "method": "تنقيط",
        "status": "مجدول",
        "reason_ar": "ري دوري بناءً على رطوبة التربة",
    }


class AuthExamples:
    """Authentication API examples"""

    LOGIN_REQUEST = {
        "email": "farmer@example.com",
        "password": "securePassword123",
    }

    LOGIN_RESPONSE = {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "id": "550e8400-e29b-41d4-a716-446655440003",
            "email": "farmer@example.com",
            "name": "أحمد محمد",
            "role": "farmer",
            "tenant_id": "tenant-001",
        },
    }

    REGISTER_REQUEST = {
        "email": "newfarmer@example.com",
        "password": "securePassword123",
        "name": "علي أحمد",
        "phone": "+967777123456",
        "region_id": 1,
        "preferred_language": "ar",
    }

    USER_PROFILE = {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "email": "farmer@example.com",
        "name": "أحمد محمد",
        "phone": "+967777123456",
        "role": "farmer",
        "region_id": 1,
        "total_fields": 3,
        "total_area_hectares": 15.5,
        "joined_at": "2023-06-15T10:00:00Z",
        "subscription_tier": "premium",
    }


class AnalyticsExamples:
    """Analytics API examples"""

    YIELD_SUMMARY = {
        "farmer_id": "550e8400-e29b-41d4-a716-446655440003",
        "year": 2024,
        "total_yield_tons": 45.5,
        "total_revenue_yer": 15000000,
        "total_expenses_yer": 5000000,
        "profit_yer": 10000000,
        "profit_margin_percent": 66.7,
        "crop_breakdown": [
            {"crop": "قمح", "yield_tons": 25.0, "revenue_yer": 8000000},
            {"crop": "ذرة", "yield_tons": 20.5, "revenue_yer": 7000000},
        ],
    }

    SEASONAL_REPORT = {
        "season": "شتاء 2024",
        "region_id": 1,
        "total_farms": 150,
        "total_area_hectares": 750.0,
        "average_yield_ton_per_ha": 3.2,
        "weather_summary": {
            "avg_temperature": 18.5,
            "total_rainfall_mm": 120.0,
            "rainy_days": 15,
        },
        "crop_performance": [
            {"crop": "قمح", "avg_yield": 3.5, "success_rate": 85.0},
            {"crop": "شعير", "avg_yield": 2.8, "success_rate": 82.0},
        ],
    }


def get_example(example_class: str, example_name: str) -> Dict[str, Any]:
    """Get an example by class and name"""
    classes = {
        "weather": WeatherExamples,
        "geo": GeoExamples,
        "field": FieldExamples,
        "auth": AuthExamples,
        "analytics": AnalyticsExamples,
    }
    cls = classes.get(example_class)
    if cls:
        return getattr(cls, example_name, {})
    return {}
