#!/bin/bash
set -euo pipefail

# =======================================================================
# سهول اليمن v7.0.0 - نشر آمن وإنتاجي
# SAHOOL Yemen - Secure Production Deployment
# =======================================================================
MAGENTA='\033[0;35m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'

log() { echo -e "${GREEN}[SAHOOL v7]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# =======================================================================
# 1. فحص متقدم للمتطلبات
# =======================================================================
check_requirements() {
    log "فحص متقدم للمتطلبات..."

    local failed=0
    for cmd in docker git curl openssl; do
        if ! command -v $cmd &>/dev/null; then
            error "الأمر المطلوب غير مثبت: $cmd"
            ((failed++))
        fi
    done

    # Check for docker compose (v2)
    if docker compose version &>/dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &>/dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        error "docker compose غير مثبت"
    fi

    # تحقق من إصدار Docker
    local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    info "Docker version: $docker_version"

    # تحقق من المساحة المتوفرة (يجب أن تكون > 5GB)
    local available_gb=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if (( available_gb < 5 )); then
        warn "المساحة المتوفرة منخفضة: ${available_gb}GB"
    fi

    [ $failed -eq 0 ] && info "✓ جميع المتطلبات متوفرة" || error "فشل في فحص المتطلبات"
}

# =======================================================================
# 2. إنشاء البنية مع أدوات التنظيف
# =======================================================================
create_secure_structure() {
    log "إنشاء بنية آمنة..."

    # إنشاء المجلدات مع أذونات آمنة
    mkdir -p field_suite_service/app/{core,clients,schemas,routers,rules,utils}
    mkdir -p field_suite_service/{tests,scripts,postgres/init,logs}
    mkdir -p nano_services/{weather-core,imagery-core,geo-core,analytics-core,query-core,advisor-core}/app
    mkdir -p field_suite_frontend/src/{components,api,utils,hooks,pages}
    mkdir -p gateway-edge/{conf.d,ssl,errors,logs}
    mkdir -p monitoring/{prometheus,grafana/provisioning/{dashboards,datasources}}
    mkdir -p data/{backups,uploads,static,logs}
    mkdir -p scripts
    mkdir -p logs

    info "✓ البنية تم إنشاؤها بنجاح"
}

# =======================================================================
# 3. إعداد بيئة آمنة متعددة
# =======================================================================
setup_secure_env() {
    log "إعداد بيئة آمنة..."

    # اختيار البيئة
    ENV_MODE="${1:-production}"
    ENV_FILE=".env.${ENV_MODE}"

    if [ -f "$ENV_FILE" ] && [ "${FORCE_RECREATE:-false}" != "true" ]; then
        warn "ملف $ENV_FILE موجود بالفعل"
        return 0
    fi

    # توليد أسرار قوية
    DB_PASS=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -base64 64 | tr -d '\n')
    REDIS_PASS=$(openssl rand -hex 32)
    GRAFANA_PASS=$(openssl rand -hex 16)
    API_SECRET=$(openssl rand -hex 32)

    # كلمات مرور افتراضية للتطوير فقط
    if [ "$ENV_MODE" == "development" ]; then
        DB_PASS="dev_sahool_secure_pass_2024"
        GRAFANA_PASS="admin"
        JWT_SECRET="dev_jwt_secret_change_in_production"
    fi

    cat > "$ENV_FILE" <<EOF
# ==========================================
# سهول اليمن - إعدادات ${ENV_MODE^^}
# تاريخ الإنشاء: $(date '+%Y-%m-%d %H:%M:%S')
# ==========================================

# البيئة
ENV_MODE=$ENV_MODE
COMPOSE_PROJECT_NAME=sahool-${ENV_MODE}
SERVICE_VERSION=7.0.0

# قاعدة البيانات (PostGIS)
DB_USER=sahool_${ENV_MODE}_user
DB_PASS=$DB_PASS
DB_NAME=sahool_yemen_${ENV_MODE}
DB_PORT=5432
DATABASE_URL=postgresql://sahool_${ENV_MODE}_user:$DB_PASS@fs-postgres:5432/sahool_yemen_${ENV_MODE}

# Redis
REDIS_URL=redis://:${REDIS_PASS}@fs-redis:6379/0
REDIS_PASSWORD=$REDIS_PASS

# الأمان
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
API_KEY_SECRET=$API_SECRET

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://localhost"]

# Rate Limiting
API_RATE_LIMIT=200
API_BURST=20

# البيانات الجغرافية - اليمن
YEMEN_REGIONS=Sanaa,Aden,Taiz,Hadramaut,Hudaydah,Ibb,Dhamar,Shabwah,Lahij,Abyan,Marib,AlJawf,Amran,Hajjah,Mahwit,Raymah,AlMahrah,Soqatra,AlBayda,Saadah

# الإحداثيات الافتراضية (صنعاء)
DEFAULT_LAT=15.3547
DEFAULT_LON=44.2067
CURRENCY=YER
LANGUAGE=ar-YE
TIMEZONE=Asia/Aden

# LLM (OpenAI)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000

# Nano Services URLs
IMAGERY_CORE_BASE_URL=http://imagery-core:8000
ANALYTICS_CORE_BASE_URL=http://analytics-core:8000
GEO_CORE_BASE_URL=http://geo-core:8000
WEATHER_CORE_BASE_URL=http://weather-core:8000
ADVISOR_CORE_BASE_URL=http://advisor-core:8000
QUERY_CORE_BASE_URL=http://query-core:8000

# التخزين
STATIC_FILES_PATH=/app/static
MAX_UPLOAD_SIZE=50MB

# المراقبة
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=$GRAFANA_PASS
GF_SERVER_ROOT_URL=http://localhost:3003
PROMETHEUS_PORT=9091

# التسجيل
LOG_LEVEL=INFO
METRICS_PORT=8001
METRICS_ENABLED=true
EOF

    chmod 600 "$ENV_FILE"

    # إنشاء ملف .env للتوافق
    cp "$ENV_FILE" .env

    info "✓ بيئة ${ENV_MODE^^} تم إعدادها في $ENV_FILE"
}

