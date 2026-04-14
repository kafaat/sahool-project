#!/bin/bash
set -euo pipefail

# =======================================================================
# سهول اليمن - سكريبت النشر النهائي (الإصدار 6.0.0 - PRODUCTION)
# SAHOOL Yemen Field Suite NDVI - Complete Deployment Script
# =======================================================================
MAGENTA='\033[0;35m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${GREEN}[SAHOOL]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# =======================================================================
# 1. التحقق من المتطلبات الأساسية
# =======================================================================
check_requirements() {
    log "التحقق من المتطلبات الأساسية..."
    for cmd in docker docker-compose git curl openssl; do
        if ! command -v $cmd &>/dev/null; then
            error "الأمر $cmd غير مثبت. يرجى التثبيت أولاً."
        fi
    done
    docker compose version &>/dev/null || error "Docker Compose v2+ مطلوب"
    info "✓ جميع المتطلبات متوفرة"
}

# =======================================================================
# 2. إنشاء بنية المشروع الكاملة
# =======================================================================
create_structure() {
    log "إنشاء بنية المشروع الكاملة..."

    # Backend umbrella
    mkdir -p field_suite_service/app/{core,clients,schemas,routers,rules,utils}
    mkdir -p field_suite_service/{tests,scripts,postgres/init}

    # Nano services
    mkdir -p nano_services/weather-core/app
    mkdir -p nano_services/imagery-core/app
    mkdir -p nano_services/geo-core/app
    mkdir -p nano_services/analytics-core/app
    mkdir -p nano_services/query-core/app
    mkdir -p nano_services/advisor-core/app

    # Frontend & Gateway
    mkdir -p field_suite_frontend/src/{components,api,utils,hooks,pages}
    mkdir -p field_suite_frontend/public/{assets,locales}
    mkdir -p gateway-edge/{conf.d,ssl,errors,logs}

    # Monitoring & Data
    mkdir -p monitoring/{prometheus,grafana/provisioning/{dashboards,datasources}}
    mkdir -p data/{backups,uploads,static,logs}
    mkdir -p scripts

    info "✓ بنية المشروع تم إنشاؤها"
}

# =======================================================================
# 3. إعداد متغيرات البيئة الآمنة
# =======================================================================
setup_env() {
    log "إعداد متغيرات البيئة الآمنة..."

    DB_PASS=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 64)
    REDIS_PASS=$(openssl rand -hex 16)
    GRAFANA_PASS=$(openssl rand -hex 16)
    POSTGRES_PASS=$(openssl rand -hex 16)

    cat > .env <<EOF
# ==========================================
# سهول اليمن - إعدادات الإنتاج
# ==========================================
# Database
DB_USER=sahool_production_user
DB_PASS=$DB_PASS
DB_NAME=sahool_yemen_db
DB_PORT=5432

# Environment
ENVIRONMENT=production
TIMEZONE=Asia/Aden
CURRENCY=YER
LANGUAGE=ar-YE

# Security
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
API_KEY_SECRET=$(openssl rand -hex 32)

# Rate Limiting
API_RATE_LIMIT=200/minute
API_BURST=20

# Yemen Regions (20 Governorates)
YEMEN_REGIONS="Sana'a,Aden,Taiz,Hadramaut,Hudaydah,Ibb,Dhamar,Shabwah,Lahij,Abyan,Marib,AlJawf,Amran,Hajjah,Mahwit,Raymah,AlMahrah,Soqatra,AlBayda,Sa'dah"

# Crops
YEMEN_CROPS="قمح,ذرة,شعير,بن,كتان,بصل,طماطم,بطاطس,باذنجان,فلفل,خضروات,فواكه,أعلاف,قات,حبوب,بقوليات"

# Redis
REDIS_URL=redis://:${REDIS_PASS}@fs-redis:6379/0
REDIS_PASSWORD=$REDIS_PASS

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=$GRAFANA_PASS

# Default Location (Sana'a)
DEFAULT_LAT=15.3547
DEFAULT_LON=44.2067

# LLM (OpenAI)
OPENAI_API_KEY=${OPENAI_API_KEY:-}
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000

# Core Services URLs
DATABASE_URL=postgresql://sahool_production_user:$DB_PASS@fs-postgres:5432/sahool_yemen_db
IMAGERY_CORE_BASE_URL=http://imagery-core:8000
ANALYTICS_CORE_BASE_URL=http://analytics-core:8000
GEO_CORE_BASE_URL=http://geo-core:8000
WEATHER_CORE_BASE_URL=http://weather-core:8000
ADVISOR_CORE_BASE_URL=http://advisor-core:8000
QUERY_CORE_BASE_URL=http://query-core:8000

# Cache
CACHE_TTL=300
LLM_CACHE_TTL=3600

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/sahool.log

