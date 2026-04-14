#!/bin/bash
set -e

#############################################
# Sahool Field Suite - All-in-One Bootstrap
# Version: 1.1.0 (Fixed)
# - يضيف query-core + weather-core
# - يبني هيكل 3 طبقات
# - ينشئ docker-compose خاص بالـ Field Suite
#############################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Go up one level to find sahool-project
REPO_DIR="$(dirname "$SCRIPT_DIR")"

QUERY_CORE_DIR="$REPO_DIR/multi-repo/query-core"
WEATHER_CORE_DIR="$REPO_DIR/multi-repo/weather-core"

write_file() {
    local file_path=$1
    local content=$2
    mkdir -p "$(dirname "$file_path")"
    echo "$content" > "$file_path"
    echo -e "${CYAN}📄 created:${NC} $file_path"
}

echo_header() {
    echo -e "\n${BLUE}══════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════${NC}\n"
}

echo_success() {
    echo -e "${GREEN}✅${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

#############################################
# 1) التحقق من المتطلبات
#############################################
echo_header "1) Checking requirements"

for cmd in git docker python3; do
  if ! command -v "$cmd" &>/dev/null; then
    echo -e "${RED}❌ $cmd غير مثبت على النظام${NC}"
    exit 1
  else
    echo_success "$cmd موجود"
  fi
done

# Check for docker compose (v2) or docker-compose (v1)
if docker compose version &>/dev/null 2>&1; then
    echo_success "docker compose v2 موجود"
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &>/dev/null; then
    echo_success "docker-compose v1 موجود"
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${RED}❌ docker compose غير مثبت${NC}"
    exit 1
fi

#############################################
# 2) التأكد من وجود المستودع
#############################################
echo_header "2) Ensuring sahool-project exists"

if [ ! -d "$REPO_DIR" ]; then
  echo -e "${RED}❌ المجلد $REPO_DIR غير موجود${NC}"
  exit 1
else
  echo_success "تم العثور على مجلد $REPO_DIR"
fi

#############################################
# 3) إنشاء خدمة query-core (Nano-Service)
#############################################
echo_header "3) Creating query-core nano-service (3 layers)"

# requirements - Fixed: Added pydantic-settings for Pydantic v2
write_file "$QUERY_CORE_DIR/requirements.txt" 'fastapi==0.110.0
uvicorn[standard]==0.29.0
httpx==0.27.0
pydantic==2.7.0
pydantic-settings==2.2.1'

# Dockerfile
write_file "$QUERY_CORE_DIR/Dockerfile" 'FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8100/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]'

# Create __init__.py files
write_file "$QUERY_CORE_DIR/app/__init__.py" ''
write_file "$QUERY_CORE_DIR/app/core/__init__.py" ''
write_file "$QUERY_CORE_DIR/app/services/__init__.py" ''
write_file "$QUERY_CORE_DIR/app/api/__init__.py" ''
write_file "$QUERY_CORE_DIR/app/api/v1/__init__.py" ''

# core/config - Fixed: Using pydantic_settings for Pydantic v2
write_file "$QUERY_CORE_DIR/app/core/config.py" 'from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Query Core Service Configuration"""
    NDVI_SERVICE_URL: str = "http://ndvi-processor:8000"
    WEATHER_SERVICE_URL: str = "http://weather-core:8200"
    GEO_SERVICE_URL: str = "http://geo-core:8000"
    ALERTS_SERVICE_URL: str = "http://alerts-core:8000"
    ENV: str = "development"

    model_config = {
        "env_prefix": "QUERY_CORE_",
        "case_sensitive": False
    }


settings = Settings()'

# core/http_client
write_file "$QUERY_CORE_DIR/app/core/http_client.py" 'import httpx
from contextlib import asynccontextmanager
from typing import AsyncGenerator


@asynccontextmanager
async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Get async HTTP client with proper timeout and error handling"""
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        follow_redirects=True
    ) as client:
        yield client'

# services/field_query_service
write_file "$QUERY_CORE_DIR/app/services/field_query_service.py" 'from datetime import date
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.http_client import get_http_client
import logging

logger = logging.getLogger(__name__)


class FieldQueryService:
    """Service for aggregating field data from multiple microservices"""

    async def build_field_dashboard(
        self,
        field_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Aggregate dashboard data from multiple services:
        - geo-core: Field information
        - ndvi-processor: NDVI timeline
        - weather-core: Weather summary
        - alerts-core: Active alerts
        """
        async with get_http_client() as client:
            # Fetch data from services (with fallbacks)
            field_info = await self._get_field_info(client, field_id)
            ndvi_timeline = await self._get_ndvi_timeline(client, field_id, start_date, end_date)
            weather_summary = await self._get_weather_summary(client, field_id)
            alerts = await self._get_alerts(client, field_id)

            return {
                "field": field_info,
                "period": {"start": str(start_date), "end": str(end_date)},
                "ndvi_timeline": ndvi_timeline,
                "weather_summary": weather_summary,
                "alerts": alerts,
                "metadata": {
                    "generated_at": date.today().isoformat(),
                    "services_status": {
                        "geo": field_info is not None,
                        "ndvi": len(ndvi_timeline) > 0,
                        "weather": weather_summary is not None,
                        "alerts": alerts is not None
                    }
                }
            }

    async def _get_field_info(
        self,
        client,
        field_id: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch field information from geo-core"""
        try:
            resp = await client.get(f"{settings.GEO_SERVICE_URL}/api/v1/fields/{field_id}")
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"Failed to fetch field info: {e}")
        return {"id": field_id, "name": f"Field {field_id}", "status": "offline"}

    async def _get_ndvi_timeline(
        self,
        client,
        field_id: int,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Fetch NDVI timeline from ndvi-processor"""
        try:
            params = {"start": str(start_date), "end": str(end_date)}
            resp = await client.get(
                f"{settings.NDVI_SERVICE_URL}/api/v1/ndvi/{field_id}/timeline",
                params=params
            )
            if resp.status_code == 200:
                return resp.json().get("timeline", [])
        except Exception as e:
            logger.warning(f"Failed to fetch NDVI timeline: {e}")
        return []

    async def _get_weather_summary(
        self,
        client,
        field_id: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch weather summary from weather-core"""
        try:
            resp = await client.get(
                f"{settings.WEATHER_SERVICE_URL}/api/v1/weather/field/{field_id}"
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"Failed to fetch weather: {e}")
        return None

    async def _get_alerts(
        self,
        client,
        field_id: int
    ) -> List[Dict[str, Any]]:
        """Fetch active alerts from alerts-core"""
        try:
            resp = await client.get(
                f"{settings.ALERTS_SERVICE_URL}/api/v1/alerts/field/{field_id}"
            )
            if resp.status_code == 200:
                return resp.json().get("alerts", [])
        except Exception as e:
            logger.warning(f"Failed to fetch alerts: {e}")
        return []'

# api/v1/fields router
write_file "$QUERY_CORE_DIR/app/api/v1/fields.py" 'from fastapi import APIRouter, Query, HTTPException
from datetime import date, timedelta
from app.services.field_query_service import FieldQueryService

router = APIRouter()


@router.get("/fields/{field_id}/dashboard")
async def get_field_dashboard(
    field_id: int,
    days: int = Query(30, ge=7, le=365, description="Number of days for historical data")
):
    """
    Get aggregated dashboard data for a field.
    Combines data from geo-core, ndvi-processor, weather-core, and alerts-core.
    """
    service = FieldQueryService()
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    try:
        return await service.build_field_dashboard(field_id, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build dashboard: {str(e)}")


@router.get("/health/services")
async def check_services_health():
    """Check connectivity to dependent services"""
    from app.core.config import settings
    from app.core.http_client import get_http_client

    services = {
        "geo-core": settings.GEO_SERVICE_URL,
        "ndvi-processor": settings.NDVI_SERVICE_URL,
        "weather-core": settings.WEATHER_SERVICE_URL,
        "alerts-core": settings.ALERTS_SERVICE_URL,
    }

    results = {}
    async with get_http_client() as client:
        for name, url in services.items():
            try:
                resp = await client.get(f"{url}/health", timeout=5.0)
                results[name] = {"status": "up" if resp.status_code == 200 else "degraded"}
            except Exception:
                results[name] = {"status": "down"}

    return {"services": results}'

# main.py
write_file "$QUERY_CORE_DIR/app/main.py" 'from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import fields
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sahool Query Core",
    description="Nano-service for aggregating field data from multiple microservices",
    version="1.1.0",
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

# Include routers
app.include_router(fields.router, prefix="/api/v1/query", tags=["Query"])


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "query-core", "version": "1.1.0"}


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Sahool Query Core",
        "version": "1.1.0",
        "docs": "/docs",
        "health": "/health"
    }'

#############################################
# 4) إنشاء خدمة weather-core (Nano-Service)
#############################################
echo_header "4) Creating weather-core nano-service (3 layers)"

# requirements - Fixed: Added pydantic-settings
write_file "$WEATHER_CORE_DIR/requirements.txt" 'fastapi==0.110.0
uvicorn[standard]==0.29.0
httpx==0.27.0
pydantic==2.7.0
pydantic-settings==2.2.1'

write_file "$WEATHER_CORE_DIR/Dockerfile" 'FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8200

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8200/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8200"]'

# Create __init__.py files
write_file "$WEATHER_CORE_DIR/app/__init__.py" ''
write_file "$WEATHER_CORE_DIR/app/core/__init__.py" ''
write_file "$WEATHER_CORE_DIR/app/services/__init__.py" ''
write_file "$WEATHER_CORE_DIR/app/repositories/__init__.py" ''
write_file "$WEATHER_CORE_DIR/app/api/__init__.py" ''
write_file "$WEATHER_CORE_DIR/app/api/v1/__init__.py" ''

# core/config - Fixed: Using pydantic_settings
write_file "$WEATHER_CORE_DIR/app/core/config.py" 'from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Weather Core Service Configuration"""
    OPENWEATHER_API_KEY: str = "change_me"
    GEO_SERVICE_URL: str = "http://geo-core:8000"
    CACHE_TTL_SECONDS: int = 300  # 5 minutes

    model_config = {
        "env_prefix": "WEATHER_CORE_",
        "case_sensitive": False
    }


settings = Settings()'

# repositories/weather_provider
write_file "$WEATHER_CORE_DIR/app/repositories/weather_provider.py" 'from typing import Dict, Any, Optional
import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class WeatherProvider:
    """Repository for fetching weather data from OpenWeatherMap API"""

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    async def get_current_by_coords(
        self,
        lat: float,
        lon: float
    ) -> Optional[Dict[str, Any]]:
        """Get current weather by coordinates"""
        params = {
            "lat": lat,
            "lon": lon,
            "appid": settings.OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "ar",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.BASE_URL}/weather", params=params)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")
            return None

    async def get_forecast_by_coords(
        self,
        lat: float,
        lon: float,
        days: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Get weather forecast by coordinates"""
        params = {
            "lat": lat,
            "lon": lon,
            "appid": settings.OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "ar",
            "cnt": days * 8,  # 3-hour intervals
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.BASE_URL}/forecast", params=params)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"Forecast fetch failed: {e}")
            return None'

# services/weather_service
write_file "$WEATHER_CORE_DIR/app/services/weather_service.py" 'from typing import Dict, Any, Optional, List
from app.repositories.weather_provider import WeatherProvider
import logging

logger = logging.getLogger(__name__)


class WeatherService:
    """Service layer for weather operations"""

    def __init__(self):
        self.provider = WeatherProvider()

    async def get_current_for_coords(
        self,
        lat: float,
        lon: float
    ) -> Dict[str, Any]:
        """Get current weather with simplified response"""
        data = await self.provider.get_current_by_coords(lat, lon)

        if not data:
            return {
                "lat": lat,
                "lon": lon,
                "error": "Unable to fetch weather data",
                "available": False
            }

        main = data.get("main", {})
        wind = data.get("wind", {})
        weather = (data.get("weather") or [{}])[0]

        return {
            "lat": lat,
            "lon": lon,
            "available": True,
            "current": {
                "temp": main.get("temp"),
                "feels_like": main.get("feels_like"),
                "humidity": main.get("humidity"),
                "pressure": main.get("pressure"),
                "temp_min": main.get("temp_min"),
                "temp_max": main.get("temp_max"),
            },
            "wind": {
                "speed": wind.get("speed"),
                "deg": wind.get("deg"),
                "gust": wind.get("gust"),
            },
            "condition": {
                "main": weather.get("main"),
                "description": weather.get("description"),
                "icon": weather.get("icon"),
            },
            "location": data.get("name", "Unknown"),
            "timestamp": data.get("dt"),
        }

    async def get_forecast_for_coords(
        self,
        lat: float,
        lon: float,
        days: int = 5
    ) -> Dict[str, Any]:
        """Get weather forecast with daily aggregation"""
        data = await self.provider.get_forecast_by_coords(lat, lon, days)

        if not data:
            return {
                "lat": lat,
                "lon": lon,
                "error": "Unable to fetch forecast",
                "available": False,
                "forecast": []
            }

        # Process forecast data
        forecast_list = data.get("list", [])
        daily_forecast: List[Dict[str, Any]] = []

        # Simple daily aggregation (can be improved)
        for item in forecast_list[::8]:  # One entry per day
            main = item.get("main", {})
            weather = (item.get("weather") or [{}])[0]
            daily_forecast.append({
                "date": item.get("dt_txt", "")[:10],
                "temp": main.get("temp"),
                "temp_min": main.get("temp_min"),
                "temp_max": main.get("temp_max"),
                "humidity": main.get("humidity"),
                "condition": weather.get("description"),
                "icon": weather.get("icon"),
            })

        return {
            "lat": lat,
            "lon": lon,
            "available": True,
            "location": data.get("city", {}).get("name", "Unknown"),
            "forecast": daily_forecast[:days]
        }

    async def get_agricultural_advisory(
        self,
        lat: float,
        lon: float
    ) -> Dict[str, Any]:
        """Get agricultural weather advisory"""
        current = await self.get_current_for_coords(lat, lon)

        if not current.get("available"):
            return {"available": False, "advisories": []}

        advisories: List[str] = []
        temp = current.get("current", {}).get("temp", 25)
        humidity = current.get("current", {}).get("humidity", 50)
        wind_speed = current.get("wind", {}).get("speed", 0)

        # Generate advisories based on conditions
        if temp > 35:
            advisories.append("درجة الحرارة مرتفعة - يُنصح بالري في الصباح الباكر أو المساء")
        elif temp < 10:
            advisories.append("درجة الحرارة منخفضة - احرص على حماية المحاصيل الحساسة")

        if humidity > 80:
            advisories.append("رطوبة عالية - خطر الإصابة بالأمراض الفطرية")
        elif humidity < 30:
            advisories.append("رطوبة منخفضة - زيادة احتياجات الري")

        if wind_speed > 10:
            advisories.append("رياح قوية - تجنب رش المبيدات")

        return {
            "available": True,
            "conditions": current,
            "advisories": advisories,
            "risk_level": "high" if len(advisories) > 2 else "medium" if advisories else "low"
        }'

# api/v1/weather router
write_file "$WEATHER_CORE_DIR/app/api/v1/weather.py" 'from fastapi import APIRouter, Query, HTTPException
from app.services.weather_service import WeatherService

router = APIRouter()


@router.get("/weather/current")
async def get_current_weather(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """Get current weather by coordinates"""
    service = WeatherService()
    return await service.get_current_for_coords(lat, lon)


@router.get("/weather/forecast")
async def get_weather_forecast(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    days: int = Query(5, ge=1, le=7, description="Number of forecast days"),
):
    """Get weather forecast by coordinates"""
    service = WeatherService()
    return await service.get_forecast_for_coords(lat, lon, days)


@router.get("/weather/advisory")
async def get_agricultural_advisory(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Get agricultural weather advisory for given location"""
    service = WeatherService()
    return await service.get_agricultural_advisory(lat, lon)


@router.get("/weather/field/{field_id}")
async def get_weather_for_field(field_id: int):
    """
    Get weather for a specific field.
    Note: Requires geo-core integration to get field coordinates.
    """
    # TODO: Integrate with geo-core to get field centroid
    # For now, return a placeholder
    return {
        "field_id": field_id,
        "message": "Integration with geo-core pending",
        "available": False
    }'

# main.py
write_file "$WEATHER_CORE_DIR/app/main.py" 'from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import weather
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sahool Weather Core",
    description="Nano-service for weather data and agricultural advisories",
    version="1.1.0",
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

# Include routers
app.include_router(weather.router, prefix="/api/v1", tags=["Weather"])


@app.get("/health")
async def health():
    """Health check endpoint"""
    from app.core.config import settings
    api_configured = settings.OPENWEATHER_API_KEY != "change_me"
    return {
        "status": "ok" if api_configured else "degraded",
        "service": "weather-core",
        "version": "1.1.0",
        "api_configured": api_configured
    }


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Sahool Weather Core",
        "version": "1.1.0",
        "docs": "/docs",
        "health": "/health"
    }'

#############################################
# 5) إضافة docker-compose خاص بالـ Field Suite
#############################################
echo_header "5) Creating docker-compose.sahool-field-suite.yml"

COMPOSE_FILE="$REPO_DIR/docker-compose.sahool-field-suite.yml"

write_file "$COMPOSE_FILE" 'version: "3.9"

# Sahool Field Suite - Microservices Compose
# Ports: 8100 (query-core), 8200 (weather-core)

services:
  query-core:
    build:
      context: ./multi-repo/query-core
    container_name: sahool_query_core
    environment:
      - QUERY_CORE_NDVI_SERVICE_URL=http://ndvi-processor:8000
      - QUERY_CORE_WEATHER_SERVICE_URL=http://weather-core:8200
      - QUERY_CORE_GEO_SERVICE_URL=http://geo-core:8000
      - QUERY_CORE_ALERTS_SERVICE_URL=http://alerts-core:8000
    ports:
      - "127.0.0.1:8100:8100"
    networks:
      - sahool_net
    restart: unless-stopped
    depends_on:
      - weather-core
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8100/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  weather-core:
    build:
      context: ./multi-repo/weather-core
    container_name: sahool_weather_core
    environment:
      - WEATHER_CORE_OPENWEATHER_API_KEY=${OPENWEATHER_API_KEY:-change_me}
      - WEATHER_CORE_GEO_SERVICE_URL=http://geo-core:8000
    ports:
      - "127.0.0.1:8200:8200"
    networks:
      - sahool_net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8200/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  sahool_net:
    driver: bridge
    name: sahool_network
'

#############################################
# 6) إنشاء ملف .env.example
#############################################
echo_header "6) Creating .env.example"

write_file "$REPO_DIR/.env.field-suite.example" '# Sahool Field Suite Environment Variables

# OpenWeatherMap API Key (Get from https://openweathermap.org/api)
OPENWEATHER_API_KEY=your_api_key_here

# Service URLs (for local development)
QUERY_CORE_GEO_SERVICE_URL=http://localhost:8005
QUERY_CORE_NDVI_SERVICE_URL=http://localhost:8006
QUERY_CORE_WEATHER_SERVICE_URL=http://localhost:8200
QUERY_CORE_ALERTS_SERVICE_URL=http://localhost:8004
'

#############################################
# 7) تعليمات تشغيل سريعة
#############################################
echo_header "7) Done — How to run"

echo -e "${GREEN}✅ تم إنشاء query-core + weather-core + docker-compose.sahool-field-suite.yml${NC}"
echo
echo -e "${YELLOW}📌 للتشغيل:${NC}"
echo -e "  cd $REPO_DIR"
echo -e "  cp .env.field-suite.example .env.field-suite"
echo -e "  # Edit .env.field-suite with your OPENWEATHER_API_KEY"
echo -e "  $DOCKER_COMPOSE -f docker-compose.sahool-field-suite.yml --env-file .env.field-suite build"
echo -e "  $DOCKER_COMPOSE -f docker-compose.sahool-field-suite.yml --env-file .env.field-suite up -d"
echo
echo -e "${YELLOW}🌐 نقاط الدخول:${NC}"
echo -e "  Query Core:   http://localhost:8100"
echo -e "  Weather Core: http://localhost:8200"
echo -e "  Query Docs:   http://localhost:8100/docs"
echo -e "  Weather Docs: http://localhost:8200/docs"
echo
echo -e "${YELLOW}🧪 اختبار سريع:${NC}"
echo -e "  curl http://localhost:8100/health"
echo -e "  curl http://localhost:8200/health"
echo -e "  curl 'http://localhost:8200/api/v1/weather/current?lat=24.7136&lon=46.6753'"
echo
echo -e "${GREEN}🎉 المعمارية جاهزة: Query Core + Weather Core${NC}"

exit 0
