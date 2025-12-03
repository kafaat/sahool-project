"""
سهول اليمن - OpenAPI Configuration
تكوين مخطط OpenAPI للتوثيق
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


class OpenAPIConfig(BaseModel):
    """OpenAPI configuration model"""
    title: str
    description: str
    version: str
    terms_of_service: Optional[str] = None
    contact_name: Optional[str] = "فريق سهول اليمن"
    contact_email: Optional[str] = "support@sahool.ye"
    license_name: Optional[str] = "MIT"
    license_url: Optional[str] = None


# Standard API Tags for all services
API_TAGS: List[Dict[str, str]] = [
    {
        "name": "Health",
        "description": "نقاط نهاية فحص صحة الخدمة - Health check endpoints",
    },
    {
        "name": "Weather",
        "description": "بيانات الطقس الزراعي لليمن - Agricultural weather data for Yemen",
    },
    {
        "name": "Geo",
        "description": "خدمات الجغرافيا والمساحة - Geographic and spatial services",
    },
    {
        "name": "Fields",
        "description": "إدارة الحقول الزراعية - Agricultural field management",
    },
    {
        "name": "Farmers",
        "description": "إدارة بيانات المزارعين - Farmer data management",
    },
    {
        "name": "NDVI",
        "description": "تحليل مؤشر الغطاء النباتي - Vegetation index analysis",
    },
    {
        "name": "Soil",
        "description": "تحليل التربة والخصوبة - Soil and fertility analysis",
    },
    {
        "name": "Irrigation",
        "description": "جدولة الري الذكية - Smart irrigation scheduling",
    },
    {
        "name": "Analytics",
        "description": "تحليلات وإحصاءات زراعية - Agricultural analytics and statistics",
    },
    {
        "name": "Alerts",
        "description": "التنبيهات والإشعارات الزراعية - Agricultural alerts and notifications",
    },
    {
        "name": "Auth",
        "description": "المصادقة والتفويض - Authentication and authorization",
    },
    {
        "name": "Admin",
        "description": "إدارة النظام - System administration",
    },
]


# Security schemes for JWT authentication
SECURITY_SCHEMES: Dict[str, Any] = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT token للمصادقة - Enter your JWT token",
    },
    "apiKey": {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "مفتاح API للتكامل - API key for integration",
    },
}


# Yemen regions for documentation
YEMEN_REGIONS = {
    "governorates": [
        {"id": 1, "name_ar": "صنعاء", "name_en": "Sana'a"},
        {"id": 2, "name_ar": "عدن", "name_en": "Aden"},
        {"id": 3, "name_ar": "تعز", "name_en": "Taiz"},
        {"id": 4, "name_ar": "الحديدة", "name_en": "Hudaydah"},
        {"id": 5, "name_ar": "إب", "name_en": "Ibb"},
        {"id": 6, "name_ar": "ذمار", "name_en": "Dhamar"},
        {"id": 7, "name_ar": "حضرموت", "name_en": "Hadhramaut"},
        {"id": 8, "name_ar": "المهرة", "name_en": "Al Mahrah"},
        {"id": 9, "name_ar": "شبوة", "name_en": "Shabwah"},
        {"id": 10, "name_ar": "أبين", "name_en": "Abyan"},
        {"id": 11, "name_ar": "لحج", "name_en": "Lahij"},
        {"id": 12, "name_ar": "الضالع", "name_en": "Ad Dali"},
        {"id": 13, "name_ar": "البيضاء", "name_en": "Al Bayda"},
        {"id": 14, "name_ar": "مأرب", "name_en": "Ma'rib"},
        {"id": 15, "name_ar": "الجوف", "name_en": "Al Jawf"},
        {"id": 16, "name_ar": "صعدة", "name_en": "Sa'dah"},
        {"id": 17, "name_ar": "عمران", "name_en": "Amran"},
        {"id": 18, "name_ar": "حجة", "name_en": "Hajjah"},
        {"id": 19, "name_ar": "المحويت", "name_en": "Al Mahwit"},
        {"id": 20, "name_ar": "ريمة", "name_en": "Raymah"},
    ],
    "agricultural_zones": [
        {"id": "coastal", "name_ar": "المنطقة الساحلية", "crops": ["قطن", "موز", "مانجو"]},
        {"id": "highland", "name_ar": "المرتفعات الجبلية", "crops": ["قمح", "شعير", "بن"]},
        {"id": "eastern", "name_ar": "المنطقة الشرقية", "crops": ["نخيل", "حبوب"]},
        {"id": "western", "name_ar": "السهول الغربية", "crops": ["ذرة", "سمسم", "خضروات"]},
    ],
}


def get_openapi_config(
    service_name: str,
    service_description: str,
    version: str = "1.0.0",
) -> OpenAPIConfig:
    """Get OpenAPI configuration for a service"""
    return OpenAPIConfig(
        title=f"سهول اليمن - {service_name}",
        description=f"""
        {service_description}

        ## المصادقة - Authentication
        استخدم JWT token في header التالي:
        ```
        Authorization: Bearer <your-token>
        ```

        ## الأخطاء - Errors
        | Code | Description |
        |------|-------------|
        | 400  | طلب غير صالح - Bad Request |
        | 401  | غير مصرح - Unauthorized |
        | 403  | محظور - Forbidden |
        | 404  | غير موجود - Not Found |
        | 422  | خطأ في البيانات - Validation Error |
        | 500  | خطأ في الخادم - Server Error |

        ## المحافظات المدعومة - Supported Governorates
        جميع المحافظات اليمنية العشرون مدعومة
        """,
        version=version,
        terms_of_service="https://sahool.ye/terms",
        contact_name="فريق سهول اليمن",
        contact_email="support@sahool.ye",
        license_name="MIT",
    )


def get_custom_openapi(
    app: FastAPI,
    config: OpenAPIConfig,
    tags: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Generate custom OpenAPI schema with Arabic support"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=config.title,
        version=config.version,
        description=config.description,
        routes=app.routes,
        tags=tags or API_TAGS,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = SECURITY_SCHEMES

    # Add server info
    openapi_schema["servers"] = [
        {"url": "/", "description": "الخادم الحالي - Current Server"},
        {"url": "http://localhost:8000", "description": "التطوير المحلي - Local Development"},
    ]

    # Add Yemen-specific info
    openapi_schema["info"]["x-logo"] = {
        "url": "https://sahool.ye/logo.png",
        "altText": "سهول اليمن",
    }
    openapi_schema["info"]["x-regions"] = YEMEN_REGIONS

    app.openapi_schema = openapi_schema
    return app.openapi_schema