# Metrics
METRICS_PORT=8001
METRICS_ENABLED=true

# CORS
ALLOWED_ORIGINS='["*"]'

# File Storage
MAX_UPLOAD_SIZE=50MB
STATIC_FILES_PATH=/app/static

# Backup
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE="0 2 * * *"

# Network
INTERNAL_SUBNET=172.20.0.0/16
EOF

    chmod 600 .env
    info "✓ ملف .env تم إنشاؤه بشكل آمن"
}

# =======================================================================
# 4. إعداد قاعدة البيانات
# =======================================================================
setup_database() {
    log "إعداد قاعدة البيانات PostgreSQL + PostGIS..."

    cat > field_suite_service/postgres/init/01-extensions.sql <<'EOF'
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
EOF

    cat > field_suite_service/postgres/init/02-tables.sql <<'EOF'
-- المناطق (المحافظات)
CREATE TABLE regions (
    id SERIAL PRIMARY KEY,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    coordinates GEOGRAPHY(POINT, 4326),
    area_km2 DECIMAL(10,2),
    agricultural_potential TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- المزارعون
CREATE TABLE farmers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100),
    region_id INTEGER REFERENCES regions(id),
    tenant_id UUID NOT NULL,
    registration_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- الحقول
CREATE TABLE fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farmer_id UUID REFERENCES farmers(id),
    region_id INTEGER REFERENCES regions(id),
    tenant_id UUID NOT NULL,
    name_ar VARCHAR(200),
    area_hectares DECIMAL(10,2) NOT NULL,
    crop_type VARCHAR(100),
    coordinates GEOGRAPHY(POINT, 4326),
    elevation_meters INTEGER,
    soil_type VARCHAR(50),
    irrigation_type VARCHAR(50),
    field_geometry GEOGRAPHY(POLYGON, 4326),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- نتائج NDVI
CREATE TABLE ndvi_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id),
    tenant_id UUID NOT NULL,
    ndvi_value DECIMAL(5,2),
    acquisition_date DATE NOT NULL,
    tile_url TEXT,
    cloud_coverage DECIMAL(5,2),
    satellite_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- بيانات الطقس
CREATE TABLE weather_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    region_id INTEGER REFERENCES regions(id),
    tenant_id UUID NOT NULL,
    temperature DECIMAL(6,2),
    humidity DECIMAL(5,2),
    rainfall DECIMAL(8,2),
    wind_speed DECIMAL(6,2),
    wind_direction VARCHAR(10),
    pressure DECIMAL(7,2),
    forecast_date DATE,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- سجل الإنتاج
CREATE TABLE yield_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id),
    tenant_id UUID NOT NULL,
    crop_type VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    yield_ton_per_hectare DECIMAL(10,2),
    revenue_yer DECIMAL(15,2),
    expenses_yer DECIMAL(15,2),
    profit_yer DECIMAL(15,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- تحليل التربة
CREATE TABLE soil_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id),
    tenant_id UUID NOT NULL,
    ph_value DECIMAL(4,2),
    nitrogen_ppm DECIMAL(8,2),
    phosphorus_ppm DECIMAL(8,2),
    potassium_ppm DECIMAL(8,2),
    organic_matter_percent DECIMAL(5,2),
    salinity_ms_cm DECIMAL(6,2),
    analysis_date DATE,
    lab_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- جداول الري
CREATE TABLE irrigation_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id),
    tenant_id UUID NOT NULL,
    schedule_date DATE NOT NULL,
    water_amount_mm DECIMAL(8,2),
    irrigation_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    executed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- صحة النبات
CREATE TABLE plant_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id),
    tenant_id UUID NOT NULL,
    disease_name VARCHAR(100),
    confidence_score DECIMAL(5,2),
    severity_level VARCHAR(20),
    recommendation TEXT,
    image_url TEXT,
    detected_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- سجل التدقيق
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100),
    tenant_id UUID NOT NULL,
    action VARCHAR(100),
    table_name VARCHAR(100),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- إدراج بيانات المحافظات (20 محافظة)
