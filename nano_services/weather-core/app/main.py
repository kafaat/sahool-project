"""
سهول اليمن - Weather Core Service v2.0
خدمة بيانات الطقس الزراعي لليمن مع تكامل قاعدة البيانات
"""
import logging
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import from shared library - imports marked as potentially unused with noqa
try:
    from sahool_shared.database import get_async_db_session, DatabaseManager  # noqa: F401
    from sahool_shared.models import WeatherData, Region, Field as FieldModel  # noqa: F401
    from sahool_shared.auth import get_current_user, AuthenticatedUser  # noqa: F401
    SHARED_LIB_AVAILABLE = True
except ImportError:
    SHARED_LIB_AVAILABLE = False

app = FastAPI(
    title="Weather Core - سهول اليمن",
    description="خدمة بيانات الطقس الزراعي لجميع المحافظات اليمنية",
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


class WeatherResponse(BaseModel):
    """نموذج استجابة بيانات الطقس"""
    id: Optional[str] = None
    field_id: Optional[str] = None
    region_id: Optional[int] = None
    date: date
    temperature: float = Field(..., description="درجة الحرارة الحالية")
    tmax: Optional[float] = Field(None, description="أعلى درجة حرارة")
    tmin: Optional[float] = Field(None, description="أدنى درجة حرارة")
    humidity: float = Field(..., description="نسبة الرطوبة")
    rainfall: float = Field(0, description="كمية الأمطار بالمم")
    wind_speed: Optional[float] = Field(None, description="سرعة الرياح")
    wind_direction: Optional[str] = Field(None, description="اتجاه الرياح")
    pressure: Optional[float] = Field(None, description="الضغط الجوي")
    source: str = Field("database", description="مصدر البيانات")

    class Config:
        from_attributes = True


class WeatherForecast(BaseModel):
    """نموذج توقعات الطقس"""
    date: date
    tmax: float
    tmin: float
    rain_probability: float
    humidity: float
    description_ar: str


class WeatherForecastResponse(BaseModel):
    """نموذج استجابة التوقعات"""
    field_id: Optional[str] = None
    region_id: Optional[int] = None
    forecasts: List[WeatherForecast]


class WeatherAlert(BaseModel):
    """نموذج تنبيه الطقس"""
    id: str
    type: str
    severity: str
    title_ar: str
    description_ar: str
    affected_regions: List[str]
    valid_from: date
    valid_until: date


class WeatherCreate(BaseModel):
    """نموذج إنشاء بيانات طقس جديدة"""
    region_id: Optional[int] = None
    field_id: Optional[str] = None
    temperature: float
    humidity: float
    rainfall: float = 0
    wind_speed: Optional[float] = None
    wind_direction: Optional[str] = None
    pressure: Optional[float] = None
    forecast_date: Optional[date] = None


# ============================================================
# Yemen Weather Profiles
# ============================================================

YEMEN_REGIONS = {
    1: {"name": "صنعاء", "type": "highland", "temp_base": 22},
    2: {"name": "عدن", "type": "coastal", "temp_base": 32},
    3: {"name": "تعز", "type": "highland", "temp_base": 24},
    4: {"name": "حضرموت", "type": "desert", "temp_base": 35},
    5: {"name": "الحديدة", "type": "coastal", "temp_base": 34},
    6: {"name": "إب", "type": "highland", "temp_base": 20},
    7: {"name": "ذمار", "type": "highland", "temp_base": 18},
    8: {"name": "مأرب", "type": "desert", "temp_base": 33},
}

WEATHER_DESCRIPTIONS = [
    "صحو مع ارتفاع في درجات الحرارة",
    "غائم جزئياً",
    "احتمال أمطار خفيفة",
    "طقس معتدل",
    "رياح نشطة",
    "صحو",
    "غائم مع احتمال زخات مطرية",
]


# ============================================================
# Database Helper Functions
# ============================================================

async def get_weather_from_db(
    session: AsyncSession,
    field_id: Optional[UUID] = None,
    region_id: Optional[int] = None,
    target_date: Optional[date] = None
) -> Optional[WeatherData]:
    """جلب بيانات الطقس من قاعدة البيانات"""
    if not SHARED_LIB_AVAILABLE:
        return None

    from sqlalchemy import select

    query = select(WeatherData)

    if field_id:
        query = query.where(WeatherData.field_id == field_id)
    if region_id:
        query = query.where(WeatherData.region_id == region_id)
    if target_date:
        query = query.where(WeatherData.forecast_date == target_date)

    query = query.order_by(WeatherData.created_at.desc()).limit(1)

    result = await session.execute(query)
    return result.scalar_one_or_none()


def generate_mock_weather(region_id: int = 1, target_date: date = None) -> dict:
    """توليد بيانات طقس وهمية للتطوير"""
    import random

    region = YEMEN_REGIONS.get(region_id, YEMEN_REGIONS[1])
    temp_base = region["temp_base"]

    temp = temp_base + random.uniform(-5, 5)

    return {
        "temperature": round(temp, 1),
        "tmax": round(temp + random.uniform(3, 8), 1),
        "tmin": round(temp - random.uniform(5, 10), 1),
        "humidity": round(random.uniform(30, 80), 1),
        "rainfall": round(random.uniform(0, 10), 1) if random.random() > 0.7 else 0,
        "wind_speed": round(random.uniform(1, 15), 1),
        "wind_direction": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
        "pressure": round(random.uniform(1010, 1025), 1),
        "date": target_date or date.today(),
        "source": "mock"
    }


# ============================================================
# API Endpoints
# ============================================================

@app.get("/health")
async def health():
    """فحص صحة الخدمة"""
    return {
        "status": "healthy",
        "service": "weather-core",
        "version": "2.0.0",
        "region": "Yemen",
        "database_connected": SHARED_LIB_AVAILABLE
    }


@app.get("/api/v1/weather/regions/{region_id}", response_model=WeatherResponse)
async def get_region_weather(
    region_id: int,
    target_date: Optional[date] = None
):
    """الحصول على بيانات الطقس حسب المنطقة"""
    d = target_date or date.today()

    # Try database first if available
    if SHARED_LIB_AVAILABLE:
        try:
            db_manager = DatabaseManager()
            async with db_manager.get_async_session() as session:
                weather = await get_weather_from_db(session, region_id=region_id, target_date=d)
                if weather:
                    return WeatherResponse(
                        id=str(weather.id),
                        region_id=region_id,
                        date=weather.forecast_date or d,
                        temperature=float(weather.temperature) if weather.temperature else 25.0,
                        humidity=float(weather.humidity) if weather.humidity else 50.0,
                        rainfall=float(weather.rainfall) if weather.rainfall else 0,
                        wind_speed=float(weather.wind_speed) if weather.wind_speed else None,
                        wind_direction=weather.wind_direction,
                        pressure=float(weather.pressure) if weather.pressure else None,
                        source="database"
                    )
        except Exception as e:
            logger.warning(f"Database query failed for region {region_id}, falling back to mock data: {e}")

    # Fallback to mock data
    mock = generate_mock_weather(region_id, d)
    return WeatherResponse(
        region_id=region_id,
        date=d,
        **mock
    )


@app.get("/api/v1/weather/fields/{field_id}", response_model=WeatherResponse)
async def get_field_weather(
    field_id: str,
    target_date: Optional[date] = None
):
    """الحصول على بيانات الطقس للحقل"""
    d = target_date or date.today()

    if SHARED_LIB_AVAILABLE:
        try:
            from uuid import UUID as UUIDType
            field_uuid = UUIDType(field_id)
            db_manager = DatabaseManager()
            async with db_manager.get_async_session() as session:
                weather = await get_weather_from_db(session, field_id=field_uuid, target_date=d)
                if weather:
                    return WeatherResponse(
                        id=str(weather.id),
                        field_id=field_id,
                        date=weather.forecast_date or d,
                        temperature=float(weather.temperature) if weather.temperature else 25.0,
                        humidity=float(weather.humidity) if weather.humidity else 50.0,
                        rainfall=float(weather.rainfall) if weather.rainfall else 0,
                        source="database"
                    )
        except Exception as e:
            logger.warning(f"Database query failed for field {field_id}, falling back to mock data: {e}")

    # Fallback to mock
    mock = generate_mock_weather(1, d)
    return WeatherResponse(
        field_id=field_id,
        date=d,
        **mock
    )


@app.get("/api/v1/weather/fields/{field_id}/forecast", response_model=WeatherForecastResponse)
async def get_field_forecast(
    field_id: str,
    days: int = Query(7, ge=1, le=14, description="عدد أيام التوقعات")
):
    """الحصول على توقعات الطقس للحقل"""
    import random

    forecasts = []
    base_date = date.today()

    for i in range(days):
        d = base_date + timedelta(days=i)
        mock = generate_mock_weather(1, d)

        forecasts.append(WeatherForecast(
            date=d,
            tmax=mock["tmax"],
            tmin=mock["tmin"],
            rain_probability=round(random.uniform(0, 60), 0),
            humidity=mock["humidity"],
            description_ar=random.choice(WEATHER_DESCRIPTIONS)
        ))

    return WeatherForecastResponse(
        field_id=field_id,
        forecasts=forecasts
    )


@app.get("/api/v1/weather/regions/{region_id}/forecast", response_model=WeatherForecastResponse)
async def get_region_forecast(
    region_id: int,
    days: int = Query(7, ge=1, le=14)
):
    """الحصول على توقعات الطقس للمنطقة"""
    import random

    forecasts = []
    base_date = date.today()

    for i in range(days):
        d = base_date + timedelta(days=i)
        mock = generate_mock_weather(region_id, d)

        forecasts.append(WeatherForecast(
            date=d,
            tmax=mock["tmax"],
            tmin=mock["tmin"],
            rain_probability=round(random.uniform(0, 60), 0),
            humidity=mock["humidity"],
            description_ar=random.choice(WEATHER_DESCRIPTIONS)
        ))

    return WeatherForecastResponse(
        region_id=region_id,
        forecasts=forecasts
    )


@app.get("/api/v1/weather/alerts", response_model=List[WeatherAlert])
async def get_weather_alerts(
    region_id: Optional[int] = None,
    severity: Optional[str] = None
):
    """الحصول على تنبيهات الطقس"""
    alerts = [
        WeatherAlert(
            id="alert-001",
            type="heat_wave",
            severity="medium",
            title_ar="موجة حرارة متوقعة",
            description_ar="ارتفاع ملحوظ في درجات الحرارة خلال الأيام القادمة. ينصح بري المزروعات في الصباح الباكر أو المساء.",
            affected_regions=["صنعاء", "مأرب", "الجوف"],
            valid_from=date.today(),
            valid_until=date.today() + timedelta(days=3)
        ),
        WeatherAlert(
            id="alert-002",
            type="rain",
            severity="low",
            title_ar="احتمال أمطار",
            description_ar="توقعات بهطول أمطار خفيفة إلى متوسطة على المرتفعات الغربية.",
            affected_regions=["إب", "تعز", "ذمار"],
            valid_from=date.today() + timedelta(days=1),
            valid_until=date.today() + timedelta(days=2)
        )
    ]

    if region_id:
        region_name = YEMEN_REGIONS.get(region_id, {}).get("name", "")
        alerts = [a for a in alerts if region_name in a.affected_regions]

    if severity:
        alerts = [a for a in alerts if a.severity == severity]

    return alerts


@app.post("/api/v1/weather", response_model=WeatherResponse)
async def create_weather_data(weather: WeatherCreate):
    """إضافة بيانات طقس جديدة"""
    if not SHARED_LIB_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="قاعدة البيانات غير متوفرة"
        )

    try:
        db_manager = DatabaseManager()
        async with db_manager.get_async_session() as session:
            from uuid import uuid4, UUID as UUIDType

            new_weather = WeatherData(
                id=uuid4(),
                tenant_id=uuid4(),  # Should come from auth
                region_id=weather.region_id,
                field_id=UUIDType(weather.field_id) if weather.field_id else None,
                temperature=weather.temperature,
                humidity=weather.humidity,
                rainfall=weather.rainfall,
                wind_speed=weather.wind_speed,
                wind_direction=weather.wind_direction,
                pressure=weather.pressure,
                forecast_date=weather.forecast_date or date.today()
            )

            session.add(new_weather)
            await session.commit()
            await session.refresh(new_weather)

            return WeatherResponse(
                id=str(new_weather.id),
                region_id=new_weather.region_id,
                field_id=str(new_weather.field_id) if new_weather.field_id else None,
                date=new_weather.forecast_date,
                temperature=float(new_weather.temperature),
                humidity=float(new_weather.humidity),
                rainfall=float(new_weather.rainfall) if new_weather.rainfall else 0,
                source="database"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/weather/regions")
async def list_regions():
    """قائمة المناطق المتوفرة"""
    return {
        "regions": [
            {"id": k, "name_ar": v["name"], "type": v["type"]}
            for k, v in YEMEN_REGIONS.items()
        ]
    }


# ============================================================
# Run Application
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