# =======================================================================
# 4. إعداد قاعدة البيانات
# =======================================================================
setup_database_with_validation() {
    log "إعداد قاعدة البيانات..."

    cat > field_suite_service/postgres/init/01-extensions.sql <<'EOF'
-- سهول اليمن - PostGIS Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Validate
SELECT PostGIS_full_version();
EOF

    cat > field_suite_service/postgres/init/02-tables.sql <<'EOF'
-- سهول اليمن - جداول قاعدة البيانات v7

-- المحافظات اليمنية
CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    lat DECIMAL(10, 6) NOT NULL,
    lon DECIMAL(10, 6) NOT NULL,
    area_km2 DECIMAL(12, 2),
    population INTEGER,
    agricultural_potential TEXT,
    climate_zone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- المزارعين
CREATE TABLE IF NOT EXISTS farmers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    region_id INTEGER REFERENCES regions(id),
    national_id VARCHAR(20),
    total_area_ha DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- الحقول الزراعية
CREATE TABLE IF NOT EXISTS fields (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(id),
    region_id INTEGER REFERENCES regions(id),
    name VARCHAR(200) NOT NULL,
    crop_type VARCHAR(100),
    area_ha DECIMAL(10, 2) NOT NULL,
    geometry GEOGRAPHY(POLYGON, 4326),
    ndvi_current DECIMAL(4, 3),
    ndvi_updated_at TIMESTAMP,
    irrigation_type VARCHAR(50),
    soil_type VARCHAR(50),
    planting_date DATE,
    expected_harvest DATE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- بيانات NDVI
CREATE TABLE IF NOT EXISTS ndvi_history (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id),
    ndvi_value DECIMAL(4, 3) NOT NULL,
    ndvi_min DECIMAL(4, 3),
    ndvi_max DECIMAL(4, 3),
    cloud_coverage DECIMAL(5, 2),
    satellite VARCHAR(50),
    captured_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- بيانات الطقس
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    region_id INTEGER REFERENCES regions(id),
    temperature DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    precipitation DECIMAL(6, 2),
    wind_speed DECIMAL(5, 2),
    conditions VARCHAR(100),
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- التنبيهات
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id),
    region_id INTEGER REFERENCES regions(id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title_ar VARCHAR(200),
    message_ar TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- المحاصيل
CREATE TABLE IF NOT EXISTS crops (
    id SERIAL PRIMARY KEY,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    season VARCHAR(50),
    ndvi_min DECIMAL(4, 3),
    ndvi_max DECIMAL(4, 3),
    water_needs VARCHAR(50),
    growth_days INTEGER
);

-- إدخال المحافظات اليمنية العشرين
INSERT INTO regions (name_ar, name_en, lat, lon, area_km2, climate_zone) VALUES
('صنعاء', 'Sanaa', 15.3547, 44.2067, 12630, 'highland'),
('عدن', 'Aden', 12.8254, 45.0339, 760, 'coastal'),
('تعز', 'Taiz', 13.5782, 44.0107, 10008, 'highland'),
('حضرموت', 'Hadramaut', 15.4768, 48.8318, 191032, 'desert'),
('الحديدة', 'Hudaydah', 14.7974, 42.9531, 13479, 'coastal'),
('إب', 'Ibb', 14.1446, 43.9440, 5546, 'highland'),
('ذمار', 'Dhamar', 15.5570, 44.4137, 9495, 'highland'),
('شبوة', 'Shabwah', 14.3801, 45.7186, 47728, 'desert'),
('لحج', 'Lahij', 13.0565, 44.8812, 12648, 'coastal'),
('أبين', 'Abyan', 13.6950, 45.8824, 16943, 'coastal'),
('مأرب', 'Marib', 15.4620, 45.3406, 17405, 'desert'),
('الجوف', 'Al Jawf', 16.7206, 44.8154, 39496, 'desert'),
('عمران', 'Amran', 16.2564, 43.9430, 7583, 'highland'),
('حجة', 'Hajjah', 16.1235, 43.3250, 10145, 'highland'),
('المحويت', 'Mahwit', 15.2589, 43.5400, 2280, 'highland'),
('ريمة', 'Raymah', 14.4000, 44.5000, 1915, 'highland'),
('المهرة', 'Al Mahrah', 16.5000, 51.8000, 82405, 'desert'),
('سقطرى', 'Soqatra', 12.5000, 53.8000, 3625, 'island'),
('البيضاء', 'Al Bayda', 14.2000, 45.3000, 9270, 'highland'),
('صعدة', 'Saadah', 16.9000, 43.7000, 11375, 'highland')
ON CONFLICT DO NOTHING;

-- إدخال المحاصيل
INSERT INTO crops (name_ar, name_en, category, season, ndvi_min, ndvi_max, water_needs, growth_days) VALUES
('قمح', 'Wheat', 'حبوب', 'شتاء', 0.30, 0.70, 'متوسط', 120),
('ذرة', 'Corn', 'حبوب', 'صيف', 0.40, 0.80, 'عالي', 90),
('شعير', 'Barley', 'حبوب', 'شتاء', 0.30, 0.65, 'منخفض', 100),
('بن', 'Coffee', 'محاصيل نقدية', 'على مدار السنة', 0.50, 0.85, 'متوسط', 365),
('طماطم', 'Tomato', 'خضروات', 'ربيع/خريف', 0.35, 0.75, 'عالي', 75),
('بصل', 'Onion', 'خضروات', 'خريف', 0.25, 0.60, 'متوسط', 120),
('بطاطس', 'Potato', 'خضروات', 'ربيع', 0.30, 0.70, 'متوسط', 90),
('خضروات', 'Vegetables', 'خضروات', 'متعدد', 0.30, 0.75, 'عالي', 60),
('فواكه', 'Fruits', 'فواكه', 'متعدد', 0.40, 0.80, 'متوسط', 180),
('أعلاف', 'Fodder', 'أعلاف', 'على مدار السنة', 0.35, 0.70, 'منخفض', 45)
ON CONFLICT DO NOTHING;
EOF

    cat > field_suite_service/postgres/init/03-indexes.sql <<'EOF'
-- الفهارس لتحسين الأداء
CREATE INDEX IF NOT EXISTS idx_fields_farmer ON fields(farmer_id);
CREATE INDEX IF NOT EXISTS idx_fields_region ON fields(region_id);
CREATE INDEX IF NOT EXISTS idx_fields_crop ON fields(crop_type);
CREATE INDEX IF NOT EXISTS idx_fields_geometry ON fields USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_ndvi_field ON ndvi_history(field_id);
CREATE INDEX IF NOT EXISTS idx_ndvi_date ON ndvi_history(captured_at);
CREATE INDEX IF NOT EXISTS idx_weather_region ON weather_data(region_id);
CREATE INDEX IF NOT EXISTS idx_alerts_field ON alerts(field_id);
CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(is_read) WHERE is_read = FALSE;
EOF

    info "✓ قاعدة البيانات تم إعدادها"
}

# =======================================================================
# 5. إعداد Nano Services
# =======================================================================
setup_nano_services_enhanced() {
    log "إعداد Nano Services..."

    local requirements='fastapi==0.110.0
uvicorn[standard]==0.29.0
httpx==0.27.0
pydantic==2.6.4
pydantic-settings==2.2.1
prometheus-client==0.20.0
structlog==24.1.0
python-dotenv==1.0.1'

    local services=("weather-core:8010" "imagery-core:8011" "geo-core:8012" "analytics-core:8013" "query-core:8014" "advisor-core:8015")

    for service_port in "${services[@]}"; do
        IFS=':' read -r service port <<< "$service_port"

        echo "$requirements" > nano_services/$service/requirements.txt

        # Dockerfile
        cat > nano_services/$service/Dockerfile <<EOF
FROM python:3.11-slim
RUN groupadd -r sahool && useradd -r -g sahool sahool
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN chown -R sahool:sahool /app
USER sahool
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:$port/health || exit 1
EXPOSE $port
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$port"]
EOF

        # Main app
        cat > nano_services/$service/app/main.py <<EOF
"""
سهول اليمن - $service
Nano Service for Yemen Agricultural Platform
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random

app = FastAPI(
    title="سهول اليمن - ${service^}",
    description="خدمة ${service} للمنصة الزراعية",
    version="7.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "$service",
        "version": "7.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

EOF

        # Service-specific endpoints
        case $service in
            weather-core)
                cat >> nano_services/$service/app/main.py <<'EOF'
YEMEN_WEATHER_PROFILES = {
    "coastal": {"temp_range": (28, 38), "humidity": (60, 85), "rain_prob": 15},
    "highland": {"temp_range": (15, 28), "humidity": (30, 60), "rain_prob": 25},
    "desert": {"temp_range": (25, 45), "humidity": (10, 30), "rain_prob": 5},
    "island": {"temp_range": (26, 32), "humidity": (70, 90), "rain_prob": 20},
}

@app.get("/api/v1/weather/fields/{field_id}")
async def get_field_weather(field_id: int, climate_zone: str = "highland"):
    profile = YEMEN_WEATHER_PROFILES.get(climate_zone, YEMEN_WEATHER_PROFILES["highland"])
    return {
        "field_id": field_id,
        "temperature": round(random.uniform(*profile["temp_range"]), 1),
        "humidity": random.randint(*profile["humidity"]),
        "wind_speed": round(random.uniform(5, 25), 1),
        "rain_probability": profile["rain_prob"],
        "conditions": random.choice(["sunny", "partly_cloudy", "cloudy"]),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/weather/fields/{field_id}/forecast")
async def get_weather_forecast(field_id: int, days: int = 7):
    forecasts = []
    for i in range(days):
        forecasts.append({
            "day": i + 1,
            "temp_max": round(random.uniform(25, 35), 1),
            "temp_min": round(random.uniform(15, 22), 1),
            "rain_prob": random.randint(0, 40),
            "conditions": random.choice(["sunny", "partly_cloudy", "cloudy", "rainy"])
        })
    return {"field_id": field_id, "forecast": forecasts}

@app.get("/api/v1/weather/alerts")
async def get_weather_alerts(region_id: int = None):
    alerts = []
    if random.random() > 0.7:
        alerts.append({
            "type": "heat_wave",
            "severity": "warning",
            "message_ar": "موجة حر متوقعة خلال الأيام القادمة",
            "region_id": region_id
        })
    return {"alerts": alerts, "count": len(alerts)}
EOF
                ;;
            imagery-core)
                cat >> nano_services/$service/app/main.py <<'EOF'
CROP_NDVI_RANGES = {
    "قمح": (0.30, 0.70), "ذرة": (0.40, 0.80), "بن": (0.50, 0.85),
    "طماطم": (0.35, 0.75), "خضروات": (0.30, 0.75),
}

def get_ndvi_status(ndvi: float) -> dict:
    if ndvi > 0.6: return {"status": "ممتاز", "color": "green", "score": 90}
    if ndvi > 0.4: return {"status": "جيد", "color": "lime", "score": 70}
    if ndvi > 0.25: return {"status": "متوسط", "color": "yellow", "score": 50}
    return {"status": "يحتاج متابعة", "color": "red", "score": 30}

@app.get("/api/v1/ndvi/{field_id}")
async def get_ndvi(field_id: int, crop_type: str = "قمح"):
    ndvi_range = CROP_NDVI_RANGES.get(crop_type, (0.3, 0.7))
    ndvi_value = round(random.uniform(*ndvi_range), 3)
    status = get_ndvi_status(ndvi_value)
    return {
        "field_id": field_id,
        "ndvi_mean": ndvi_value,
        "ndvi_min": round(ndvi_value - 0.15, 3),
        "ndvi_max": round(ndvi_value + 0.1, 3),
        **status,
        "satellite": random.choice(["Sentinel-2A", "Sentinel-2B", "Landsat-8"]),
        "cloud_coverage": random.randint(0, 20),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/ndvi/{field_id}/history")
async def get_ndvi_history(field_id: int, months: int = 6):
    history = []
    for i in range(months * 4):
        history.append({
            "week": i + 1,
            "ndvi": round(random.uniform(0.3, 0.75), 3),
            "date": f"2024-{(i//4)+1:02d}-{(i%4)*7+1:02d}"
        })
    return {"field_id": field_id, "history": history}
EOF
                ;;
            geo-core)
                cat >> nano_services/$service/app/main.py <<'EOF'
import math

YEMEN_BOUNDS = {"min_lat": 12.0, "max_lat": 19.0, "min_lon": 42.0, "max_lon": 55.0}

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

@app.post("/api/v1/geo/compute-area")
async def compute_area(coordinates: list):
    # Simplified area calculation
    area_ha = len(coordinates) * random.uniform(5, 50)
    perimeter = len(coordinates) * random.uniform(100, 500)
    return {
        "area_hectares": round(area_ha, 2),
        "area_dunums": round(area_ha * 10, 2),
        "perimeter_meters": round(perimeter, 2)
    }

@app.get("/api/v1/geo/elevation")
async def get_elevation(lat: float, lon: float):
    if not (YEMEN_BOUNDS["min_lat"] <= lat <= YEMEN_BOUNDS["max_lat"]):
        raise HTTPException(400, "Latitude outside Yemen bounds")
    elevation = random.randint(0, 3000) if lat > 14 else random.randint(0, 500)
    return {"lat": lat, "lon": lon, "elevation_m": elevation}

@app.get("/api/v1/geo/distance")
async def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float):
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    return {"distance_km": round(distance, 2), "distance_m": round(distance * 1000, 0)}

@app.get("/api/v1/geo/zone-info")
async def get_zone_info(lat: float, lon: float):
    if lat > 15: zone = "highland"
    elif lon < 44: zone = "coastal"
    else: zone = "desert"
    return {"lat": lat, "lon": lon, "zone": zone, "country": "Yemen"}
EOF
                ;;
            analytics-core)
                cat >> nano_services/$service/app/main.py <<'EOF'
BASE_YIELDS = {"قمح": 2200, "ذرة": 3500, "شعير": 1800, "طماطم": 25000, "بصل": 15000}

@app.get("/api/v1/analytics/yield-prediction")
async def predict_yield(field_id: int, crop_type: str = "قمح", area_ha: float = 10, ndvi: float = 0.6):
    base = BASE_YIELDS.get(crop_type, 2000)
    factor = 0.5 + ndvi
    predicted = base * factor * area_ha
    return {
        "field_id": field_id,
        "crop": crop_type,
        "predicted_yield_kg": round(predicted, 0),
        "yield_per_ha": round(predicted / area_ha, 0),
        "confidence": round(0.7 + ndvi * 0.2, 2)
    }

@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_stats():
    return {
        "total_farmers": random.randint(15000, 25000),
        "total_fields": random.randint(40000, 60000),
        "total_area_ha": random.randint(150000, 300000),
        "active_regions": 20,
        "ndvi_average": round(random.uniform(0.4, 0.65), 2),
        "alerts_count": random.randint(50, 200)
    }

@app.get("/api/v1/analytics/region-stats")
async def get_region_stats(region_id: int):
    return {
        "region_id": region_id,
        "farmers": random.randint(500, 3000),
        "fields": random.randint(1000, 8000),
        "total_area_ha": random.randint(5000, 50000),
        "avg_ndvi": round(random.uniform(0.35, 0.7), 2),
        "top_crops": ["قمح", "ذرة", "خضروات"]
    }
EOF
                ;;
            query-core)
                cat >> nano_services/$service/app/main.py <<'EOF'
@app.get("/api/v1/fields")
async def list_fields(region_id: int = None, limit: int = 20, offset: int = 0):
    fields = []
    for i in range(limit):
        fields.append({
            "id": offset + i + 1,
            "name": f"حقل {offset + i + 1}",
            "crop_type": random.choice(["قمح", "ذرة", "طماطم", "خضروات"]),
            "area_ha": round(random.uniform(1, 50), 2),
            "ndvi": round(random.uniform(0.3, 0.8), 3),
            "region_id": region_id or random.randint(1, 20)
        })
    return {"fields": fields, "total": 1000, "limit": limit, "offset": offset}

@app.get("/api/v1/fields/{field_id}")
async def get_field(field_id: int):
    return {
        "id": field_id,
        "name": f"حقل {field_id}",
        "crop_type": random.choice(["قمح", "ذرة", "طماطم"]),
        "area_ha": round(random.uniform(5, 30), 2),
        "ndvi_current": round(random.uniform(0.4, 0.75), 3),
        "irrigation_type": random.choice(["drip", "sprinkler", "flood"]),
        "soil_type": random.choice(["loamy", "clay", "sandy"]),
        "status": "active"
    }

@app.get("/api/v1/fields/summary")
async def get_fields_summary(region_id: int = None):
    return {
        "total_fields": random.randint(1000, 5000),
        "total_area_ha": random.randint(10000, 50000),
        "by_crop": {
            "قمح": random.randint(200, 1000),
            "ذرة": random.randint(200, 800),
            "خضروات": random.randint(300, 1200)
        }
    }
EOF
                ;;
            advisor-core)
                cat >> nano_services/$service/app/main.py <<'EOF'
YEMEN_PESTS = [
    {"name_ar": "دودة الحشد الخريفية", "crops": ["ذرة", "قمح"], "season": "خريف"},
    {"name_ar": "المن", "crops": ["خضروات", "طماطم"], "season": "ربيع"},
    {"name_ar": "الجراد الصحراوي", "crops": ["all"], "season": "صيف"},
]

@app.post("/api/v1/advisor/analyze-field")
async def analyze_field(field_id: int, ndvi: float = 0.5, crop_type: str = "قمح"):
    recommendations = []
    if ndvi < 0.4:
        recommendations.append({"type": "irrigation", "message_ar": "زيادة الري موصى بها", "priority": "high"})
    if ndvi < 0.3:
        recommendations.append({"type": "fertilizer", "message_ar": "إضافة سماد نيتروجيني", "priority": "high"})
    if ndvi > 0.7:
        recommendations.append({"type": "harvest", "message_ar": "المحصول جاهز للحصاد قريباً", "priority": "medium"})
    return {"field_id": field_id, "ndvi": ndvi, "health_score": int(ndvi * 100), "recommendations": recommendations}

@app.get("/api/v1/advisor/irrigation/{field_id}")
async def get_irrigation_advice(field_id: int, crop_type: str = "قمح", soil_type: str = "loamy"):
    water_needs = {"قمح": 450, "ذرة": 600, "طماطم": 700, "خضروات": 500}
    return {
        "field_id": field_id,
        "recommended_mm_per_week": water_needs.get(crop_type, 500) // 7,
        "irrigation_schedule": "كل 3 أيام",
        "best_time": "الصباح الباكر أو المساء"
    }

@app.get("/api/v1/advisor/pest-alerts")
async def get_pest_alerts(region_id: int = None, crop_type: str = None):
    alerts = [p for p in YEMEN_PESTS if crop_type is None or crop_type in p["crops"] or "all" in p["crops"]]
    return {"alerts": alerts[:3], "count": len(alerts[:3])}

@app.post("/api/v1/advisor/ask")
async def ask_advisor(question: str, context: dict = None):
    return {
        "question": question,
        "answer": "بناءً على البيانات المتاحة، ننصح بمراجعة حالة الري والتسميد للحقل.",
        "confidence": 0.85,
        "sources": ["قاعدة المعرفة الزراعية اليمنية"]
    }
EOF
                ;;
        esac

        touch nano_services/$service/app/__init__.py
    done

    info "✓ Nano Services تم إعدادها"
}

# =======================================================================
# 6. إعداد Frontend
# =======================================================================
setup_frontend() {
    log "إعداد Frontend..."

    # package.json
    cat > field_suite_frontend/package.json <<'EOF'
{
  "name": "sahool-yemen-frontend",
  "version": "7.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.3",
    "axios": "^1.6.8",
    "@tanstack/react-query": "^5.28.9",
    "recharts": "^2.12.5",
    "leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1",
    "zustand": "^4.5.2",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@types/leaflet": "^1.9.8",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.4.2",
    "vite": "^5.2.0",
    "tailwindcss": "^3.4.3",
    "postcss": "^8.4.38",
    "autoprefixer": "^10.4.19",
    "vitest": "^1.4.0"
  }
}
EOF

    # Vite config
    cat > field_suite_frontend/vite.config.ts <<'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false
  }
})
EOF

    # Tailwind config
    cat > field_suite_frontend/tailwind.config.js <<'EOF'
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        sahool: { 50: '#f0fdf4', 500: '#22c55e', 600: '#16a34a', 700: '#15803d' }
      },
      fontFamily: { arabic: ['Tajawal', 'sans-serif'] }
    }
  },
  plugins: []
}
EOF

    # Index HTML
    cat > field_suite_frontend/index.html <<'EOF'
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>سهول اليمن - المنصة الزراعية الذكية</title>
  <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap" rel="stylesheet">
</head>
<body class="font-arabic bg-gray-50">
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
EOF

    # Dockerfile
    cat > field_suite_frontend/Dockerfile <<'EOF'
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

    cat > field_suite_frontend/nginx.conf <<'EOF'
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
    location /api {
        proxy_pass http://field-suite-backend:8000;
    }
}
EOF

    info "✓ Frontend تم إعدادها"
}

# =======================================================================
# 7. إعداد Gateway
# =======================================================================
setup_gateway() {
    log "إعداد Gateway..."

    cat > gateway-edge/Dockerfile <<'EOF'
FROM nginx:alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d /etc/nginx/conf.d
COPY errors /usr/share/nginx/errors
EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]
EOF

    cat > gateway-edge/nginx.conf <<'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;
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
    types_hash_max_size 2048;
    client_max_body_size 50M;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=50r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    include /etc/nginx/conf.d/*.conf;
}
EOF

    cat > gateway-edge/conf.d/default.conf <<'EOF'
upstream backend {
    server field-suite-backend:8000;
    keepalive 32;
}

upstream frontend {
    server frontend:80;
}

server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Health check
    location /health {
        access_log off;
        return 200 '{"status":"healthy","gateway":"nginx"}';
        add_header Content-Type application/json;
    }

    # API routes
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://backend/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket
    location /ws {
        proxy_pass http://backend/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # API docs
    location /docs {
        proxy_pass http://backend/docs;
    }

    location /redoc {
        proxy_pass http://backend/redoc;
    }

    # Metrics
    location /metrics {
        proxy_pass http://backend/metrics;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
    }

    # Error pages
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/errors;
    }
}
EOF

    mkdir -p gateway-edge/errors
    cat > gateway-edge/errors/50x.html <<'EOF'
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="UTF-8"><title>خطأ - سهول اليمن</title></head>
<body style="font-family: Tajawal, sans-serif; text-align: center; padding: 50px;">
<h1>عذراً، حدث خطأ</h1>
<p>نعتذر عن هذا الخطأ. يرجى المحاولة مرة أخرى لاحقاً.</p>
</body>
</html>
EOF

    info "✓ Gateway تم إعدادها"
}

# =======================================================================
# 8. إعداد Monitoring
# =======================================================================
setup_monitoring() {
    log "إعداد المراقبة..."

    cat > monitoring/prometheus/prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'sahool-backend'
    static_configs:
      - targets: ['field-suite-backend:8001']
    metrics_path: /metrics

  - job_name: 'nano-services'
    static_configs:
      - targets:
        - 'weather-core:8010'
        - 'imagery-core:8011'
        - 'geo-core:8012'
        - 'analytics-core:8013'
        - 'query-core:8014'
        - 'advisor-core:8015'

  - job_name: 'gateway'
    static_configs:
      - targets: ['gateway:80']
    metrics_path: /health
EOF

    cat > monitoring/grafana/provisioning/datasources/datasources.yml <<'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    mkdir -p monitoring/grafana/provisioning/dashboards
    cat > monitoring/grafana/provisioning/dashboards/dashboards.yml <<'EOF'
apiVersion: 1
providers:
  - name: 'default'
    folder: 'سهول اليمن'
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    info "✓ المراقبة تم إعدادها"
}

# =======================================================================
# 9. Docker Compose Production
# =======================================================================
setup_docker_compose_production() {
    log "إعداد Docker Compose..."

    cat > docker-compose.prod.yml <<'EOF'
version: "3.9"

networks:
  sahool-network:
    driver: bridge

volumes:
  pg_data:
  redis_data:
  prometheus_data:
  grafana_data:

services:
  fs-postgres:
    image: postgis/postgis:15-3.4-alpine
    container_name: sahool-postgres
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASS}
      POSTGRES_DB: ${DB_NAME}
    ports:
      - "5434:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./field_suite_service/postgres/init:/docker-entrypoint-initdb.d:ro
    networks:
      - sahool-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  fs-redis:
    image: redis:7-alpine
    container_name: sahool-redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6380:6379"
    networks:
      - sahool-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  weather-core:
    build: ./nano_services/weather-core
    container_name: sahool-weather
    ports:
      - "8010:8010"
    networks:
      - sahool-network
    restart: unless-stopped

  imagery-core:
    build: ./nano_services/imagery-core
    container_name: sahool-imagery
    ports:
      - "8011:8011"
    networks:
      - sahool-network
    restart: unless-stopped

  geo-core:
    build: ./nano_services/geo-core
    container_name: sahool-geo
    ports:
      - "8012:8012"
    networks:
      - sahool-network
    restart: unless-stopped

  analytics-core:
    build: ./nano_services/analytics-core
    container_name: sahool-analytics
    ports:
      - "8013:8013"
    networks:
      - sahool-network
    restart: unless-stopped

  query-core:
    build: ./nano_services/query-core
    container_name: sahool-query
    ports:
      - "8014:8014"
    networks:
      - sahool-network
    restart: unless-stopped

  advisor-core:
    build: ./nano_services/advisor-core
    container_name: sahool-advisor
    ports:
      - "8015:8015"
    networks:
      - sahool-network
    restart: unless-stopped

  field-suite-backend:
    build: ./field_suite_service
    container_name: sahool-backend
    depends_on:
      fs-postgres:
        condition: service_healthy
      fs-redis:
        condition: service_healthy
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - IMAGERY_CORE_BASE_URL=http://imagery-core:8011
      - ANALYTICS_CORE_BASE_URL=http://analytics-core:8013
      - GEO_CORE_BASE_URL=http://geo-core:8012
      - WEATHER_CORE_BASE_URL=http://weather-core:8010
      - ADVISOR_CORE_BASE_URL=http://advisor-core:8015
      - QUERY_CORE_BASE_URL=http://query-core:8014
    volumes:
      - ./logs:/app/logs
    ports:
      - "8000:8000"
      - "8001:8001"
    networks:
      - sahool-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

  frontend:
    build: ./field_suite_frontend
    container_name: sahool-frontend
    networks:
      - sahool-network
    restart: unless-stopped

  gateway:
    build: ./gateway-edge
    container_name: sahool-gateway
    depends_on:
      - frontend
      - field-suite-backend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./logs/nginx:/var/log/nginx
    networks:
      - sahool-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:v2.51.0
    container_name: sahool-prometheus
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--web.enable-lifecycle"
    ports:
      - "9091:9090"
    networks:
      - sahool-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:10.4.0
    container_name: sahool-grafana
    depends_on:
      - prometheus
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3003:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    networks:
      - sahool-network
    restart: unless-stopped
EOF

    info "✓ Docker Compose تم إعدادها"
}

# =======================================================================
# 10. سكريبتات التحكم
# =======================================================================
create_advanced_scripts() {
    log "إنشاء سكريبتات التحكم..."

    cat > scripts/sahoolctl.sh <<'EOF'
#!/bin/bash
set -euo pipefail

COMMAND="${1:-help}"
SERVICE="${2:-}"

case $COMMAND in
    start)
        echo "🚀 بدء تشغيل سهول اليمن..."
        docker compose -f docker-compose.prod.yml up -d --build
        echo "✅ تم التشغيل بنجاح"
        ;;
    stop)
        echo "⏹️ إيقاف الخدمات..."
        docker compose -f docker-compose.prod.yml down
        ;;
    restart)
        echo "🔄 إعادة التشغيل..."
        docker compose -f docker-compose.prod.yml restart $SERVICE
        ;;
    logs)
        docker compose -f docker-compose.prod.yml logs -f $SERVICE
        ;;
    status)
        docker compose -f docker-compose.prod.yml ps
        ;;
    health)
        echo "🏥 فحص الصحة..."
        curl -s http://localhost/health | jq . 2>/dev/null || echo "Gateway: ❌"
        curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "Backend: ❌"
        ;;
    clean)
        echo "🧹 تنظيف..."
        docker compose -f docker-compose.prod.yml down -v --remove-orphans
        docker system prune -f
        ;;
    backup)
        ./scripts/backup.sh
        ;;
    help|*)
        echo "سهول اليمن - أوامر التحكم"
        echo ""
        echo "الاستخدام: ./scripts/sahoolctl.sh [أمر] [خدمة]"
        echo ""
        echo "الأوامر:"
        echo "  start    - تشغيل جميع الخدمات"
        echo "  stop     - إيقاف جميع الخدمات"
        echo "  restart  - إعادة تشغيل (خدمة محددة أو الكل)"
        echo "  logs     - عرض السجلات"
        echo "  status   - حالة الخدمات"
        echo "  health   - فحص الصحة"
        echo "  clean    - تنظيف البيئة"
        echo "  backup   - نسخ احتياطي"
        ;;
esac
EOF
    chmod +x scripts/sahoolctl.sh

    cat > scripts/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="./data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

echo "📦 إنشاء نسخة احتياطية..."
docker exec sahool-postgres pg_dump -U sahool_production_user sahool_yemen_production | gzip > "$BACKUP_DIR/db_${TIMESTAMP}.sql.gz"
echo "✅ النسخة الاحتياطية: $BACKUP_DIR/db_${TIMESTAMP}.sql.gz"

# حذف النسخ القديمة (أكثر من 30 يوم)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
EOF
    chmod +x scripts/backup.sh

    info "✓ سكريبتات التحكم تم إنشاؤها"
}

# =======================================================================
# الدالة الرئيسية
# =======================================================================
main_v7() {
    clear
    echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║           سهول اليمن v7.0.0 - نشر آمن وإنتاجي              ║${NC}"
    echo -e "${MAGENTA}║         SAHOOL Yemen - Secure Production Deployment          ║${NC}"
    echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    ENV_MODE="${1:-production}"
    export FORCE_RECREATE="${2:-false}"

    log "وضع البيئة: ${ENV_MODE^^}"

    check_requirements
    create_secure_structure
    setup_secure_env "$ENV_MODE"
    setup_database_with_validation
    setup_nano_services_enhanced
    setup_frontend
    setup_gateway
    setup_monitoring
    setup_docker_compose_production
    create_advanced_scripts

    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ تم إعداد سهول اليمن v7.0.0 بنجاح!${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}📋 ملخص الإعداد:${NC}"
    echo "   • البيئة: $ENV_MODE"
    echo "   • ملف الإعدادات: .env.$ENV_MODE"
    echo "   • Docker Compose: docker-compose.prod.yml"
    echo ""
    echo -e "${GREEN}🚀 للتشغيل:${NC}"
    echo "   ./scripts/sahoolctl.sh start"
    echo ""
    echo -e "${BLUE}🔗 الروابط بعد التشغيل:${NC}"
    echo "   • الواجهة: http://localhost"
    echo "   • API: http://localhost/api"
    echo "   • التوثيق: http://localhost/docs"
    echo "   • Grafana: http://localhost:3003"
    echo "   • Prometheus: http://localhost:9091"
}

main_v7 "$@"