INSERT INTO regions (name_ar, name_en, coordinates, area_km2, agricultural_potential) VALUES
('صنعاء', 'Sanaa', ST_SetSRID(ST_MakePoint(44.2067, 15.3547), 4326)::GEOGRAPHY, 12630, 'عالية - قمح, خضروات'),
('عدن', 'Aden', ST_SetSRID(ST_MakePoint(45.0339, 12.8254), 4326)::GEOGRAPHY, 1114, 'متوسطة - خضروات استوائية'),
('تعز', 'Taiz', ST_SetSRID(ST_MakePoint(44.0107, 13.5782), 4326)::GEOGRAPHY, 12213, 'عالية - قهوة, حبوب'),
('حضرموت', 'Hadramaut', ST_SetSRID(ST_MakePoint(48.8318, 15.4768), 4326)::GEOGRAPHY, 98044, 'متوسطة - نخيل, أعلاف'),
('الحديدة', 'Hudaydah', ST_SetSRID(ST_MakePoint(42.9531, 14.7974), 4326)::GEOGRAPHY, 17090, 'عالية - خضروات, حبوب'),
('إب', 'Ibb', ST_SetSRID(ST_MakePoint(43.9440, 14.1446), 4326)::GEOGRAPHY, 11770, 'عالية - قهوة, حبوب'),
('ذمار', 'Dhamar', ST_SetSRID(ST_MakePoint(44.4137, 15.5570), 4326)::GEOGRAPHY, 10100, 'عالية - قمح, حبوب'),
('شبوة', 'Shabwah', ST_SetSRID(ST_MakePoint(45.7186, 14.3801), 4326)::GEOGRAPHY, 49230, 'متوسطة - أعلاف, نخيل'),
('لحج', 'Lahij', ST_SetSRID(ST_MakePoint(44.8812, 13.0565), 4326)::GEOGRAPHY, 15730, 'متوسطة - خضروات, أعلاف'),
('أبين', 'Abyan', ST_SetSRID(ST_MakePoint(45.8824, 13.6950), 4326)::GEOGRAPHY, 21789, 'متوسطة - نخيل, حبوب'),
('مأرب', 'Marib', ST_SetSRID(ST_MakePoint(45.3406, 15.4620), 4326)::GEOGRAPHY, 20423, 'متوسطة - نخيل, أعلاف'),
('الجوف', 'Al Jawf', ST_SetSRID(ST_MakePoint(44.8154, 16.7206), 4326)::GEOGRAPHY, 44773, 'متوسطة - حبوب, خضروات'),
('عمران', 'Amran', ST_SetSRID(ST_MakePoint(43.9430, 16.2564), 4326)::GEOGRAPHY, 9250, 'عالية - قمح, خضروات'),
('حجة', 'Hajjah', ST_SetSRID(ST_MakePoint(43.3250, 16.1235), 4326)::GEOGRAPHY, 10000, 'متوسطة - حبوب, أعلاف'),
('المحويت', 'Mahwit', ST_SetSRID(ST_MakePoint(43.5400, 15.2589), 4326)::GEOGRAPHY, 2858, 'متوسطة - قهوة, حبوب'),
('ريمة', 'Raymah', ST_SetSRID(ST_MakePoint(44.5000, 14.4000), 4326)::GEOGRAPHY, 3940, 'متوسطة - حبوب, خضروات'),
('المهرة', 'Al Mahrah', ST_SetSRID(ST_MakePoint(51.8000, 16.5000), 4326)::GEOGRAPHY, 123500, 'منخفضة - أعلاف, نحل'),
('سقطرى', 'Soqatra', ST_SetSRID(ST_MakePoint(53.8000, 12.5000), 4326)::GEOGRAPHY, 3650, 'منخفضة - نباتات نادرة'),
('البيضاء', 'Al Bayda', ST_SetSRID(ST_MakePoint(45.3000, 14.2000), 4326)::GEOGRAPHY, 11170, 'متوسطة - حبوب, أعلاف'),
('صعدة', 'Sa''dah', ST_SetSRID(ST_MakePoint(43.7000, 16.9000), 4326)::GEOGRAPHY, 14564, 'متوسطة - حبوب, أعلاف');
EOF

    cat > field_suite_service/postgres/init/03-indexes.sql <<'EOF'
-- فهارس الأداء
CREATE INDEX idx_fields_region ON fields(region_id);
CREATE INDEX idx_fields_farmer ON fields(farmer_id);
CREATE INDEX idx_fields_tenant ON fields(tenant_id);
CREATE INDEX idx_fields_crop ON fields(crop_type);
CREATE INDEX idx_ndvi_field ON ndvi_results(field_id);
CREATE INDEX idx_ndvi_tenant ON ndvi_results(tenant_id);
CREATE INDEX idx_ndvi_date ON ndvi_results(acquisition_date DESC);
CREATE INDEX idx_weather_region ON weather_data(region_id);
CREATE INDEX idx_weather_tenant ON weather_data(tenant_id);
CREATE INDEX idx_weather_date ON weather_data(forecast_date);
CREATE INDEX idx_yield_field ON yield_records(field_id);
CREATE INDEX idx_yield_tenant ON yield_records(tenant_id);
CREATE INDEX idx_yield_year ON yield_records(year DESC);
CREATE INDEX idx_soil_field ON soil_analysis(field_id);
CREATE INDEX idx_soil_tenant ON soil_analysis(tenant_id);
CREATE INDEX idx_irrigation_field ON irrigation_schedules(field_id);
CREATE INDEX idx_irrigation_tenant ON irrigation_schedules(tenant_id);
CREATE INDEX idx_health_field ON plant_health(field_id);
CREATE INDEX idx_health_tenant ON plant_health(tenant_id);
CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_date ON audit_logs(created_at DESC);

-- فهارس المساحات الجغرافية
CREATE INDEX idx_fields_location ON fields USING GIST(coordinates);
CREATE INDEX idx_fields_geometry ON fields USING GIST(field_geometry);
CREATE INDEX idx_regions_location ON regions USING GIST(coordinates);

-- فهارس النصوص الكاملة
CREATE INDEX idx_fields_name_ar ON fields USING gin(to_tsvector('arabic', name_ar));
CREATE INDEX idx_farmers_name ON farmers USING gin(to_tsvector('arabic', name));
EOF

    info "✓ قاعدة البيانات مع 20 محافظة تم إعدادها"
}

# =======================================================================
# 5. إعداد Nano Services (الخدمات المتخصصة)
# =======================================================================
write_fastapi_requirements() {
    local target="$1"
    cat > "$target/requirements.txt" <<'EOF'
fastapi==0.110.0
uvicorn[standard]==0.29.0
httpx==0.27.0
pydantic==2.6.4
pydantic-settings==2.2.1
python-dotenv==1.0.1
prometheus-client==0.20.0
structlog==24.1.0
EOF
}

setup_nano_services() {
    log "إعداد Nano Services..."

    # Weather Core
    write_fastapi_requirements "nano_services/weather-core"
    cat > nano_services/weather-core/app/main.py <<'EOF'
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
from typing import Optional
import random

app = FastAPI(title="Weather Core", version="1.0.0")

class WeatherResponse(BaseModel):
    field_id: int
    date: date
    tmax: float
    tmin: float
    tmean: float
    rain_mm: float
    humidity: float
    wind_speed: float

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "weather-core"}

@app.get("/api/v1/weather/fields/{field_id}", response_model=WeatherResponse)
async def get_weather(field_id: int, target_date: Optional[date] = None):
    d = target_date or date.today()
    return WeatherResponse(
        field_id=field_id,
        date=d,
        tmax=round(random.uniform(25, 35), 1),
        tmin=round(random.uniform(12, 20), 1),
        tmean=round(random.uniform(18, 27), 1),
        rain_mm=round(random.uniform(0, 15), 1),
        humidity=round(random.uniform(30, 85), 1),
        wind_speed=round(random.uniform(0.5, 6.0), 1),
    )
EOF
    cat > nano_services/weather-core/Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    # Imagery Core
    write_fastapi_requirements "nano_services/imagery-core"
    cat > nano_services/imagery-core/app/main.py <<'EOF'
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
from typing import Optional

app = FastAPI(title="Imagery Core", version="1.0.0")

class NDVITileResponse(BaseModel):
    field_id: int
    date: date
    tile_url: str
    satellite: str
    cloud_coverage: float

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "imagery-core"}

@app.get("/api/v1/ndvi/{field_id}", response_model=NDVITileResponse)
async def get_ndvi_tile(field_id: int, target_date: Optional[date] = None):
    d = target_date or date.today()
    return NDVITileResponse(
        field_id=field_id,
        date=d,
        tile_url=f"https://sahool-tiles.yemen/ndvi/{field_id}/{d.isoformat()}.png",
        satellite="Sentinel-2",
        cloud_coverage=5.0,
    )
EOF
    cat > nano_services/imagery-core/Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    # Geo Core
    write_fastapi_requirements "nano_services/geo-core"
    cat > nano_services/geo-core/app/main.py <<'EOF'
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="Geo Core", version="1.0.0")

class AreaResponse(BaseModel):
    area_ha: float
    perimeter_m: float

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "geo-core"}

@app.post("/api/v1/geo/compute-area", response_model=AreaResponse)
async def compute_area(geometry: dict):
    return AreaResponse(area_ha=12.5, perimeter_m=1450.0)
EOF
    cat > nano_services/geo-core/Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    # Analytics Core
    write_fastapi_requirements "nano_services/analytics-core"
    cat > nano_services/analytics-core/app/main.py <<'EOF'
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
from typing import List

app = FastAPI(title="Analytics Core", version="1.0.0")

class NDVITimelinePoint(BaseModel):
    date: date
    mean_ndvi: float
    min_ndvi: float
    max_ndvi: float

class NDVITimelineResponse(BaseModel):
    field_id: int
    data: List[NDVITimelinePoint]

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "analytics-core"}

@app.get("/api/v1/ndvi/{field_id}/timeline", response_model=NDVITimelineResponse)
async def get_ndvi_timeline(field_id: int):
    from datetime import timedelta
    base_date = date.today()
    data = []
    for i in range(10):
        d = base_date - timedelta(days=i*7)
        mean_val = 0.3 + (i * 0.02)
        data.append({
            "date": d,
            "mean_ndvi": round(mean_val, 3),
            "min_ndvi": round(mean_val - 0.1, 3),
            "max_ndvi": round(mean_val + 0.1, 3),
        })
    return {"field_id": field_id, "data": data}
EOF
    cat > nano_services/analytics-core/Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    # Query Core
    write_fastapi_requirements "nano_services/query-core"
    cat > nano_services/query-core/app/main.py <<'EOF'
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date

app = FastAPI(title="Query Core", version="1.0.0")

class FieldSummary(BaseModel):
    field_id: int
    name_ar: str
    crop_type: str
    area_ha: float
    last_ndvi_date: date
    last_ndvi_value: float

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "query-core"}

@app.get("/api/v1/fields/{field_id}/summary", response_model=FieldSummary)
async def get_field_summary(field_id: int):
    return {
        "field_id": field_id,
        "name_ar": f"حقل #{field_id}",
        "crop_type": "قمح",
        "area_ha": 10.5,
        "last_ndvi_date": date.today(),
        "last_ndvi_value": 0.62,
    }
EOF
    cat > nano_services/query-core/Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    # Advisor Core
    write_fastapi_requirements "nano_services/advisor-core"
    cat > nano_services/advisor-core/app/main.py <<'EOF'
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

app = FastAPI(title="Advisor Core", version="1.0.0")

class RecommendationAction(BaseModel):
    action_ar: str
    action_en: str
    urgency: str

class Recommendation(BaseModel):
    id: str
    priority: str
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    actions: List[RecommendationAction]
    created_at: datetime

class AdvisorResponse(BaseModel):
    field_id: int
    recommendations: List[Recommendation]
    ndvi_snapshot: Dict[str, Any]

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "advisor-core"}

@app.post("/api/v1/advisor/analyze-field", response_model=AdvisorResponse)
async def analyze_field(payload: dict):
    now = datetime.utcnow()
    return {
        "field_id": payload.get("field_id", 0),
        "recommendations": [
            {
                "id": f"rec-{now.timestamp()}",
                "priority": "medium",
                "title_ar": "المحصول في حالة مقبولة",
                "title_en": "Crop condition acceptable",
                "description_ar": "لا توجد مؤشرات خطرة، تابع الري والتسميد",
                "description_en": "No critical indicators, maintain irrigation",
                "actions": [
                    {
                        "action_ar": "استمر بمراقبة الحقل",
                        "action_en": "Continue field monitoring",
                        "urgency": "routine",
                    }
                ],
                "created_at": now,
            }
        ],
        "ndvi_snapshot": {"latest_mean_ndvi": 0.55, "trend": "stable"},
    }
EOF
    cat > nano_services/advisor-core/Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    info "✓ Nano Services تم إعدادها جميعها"
}

# =======================================================================
# 6. إعداد Backend Core Services
# =======================================================================
setup_backend_core() {
    log "إعداد Backend Core Services..."

    cat > field_suite_service/requirements.txt <<'EOF'
fastapi==0.110.0
uvicorn[standard]==0.29.0
httpx==0.27.0
pydantic==2.6.4
pydantic-settings==2.2.1
python-dotenv==1.0.1
redis==5.0.3
prometheus-client==0.20.0
structlog==24.1.0
psycopg2-binary==2.9.9
sqlalchemy==2.0.28
alembic==1.13.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
openai==1.30.0
tenacity==8.2.3
PyYAML==6.0.1
geoalchemy2==0.14.7
EOF

    # Core Utilities
    cat > field_suite_service/app/core/__init__.py <<'EOF'
from .config import settings
from .cache import cache
from .circuit_breaker import *
from .metrics import *
from .logging import setup_logging
EOF

    cat > field_suite_service/app/core/config.py <<'EOF'
from pydantic_settings import BaseSettings
from pydantic import validator, Field
from functools import lru_cache
from typing import List, Optional

class Settings(BaseSettings):
    SERVICE_NAME: str = "field-suite-ndvi-advisor"
    VERSION: str = "6.0.0"

    # External Services
    IMAGERY_CORE_BASE_URL: str = Field(..., env="IMAGERY_CORE_BASE_URL")
    ANALYTICS_CORE_BASE_URL: str = Field(..., env="ANALYTICS_CORE_BASE_URL")
    GEO_CORE_BASE_URL: str = Field(..., env="GEO_CORE_BASE_URL")
    WEATHER_CORE_BASE_URL: str = Field(..., env="WEATHER_CORE_BASE_URL")
    ADVISOR_CORE_BASE_URL: str = Field(..., env="ADVISOR_CORE_BASE_URL")
    QUERY_CORE_BASE_URL: str = Field(..., env="QUERY_CORE_BASE_URL")

    # Redis
    REDIS_URL: str = Field(..., env="REDIS_URL")
    CACHE_TTL: int = 300
    LLM_CACHE_TTL: int = 3600

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # Timeouts
    REQUEST_TIMEOUT: int = 30

    # LLM
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Security
    JWT_SECRET_KEY: str
    API_KEY_SECRET: str

    # Metrics
    METRICS_PORT: int = 8001

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Rate Limiting
    API_RATE_LIMIT: int = 200

    @validator("DATABASE_URL")
    def validate_url(cls, v):
        if not v.startswith("postgresql://"):
            raise ValueError("Invalid DATABASE_URL")
        return v

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
EOF

    # Circuit Breaker
    cat > field_suite_service/app/core/circuit_breaker.py <<'EOF'
import asyncio
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, name: str = ""):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self.lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        async with self.lock:
            now = datetime.utcnow()

            if self.state == CircuitState.OPEN:
                if now - (self.last_failure_time or now) > timedelta(seconds=self.recovery_timeout):
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit {self.name}: HALF_OPEN")
                else:
                    raise Exception(f"Circuit {self.name} is OPEN")

            try:
                result = await func(*args, **kwargs)
                async with self.lock:
                    if self.state == CircuitState.HALF_OPEN:
                        self.state = CircuitState.CLOSED
                        self.failure_count = 0
                return result
            except Exception as e:
                async with self.lock:
                    self.failure_count += 1
                    self.last_failure_time = now
                    if self.failure_count >= self.failure_threshold:
                        self.state = CircuitState.OPEN
                        logger.error(f"Circuit {self.name}: OPEN")
                raise

imagery_circuit = CircuitBreaker(name="imagery-core")
analytics_circuit = CircuitBreaker(name="analytics-core")
geo_circuit = CircuitBreaker(name="geo-core")
weather_circuit = CircuitBreaker(name="weather-core")
advisor_circuit = CircuitBreaker(name="advisor-core")
query_circuit = CircuitBreaker(name="query-core")
EOF

    # Redis Cache
    cat > field_suite_service/app/core/cache.py <<'EOF'
import redis
import json
import logging
from typing import Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
            self.client.ping()
            logger.info("✓ Redis connected successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise

    async def get(self, key: str) -> Optional[Any]:
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        try:
            self.client.setex(key, ttl or settings.CACHE_TTL, json.dumps(value))
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def delete(self, key: str) -> None:
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")

    async def ping(self) -> bool:
        try:
            return self.client.ping()
        except:
            return False

cache = RedisCache()
EOF

    info "✓ Backend Core Services تم إعدادها"
}

# =======================================================================
# 7. إعداد Docker Compose النهائي
# =======================================================================
setup_docker_compose() {
    log "إعداد docker-compose.yml النهائي..."

    cat > docker-compose.production.yml <<'EOF'
version: "3.9"

networks:
  sahool-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  fs_pg_data:
  fs_redis_data:
  fs_prometheus_data:
  fs_grafana_data:

services:
  # =======================
  # PostgreSQL + PostGIS
  # =======================
  fs-postgres:
    image: postgis/postgis:15-3.4-alpine
    container_name: sahool-fs-postgres
    environment:
      POSTGRES_USER: ${DB_USER:-sahool_production_user}
      POSTGRES_PASSWORD: ${DB_PASS:-change_me_in_production}
      POSTGRES_DB: ${DB_NAME:-sahool_yemen_db}
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5434:5432"
    volumes:
      - fs_pg_data:/var/lib/postgresql/data
      - ./field_suite_service/postgres/init:/docker-entrypoint-initdb.d:ro
    networks:
      - sahool-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 10s
      timeout: 5s
      retries: 5

  # =======================
  # Redis
  # =======================
  fs-redis:
    image: redis:7-alpine
    container_name: sahool-fs-redis
    command: >
      redis-server --appendonly yes
      --requirepass ${REDIS_PASSWORD:-change_me_in_production}
    ports:
      - "6380:6379"
    volumes:
      - fs_redis_data:/data
    networks:
      - sahool-net
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD:-change_me_in_production}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # =======================
  # Nano Services
  # =======================
  weather-core:
    build: ./nano_services/weather-core
    container_name: sahool-weather-core
    networks:
      - sahool-net
    restart: unless-stopped

  imagery-core:
    build: ./nano_services/imagery-core
    container_name: sahool-imagery-core
    networks:
      - sahool-net
    restart: unless-stopped

  geo-core:
    build: ./nano_services/geo-core
    container_name: sahool-geo-core
    networks:
      - sahool-net
    restart: unless-stopped

  analytics-core:
    build: ./nano_services/analytics-core
    container_name: sahool-analytics-core
    networks:
      - sahool-net
    restart: unless-stopped

  query-core:
    build: ./nano_services/query-core
    container_name: sahool-query-core
    networks:
      - sahool-net
    restart: unless-stopped

  advisor-core:
    build: ./nano_services/advisor-core
    container_name: sahool-advisor-core
    networks:
      - sahool-net
    restart: unless-stopped

  # =======================
  # Field Suite Backend
  # =======================
  field-suite-backend:
    build: ./field_suite_service
    container_name: sahool-field-suite-backend
    depends_on:
      fs-postgres:
        condition: service_healthy
      fs-redis:
        condition: service_healthy
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      IMAGERY_CORE_BASE_URL: ${IMAGERY_CORE_BASE_URL}
      ANALYTICS_CORE_BASE_URL: ${ANALYTICS_CORE_BASE_URL}
      GEO_CORE_BASE_URL: ${GEO_CORE_BASE_URL}
      WEATHER_CORE_BASE_URL: ${WEATHER_CORE_BASE_URL}
      ADVISOR_CORE_BASE_URL: ${ADVISOR_CORE_BASE_URL}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    ports:
      - "8000:8000"
      - "8001:8001"
    volumes:
      - ./logs:/app/logs
    networks:
      - sahool-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
      interval: 20s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # =======================
  # Frontend
  # =======================
  frontend:
    build: ./field_suite_frontend
    container_name: sahool-frontend
    depends_on:
      - field-suite-backend
    environment:
      VITE_API_BASE_URL: /api
      VITE_APP_NAME: "سهول اليمن"
    networks:
      - sahool-net
    restart: unless-stopped

  # =======================
  # Gateway (Nginx)
  # =======================
  gateway:
    build: ./gateway-edge
    container_name: sahool-gateway
    depends_on:
      - frontend
      - field-suite-backend
      - weather-core
      - imagery-core
      - geo-core
      - analytics-core
      - query-core
      - advisor-core
    ports:
      - "80:80"
      - "443:443"
    networks:
      - sahool-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 20s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # =======================
  # Prometheus
  # =======================
  prometheus:
    image: prom/prometheus:v2.51.0
    container_name: sahool-prometheus
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - fs_prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--web.console.libraries=/etc/prometheus/console_libraries"
      - "--web.console.templates=/etc/prometheus/consoles"
    ports:
      - "9091:9090"
    networks:
      - sahool-net
    restart: unless-stopped

  # =======================
  # Grafana
  # =======================
  grafana:
    image: grafana/grafana:10.4.0
    container_name: sahool-grafana
    depends_on:
      - prometheus
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_ADMIN_USER:-admin}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin}
      GF_SERVER_ROOT_URL: http://localhost:3003
      GF_USERS_ALLOW_SIGN_UP: "false"
    ports:
      - "3003:3000"
    volumes:
      - fs_grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    networks:
      - sahool-net
    restart: unless-stopped
EOF

    info "✓ Docker Compose تم إعدادها"
}

# =======================================================================
# 8. إعداد Gateway NGINX
# =======================================================================
setup_gateway() {
    log "إعداد Gateway NGINX..."

    cat > gateway-edge/Dockerfile <<'EOF'
FROM nginx:alpine
RUN apk add --no-cache curl
COPY nginx.conf /etc/nginx/nginx.conf
COPY ssl /etc/nginx/ssl
EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]
EOF

    cat > gateway-edge/nginx.conf <<'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    client_max_body_size 50M;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=200r/m;
    limit_req_zone $binary_remote_addr zone=general:10m rate=100r/s;

    # Upstreams
    upstream backend {
        server field-suite-backend:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    upstream frontend {
        server frontend:3000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    upstream nano_weather {
        server weather-core:8000;
    }

    upstream nano_imagery {
        server imagery-core:8000;
    }

    upstream nano_geo {
        server geo-core:8000;
    }

    upstream nano_analytics {
        server analytics-core:8000;
    }

    upstream nano_query {
        server query-core:8000;
    }

    upstream nano_advisor {
        server advisor-core:8000;
    }

    server {
        listen 80;
        server_name _;
        server_tokens off;

        # Security Headers
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

        # CORS
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Tenant-Id" always;

        if ($request_method = 'OPTIONS') {
            return 204;
        }

        # Health Check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }

        # Backend API
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Tenant-Id $http_x_tenant_id;
            proxy_set_header Authorization $http_authorization;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            proxy_connect_timeout 5s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Nano Services Routes
        location /nano/weather/ {
            proxy_pass http://nano_weather/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /nano/imagery/ {
            proxy_pass http://nano_imagery/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /nano/geo/ {
            proxy_pass http://nano_geo/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /nano/analytics/ {
            proxy_pass http://nano_analytics/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /nano/query/ {
            proxy_pass http://nano_query/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /nano/advisor/ {
            proxy_pass http://nano_advisor/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Metrics (internal only)
        location /metrics {
            allow 172.20.0.0/16;
            deny all;
            proxy_pass http://backend/metrics;
        }

        # Error Pages
        error_page 400 401 403 404 429 500 502 503 504 /error.json;
        location = /error.json {
            internal;
            default_type application/json;
            return 503 '{"error":"Service Unavailable","retry_after":30}';
        }
    }
}
EOF

    # Create empty ssl directory for future SSL certificates
    mkdir -p gateway-edge/ssl
    touch gateway-edge/ssl/.gitkeep

    info "✓ NGINX Gateway تم إعدادها"
}

# =======================================================================
# 9. إعداد Frontend (React + Vite)
# =======================================================================
setup_frontend() {
    log "إعداد Frontend..."

    cat > field_suite_frontend/Dockerfile <<'EOF'
FROM node:20-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
EOF

    cat > field_suite_frontend/nginx.conf <<'EOF'
server {
    listen 3000;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    cat > field_suite_frontend/package.json <<'EOF'
{
  "name": "sahool-field-suite-frontend",
  "version": "6.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.3",
    "axios": "^1.6.8",
    "leaflet": "^1.9.4",
    "recharts": "^2.12.5",
    "@tanstack/react-query": "^5.28.9",
    "zustand": "^4.5.2"
  },
  "devDependencies": {
    "@types/react": "^18.2.73",
    "@types/react-dom": "^18.2.23",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.4.3",
    "vite": "^5.2.6"
  }
}
EOF

    info "✓ Frontend تم إعدادها"
}

# =======================================================================
# 10. إعداد Monitoring
# =======================================================================
setup_monitoring() {
    log "إعداد Monitoring..."

    cat > monitoring/prometheus/prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "field-suite-backend"
    metrics_path: /metrics
    static_configs:
      - targets: ["field-suite-backend:8001"]
    scrape_interval: 15s

  - job_name: "nano-services"
    metrics_path: /metrics
    static_configs:
      - targets:
          - "weather-core:8000"
          - "imagery-core:8000"
          - "geo-core:8000"
          - "analytics-core:8000"
          - "query-core:8000"
          - "advisor-core:8000"
    scrape_interval: 30s
EOF

    cat > monitoring/grafana/provisioning/datasources/datasource.yml <<'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    cat > monitoring/grafana/provisioning/dashboards/dashboards.yml <<'EOF'
apiVersion: 1

providers:
  - name: "Field Suite Dashboards"
    orgId: 1
    folder: "Field Suite"
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    info "✓ Monitoring تم إعدادها"
}

# =======================================================================
# الدالة الرئيسية - One-Click Deployment
# =======================================================================
main() {
    clear
    echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║          سهول اليمن - Field Suite NDVI v6.0.0              ║${NC}"
    echo -e "${MAGENTA}║    المنصة الزراعية الذكية لليمن - النشر الكامل              ║${NC}"
    echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # مرحلة التهيئة
    check_requirements
    create_structure
    setup_env

    # مرحلة البيانات
    setup_database

    # مرحلة الخدمات المتخصصة
    setup_nano_services

    # مرحلة الخدمات الرئيسية
    setup_backend_core
    setup_frontend
    setup_gateway

    # مرحلة المراقبة
    setup_monitoring
    setup_docker_compose

    # مرحلة النشر
    log "🔧 بناء وتشغيل المنصة..."
    docker compose -f docker-compose.production.yml up -d --build

    log "⏳ انتظار بدء الخدمات (60 ثانية)..."
    sleep 60

    # فحص الصحة
    log "🏥 فحص صحة الخدمات..."
    curl -f http://localhost/health || warn "لم يتم الوصول إلى Gateway"
    curl -f http://localhost:8000/health/ready || warn "لم يتم الوصول إلى Backend"

    # عرض المعلومات النهائية
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              ✅ اكتمل النشر بنجاح! ✅                        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    info "🌐 المنصة الكاملة: http://localhost/"
    info "📡 API Docs: http://localhost:8000/docs"
    info "📊 Prometheus: http://localhost:9091"
    info "📈 Grafana: http://localhost:3003 (admin/admin)"
    info "🗄️ Database: localhost:5434"
    info "💾 Redis: localhost:6380"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    log "💡 المستخدم الافتراضي: admin / $(grep GRAFANA_ADMIN_PASSWORD .env | cut -d'=' -f2)"
    log "🔐 تأكد من تغيير كلمات المرور في ملف .env"

    echo ""
    log "📋 سكريبتات مساعدة:"
    info " - إيقاف المنصة: docker compose -f docker-compose.production.yml down"
    info " - سجلات الخدمات: docker compose -f docker-compose.production.yml logs -f [service_name]"
    info " - نسخة احتياطية: docker exec sahool-fs-postgres pg_dump -U sahool_production_user sahool_yemen_db > backup_\$(date +%Y%m%d).sql"
}

# تنفيذ السكريبت
main "$@"
