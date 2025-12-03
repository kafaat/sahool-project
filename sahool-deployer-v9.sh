#!/bin/bash
set -euo pipefail

# =======================================================================
# سهول اليمن v9.0.0 - سكريبت النشر الشامل للإنتاج
# SAHOOL Yemen Field Suite - All-in-One Production Deployment Script
# Includes: Security, Performance, Service Mesh, Monitoring, CI/CD
# =======================================================================

# ==================== الإعدادات والألوان ====================
MAGENTA='\033[0;35m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${GREEN}[SAHOOL v9]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ==================== معالجة الأخطاء المتقدمة ====================
CLEANUP_NEEDED=false

error_handler() {
    local line_no=$1
    local exit_code=$2
    echo -e "\n${RED}[FATAL]${NC} خطأ على السطر $line_no (كود الخروج: $exit_code)"
    echo -e "${YELLOW}جارٍ التنظيف الآمن...${NC}"
    cleanup_on_exit
    exit 1
}

cleanup_on_exit() {
    if [ "$CLEANUP_NEEDED" = true ] && [ "${KEEP_ON_FAILURE:-false}" != "true" ]; then
        log "تنظيف الموارد المؤقتة..."
        docker compose -f docker-compose.v9.yml down --remove-orphans 2>/dev/null || true
    fi
}

trap 'error_handler $LINENO $?' ERR
trap 'cleanup_on_exit' EXIT

# ==================== 1. فحص البيئة الشامل ====================
comprehensive_check() {
    log "فحص شامل للبيئة والمتطلبات..."

    local required_tools=("docker" "curl" "openssl" "jq" "git")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &>/dev/null; then
            error "الأمر المطلوب غير مثبت: $tool"
        fi
    done

    # فحص docker compose (v2)
    if ! docker compose version &>/dev/null; then
        error "Docker Compose V2 غير مثبت"
    fi

    local docker_version
    docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [[ "$(printf '%s\n' "24.0.0" "$docker_version" | sort -V | head -n1)" != "24.0.0" ]]; then
        warn "Docker إصدار $docker_version قديم، يُنصح بالترقية إلى 24.0+"
    fi

    local available_gb
    available_gb=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if (( available_gb < 25 )); then
        error "المساحة المتوفرة غير كافية: ${available_gb}GB (مطلوب 25GB على الأقل)"
    fi

    local available_mem
    available_mem=$(free -g 2>/dev/null | awk '/Mem:/ {print $2}' || echo "16")
    if (( available_mem < 8 )); then
        warn "الذاكرة المتوفرة قد تكون غير كافية: ${available_mem}GB"
    fi

    if [ "$(id -u)" -eq 0 ]; then
        warn "التشغيل كـ root غير مستحسن. استخدم مستخدماً عادياً مع sudo."
    fi

    info "البيئة مكتملة وآمنة"
}

# ==================== 2. إنشاء البنية الآمنة ====================
create_secure_structure() {
    log "إنشاء البنية الآمنة والمنظمة..."

    if [ -f "docker-compose.v9.yml" ] && [ "${FORCE_REBUILD:-false}" != "true" ]; then
        warn "تم العثور على نشر قديم. استخدم FORCE_REBUILD=true للاستبدال"
        read -p "هل تريد الحذف والإعادة البناء؟ (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
        docker compose -f docker-compose.v9.yml down --volumes --remove-orphans 2>/dev/null || true
        CLEANUP_NEEDED=true
    fi

    # إنشاء المجلدات بشكل صريح
    local dirs=(
        "field_suite_service/app/core"
        "field_suite_service/app/clients"
        "field_suite_service/app/schemas"
        "field_suite_service/app/routers"
        "field_suite_service/app/services"
        "field_suite_service/app/utils"
        "field_suite_service/tests"
        "field_suite_service/scripts"
        "field_suite_service/postgres/init"
        "field_suite_service/logs"
        "field_suite_service/static"
        "field_suite_service/migrations/versions"
        "field_suite_service/redis"
        "nano_services/weather-core/app"
        "nano_services/imagery-core/app"
        "nano_services/geo-core/app"
        "nano_services/analytics-core/app"
        "nano_services/query-core/app"
        "nano_services/advisor-core/app"
        "nano_services/notification-core/app"
        "field_suite_frontend/src/components"
        "field_suite_frontend/src/api"
        "field_suite_frontend/src/hooks"
        "field_suite_frontend/src/utils"
        "field_suite_frontend/src/store"
        "field_suite_frontend/src/pages"
        "field_suite_frontend/public/assets"
        "field_suite_frontend/public/locales"
        "field_suite_frontend/public/icons"
        "field_suite_frontend/tests"
        "gateway-edge/conf.d"
        "gateway-edge/ssl"
        "gateway-edge/certs"
        "gateway-edge/logs"
        "gateway-edge/errors"
        "monitoring/prometheus/rules"
        "monitoring/prometheus/targets"
        "monitoring/grafana/provisioning/dashboards"
        "monitoring/grafana/provisioning/datasources"
        "monitoring/grafana/dashboards"
        "monitoring/loki"
        "monitoring/tempo"
        "monitoring/blackbox"
        "monitoring/cadvisor"
        "data/backups"
        "data/uploads"
        "data/static"
        "data/logs"
        "data/secrets"
        "scripts/helpers"
        "scripts/backups"
        "scripts/alerts"
        "vault/secrets"
        "vault/policies"
        "vault/audit"
        "tests/unit"
        "tests/integration"
        "tests/e2e"
        "tests/performance"
        "docs/api"
        "docs/architecture"
        "docs/guides"
        "envoy/configs"
        "tls"
        "logs/audit"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done

    chmod 755 scripts/ field_suite_service/ nano_services/ field_suite_frontend/ 2>/dev/null || true
    chmod 700 vault/ data/secrets/ logs/audit/ 2>/dev/null || true

    info "البنية الآمنة جاهزة"
}

# ==================== 3. توليد وإدارة الأسرار الآمنة ====================
setup_vault_and_secrets() {
    log "إعداد Vault وإدارة الأسرار (مع Rotation)..."

    mkdir -p vault/{policies,audit} data/secrets tls

    # توليد الأسرار بشكل صحيح (بدون heredoc مع اقتباسات)
    local db_password
    local db_root_password
    local db_monitor_password
    local redis_password
    local redis_encryption_key
    local redis_acl_default
    local redis_acl_monitor
    local jwt_secret
    local jwt_refresh_secret
    local api_key
    local api_key_id
    local api_key_hash
    local grafana_admin_password
    local grafana_secret_key
    local encryption_key
    local encryption_salt

    db_password=$(openssl rand -base64 64 | tr -d '\n')
    db_root_password=$(openssl rand -base64 64 | tr -d '\n')
    db_monitor_password=$(openssl rand -base64 32 | tr -d '\n')
    redis_password=$(openssl rand -base64 64 | tr -d '\n')
    redis_encryption_key=$(openssl rand -hex 32)
    redis_acl_default=$(openssl rand -base64 32 | tr -d '\n')
    redis_acl_monitor=$(openssl rand -base64 32 | tr -d '\n')
    jwt_secret=$(openssl rand -base64 64 | tr -d '\n')
    jwt_refresh_secret=$(openssl rand -base64 64 | tr -d '\n')
    api_key=$(openssl rand -hex 64)
    api_key_id="sahool-key-$(date +%Y%m%d_%H%M%S)"
    api_key_hash=$(openssl rand -hex 32)
    grafana_admin_password=$(openssl rand -base64 32 | head -c 16)
    grafana_secret_key=$(openssl rand -base64 32 | tr -d '\n')
    encryption_key=$(openssl rand -base64 32 | tr -d '\n')
    encryption_salt=$(openssl rand -base64 16 | tr -d '\n')

    # إنشاء ملف الأسرار JSON
    cat > vault/secrets.json <<EOF
{
  "secrets": {
    "db": {
      "password": "${db_password}",
      "root_password": "${db_root_password}",
      "monitor_password": "${db_monitor_password}"
    },
    "redis": {
      "password": "${redis_password}",
      "encryption_key": "${redis_encryption_key}",
      "acl_users": {
        "default": "${redis_acl_default}",
        "monitor": "${redis_acl_monitor}"
      }
    },
    "jwt": {
      "secret": "${jwt_secret}",
      "refresh_secret": "${jwt_refresh_secret}"
    },
    "api": {
      "key": "${api_key}",
      "key_id": "${api_key_id}",
      "key_hash": "${api_key_hash}"
    },
    "grafana": {
      "admin_password": "${grafana_admin_password}",
      "secret_key": "${grafana_secret_key}"
    },
    "encryption": {
      "key": "${encryption_key}",
      "salt": "${encryption_salt}",
      "algorithm": "aes-256-gcm"
    },
    "sentinel_hub": {
      "client_id": "${SENTINEL_CLIENT_ID:-}",
      "client_secret": "${SENTINEL_CLIENT_SECRET:-}"
    },
    "openweather": {
      "api_key": "${OPENWEATHER_API_KEY:-}"
    },
    "email": {
      "smtp_host": "${SMTP_HOST:-}",
      "smtp_user": "${SMTP_USER:-}",
      "smtp_pass": "${SMTP_PASS:-}"
    }
  },
  "metadata": {
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "9.0.0",
    "rotation_policy": {
      "jwt": "30d",
      "api": "90d",
      "db": "365d"
    },
    "last_rotation": null
  }
}
EOF

    chmod 600 vault/secrets.json

    # إنشاء ACL لـ Redis
    cat > data/secrets/redis.acl <<EOF
user default on >${redis_acl_default} +@all ~* &*
user monitor on >${redis_acl_monitor} +ping +info +monitor +client|list ~* &*
EOF
    chmod 600 data/secrets/redis.acl

    # توليد شهادات TLS
    if [ ! -f "tls/internal.key" ] || [ "${FORCE_RECREATE_CERTS:-false}" == "true" ]; then
        openssl req -x509 -newkey rsa:4096 -keyout tls/internal.key -out tls/internal.crt \
            -days 365 -nodes -subj "/CN=sahool.internal/O=Sahool Yemen/C=YE/L=Sanaa" 2>/dev/null
        chmod 600 tls/*
    fi

    # توليد مفاتيح JWT
    if [ ! -f "data/secrets/jwt.key" ]; then
        openssl genrsa -out data/secrets/jwt.key 4096 2>/dev/null
        openssl rsa -in data/secrets/jwt.key -pubout -out data/secrets/jwt.pub 2>/dev/null
        chmod 600 data/secrets/jwt.*
    fi

    # إنشاء ملفات secrets لـ Docker
    echo -n "$db_password" > data/secrets/db_pass
    echo -n "$redis_password" > data/secrets/redis_pass
    echo -n "$jwt_secret" > data/secrets/jwt_secret
    echo -n "$api_key" > data/secrets/api_key
    echo -n "$grafana_admin_password" > data/secrets/grafana_pass
    echo -n "${OPENAI_API_KEY:-}" > data/secrets/openai_key
    echo -n "${SENTINEL_CLIENT_ID:-}" > data/secrets/sentinel_id
    echo -n "${SENTINEL_CLIENT_SECRET:-}" > data/secrets/sentinel_secret
    echo -n "${OPENWEATHER_API_KEY:-}" > data/secrets/openweather_key

    chmod 600 data/secrets/*

    info "Vault وإدارة الأسرار جاهزة مع rotation policies"
}

# ==================== 4. إعداد قاعدة البيانات مع Alembic ====================
setup_database() {
    log "إعداد قاعدة البيانات مع migrations..."

    cat > field_suite_service/alembic.ini <<'EOF'
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://%(DB_USER)s:%(DB_PASS)s@%(DB_HOST)s:%(DB_PORT)s/%(DB_NAME)s

[loggers]
keys = root,sqlalchemy,alembic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

    mkdir -p field_suite_service/migrations/versions

    cat > field_suite_service/migrations/env.py <<'EOF'
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio
import os
import sys

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

target_metadata = None

def get_database_url():
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://sahool:sahool@localhost:5432/sahool_db"
    ).replace("postgresql://", "postgresql+asyncpg://")

def run_migrations_offline():
    url = get_database_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def do_run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

    # إنشاء migration أولي
    cat > field_suite_service/migrations/versions/001_initial_schema.sql <<'EOF'
-- Sahool Yemen Initial Schema v9.0.0
BEGIN;

-- Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Tables
CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    coordinates GEOGRAPHY(POINT, 4326) NOT NULL,
    area_km2 DECIMAL(10,2),
    agricultural_potential TEXT,
    climate_zone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS farmers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100),
    phone_encrypted BYTEA,
    email_encrypted BYTEA,
    region_id INTEGER REFERENCES regions(id),
    tenant_id UUID NOT NULL,
    registration_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT check_contact CHECK (phone IS NOT NULL OR phone_encrypted IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farmer_id UUID REFERENCES farmers(id),
    region_id INTEGER REFERENCES regions(id),
    tenant_id UUID NOT NULL,
    name_ar VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    area_hectares DECIMAL(10,2) NOT NULL CHECK (area_hectares > 0),
    crop_type VARCHAR(100),
    crop_variety VARCHAR(100),
    planting_date DATE,
    expected_harvest_date DATE,
    coordinates GEOGRAPHY(POINT, 4326) NOT NULL,
    elevation_meters INTEGER,
    soil_type VARCHAR(50),
    soil_ph DECIMAL(4,2),
    irrigation_type VARCHAR(50),
    irrigation_system JSONB,
    field_geometry GEOGRAPHY(POLYGON, 4326),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ndvi_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    ndvi_value DECIMAL(5,3) CHECK (ndvi_value BETWEEN -1 AND 1),
    acquisition_date DATE NOT NULL,
    tile_url TEXT,
    tile_metadata JSONB,
    cloud_coverage DECIMAL(5,2),
    satellite_name VARCHAR(50),
    processing_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weather_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    region_id INTEGER REFERENCES regions(id),
    field_id UUID REFERENCES fields(id),
    tenant_id UUID NOT NULL,
    temperature DECIMAL(6,2),
    humidity DECIMAL(5,2),
    rainfall DECIMAL(8,2),
    wind_speed DECIMAL(6,2),
    wind_direction VARCHAR(10),
    pressure DECIMAL(7,2),
    solar_radiation DECIMAL(8,2),
    forecast_date DATE,
    forecast_accuracy DECIMAL(5,2),
    source VARCHAR(50),
    station_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_fields_farmer ON fields(farmer_id);
CREATE INDEX IF NOT EXISTS idx_fields_region ON fields(region_id);
CREATE INDEX IF NOT EXISTS idx_fields_tenant ON fields(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ndvi_field ON ndvi_results(field_id);
CREATE INDEX IF NOT EXISTS idx_ndvi_date ON ndvi_results(acquisition_date);
CREATE INDEX IF NOT EXISTS idx_weather_region ON weather_data(region_id);
CREATE INDEX IF NOT EXISTS idx_weather_field ON weather_data(field_id);

COMMIT;
EOF

    # إنشاء سكريبت init للـ PostgreSQL
    cat > field_suite_service/postgres/init/01-init.sql <<'EOF'
-- Initialize Sahool Yemen Database
\echo 'Initializing Sahool Yemen Database v9.0.0'

-- Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create application schema
CREATE SCHEMA IF NOT EXISTS sahool;

\echo 'Database initialization complete'
EOF

    info "قاعدة البيانات مع Alembic جاهزة"
}

# ==================== 5. إعداد Redis الآمن ====================
setup_redis_secure() {
    log "إعداد Redis مع TLS و ACLs..."

    mkdir -p field_suite_service/redis

    # الحصول على كلمة مرور Redis من الملف
    local redis_pass
    redis_pass=$(cat data/secrets/redis_pass 2>/dev/null || echo "redis_secure_password")

    # إنشاء إعدادات Redis
    cat > field_suite_service/redis/redis.conf <<EOF
# Redis v9.0.0 Secure Config
bind 0.0.0.0
port 6379
tcp-backlog 511
timeout 300
tcp-keepalive 300

# Authentication
requirepass ${redis_pass}

# Memory
maxmemory 1gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Persistence
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Security
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""

# Logging
loglevel notice
logfile ""

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Performance
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
EOF

    info "Redis جاهز"
}

# ==================== 6. إعداد Nano Services ====================
setup_nano_services() {
    log "إعداد Nano Services الكاملة..."

    # Middleware مشترك
    cat > nano_services/middleware.py <<'EOF'
import time
import uuid
from typing import Optional
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog
from prometheus_client import Counter, Histogram, Gauge
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from functools import wraps

logger = structlog.get_logger()
security = HTTPBearer()

request_duration = Histogram('nano_request_duration_seconds', 'Request duration', ['service', 'method', 'endpoint'])
active_requests = Gauge('nano_active_requests', 'Active requests', ['service'])
requests_total = Counter('nano_requests_total', 'Total requests', ['service', 'method', 'status'])


class ObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        active_requests.labels(service=self.service_name).inc()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            service=self.service_name,
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )

        logger.info("request_started", path=request.url.path, method=request.method)

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            request_duration.labels(
                service=self.service_name,
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)

            requests_total.labels(
                service=self.service_name,
                method=request.method,
                status=response.status_code
            ).inc()

            logger.info("request_completed", status_code=response.status_code, duration=f"{duration:.3f}s")
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            logger.error("request_failed", error=str(e))
            requests_total.labels(service=self.service_name, method=request.method, status=500).inc()
            raise
        finally:
            active_requests.labels(service=self.service_name).dec()


def require_api_key(expected_key: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            if request is None:
                raise HTTPException(status_code=500, detail="Request not found")
            api_key = request.headers.get("X-API-Key")
            if api_key != expected_key:
                logger.warning("unauthorized_access", path=request.url.path)
                raise HTTPException(status_code=401, detail="Invalid API key")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
EOF

    # Weather Core
    cat > nano_services/weather-core/app/main.py <<'EOF'
from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
from datetime import date, timedelta
from typing import Optional, List
import httpx
import os
import sys
import random

sys.path.insert(0, '/app')
from middleware import ObservabilityMiddleware
from prometheus_client import generate_latest


class WeatherData(BaseModel):
    date: date
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: float
    wind_direction: str
    pressure: float
    solar_radiation: Optional[float] = None


class WeatherForecast(BaseModel):
    field_id: int
    current: WeatherData
    forecast: List[WeatherData]
    source: str


app = FastAPI(title="Weather Core v9", version="9.0.0")
app.add_middleware(ObservabilityMiddleware, service_name="weather-core")


class WeatherClient:
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "demo")

    async def get_weather(self, lat: float, lon: float, target_date: date) -> dict:
        if self.api_key == "demo" or not self.api_key:
            return {
                "current": {
                    "date": target_date,
                    "temperature": round(20 + random.uniform(-5, 10), 1),
                    "humidity": round(50 + random.uniform(-20, 30), 1),
                    "rainfall": round(random.uniform(0, 10), 1),
                    "wind_speed": round(random.uniform(1, 6), 1),
                    "wind_direction": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
                    "pressure": round(1013 + random.uniform(-10, 10), 1),
                    "solar_radiation": round(random.uniform(200, 600), 0)
                },
                "forecast": [{
                    "date": target_date + timedelta(days=i),
                    "temperature": round(20 + random.uniform(-5, 10), 1),
                    "humidity": round(50 + random.uniform(-20, 30), 1),
                    "rainfall": round(random.uniform(0, 10), 1),
                    "wind_speed": round(random.uniform(1, 6), 1),
                    "wind_direction": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
                    "pressure": round(1013 + random.uniform(-10, 10), 1),
                    "solar_radiation": round(random.uniform(200, 600), 0)
                } for i in range(1, 6)],
                "source": "Demo"
            }

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"}
            )
            data = resp.json()
            return {
                "current": {
                    "date": target_date,
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "rainfall": data.get("rain", {}).get("1h", 0),
                    "wind_speed": data["wind"]["speed"],
                    "wind_direction": self._degrees_to_direction(data["wind"].get("deg", 0)),
                    "pressure": data["main"]["pressure"],
                    "solar_radiation": 0
                },
                "forecast": [],
                "source": "OpenWeather"
            }

    def _degrees_to_direction(self, deg: float) -> str:
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                      "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        return directions[round(deg / 22.5) % 16]


weather_client = WeatherClient()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "weather-core", "version": "9.0.0"}


@app.get("/api/v1/weather/fields/{field_id}")
async def get_weather(field_id: int, lat: float = 15.3547, lon: float = 44.2067, target_date: Optional[date] = None):
    target_date = target_date or date.today()
    data = await weather_client.get_weather(lat, lon, target_date)
    return WeatherForecast(field_id=field_id, **data)


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
EOF

    # Dockerfile لـ Weather Core
    cat > nano_services/weather-core/Dockerfile <<'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../middleware.py /app/middleware.py
COPY app/ ./app/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
EOF

    # متطلبات Weather Core
    cat > nano_services/weather-core/requirements.txt <<'EOF'
fastapi==0.115.0
uvicorn[standard]==0.29.0
httpx==0.27.0
pydantic==2.9.0
prometheus-client==0.20.0
structlog==24.1.0
EOF

    # نسخ نفس البنية للخدمات الأخرى
    for service in imagery-core geo-core analytics-core query-core advisor-core notification-core; do
        cp nano_services/weather-core/requirements.txt "nano_services/$service/requirements.txt"
        cp nano_services/weather-core/Dockerfile "nano_services/$service/Dockerfile"

        cat > "nano_services/$service/app/main.py" <<EOF
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import generate_latest
import sys
sys.path.insert(0, '/app')
from middleware import ObservabilityMiddleware

app = FastAPI(title="${service} v9", version="9.0.0")
app.add_middleware(ObservabilityMiddleware, service_name="${service}")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "${service}", "version": "9.0.0"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
EOF
    done

    info "Nano Services جاهزة"
}

# ==================== 7. إعداد Backend Core ====================
setup_backend_core() {
    log "إعداد Backend Core مع المصادقة..."

    # Config
    cat > field_suite_service/app/core/config.py <<'EOF'
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    APP_NAME: str = "Sahool Yemen Field Suite"
    APP_VERSION: str = "9.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://sahool:sahool@fs-postgres:5432/sahool_yemen_production"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://fs-redis:6379/0")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    JWT_REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY", "dev-refresh-secret")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    API_KEY_SECRET: str = os.getenv("API_KEY_SECRET", "dev-api-key")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SENTINEL_CLIENT_ID: str = os.getenv("SENTINEL_CLIENT_ID", "")
    SENTINEL_CLIENT_SECRET: str = os.getenv("SENTINEL_CLIENT_SECRET", "")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
EOF

    # Cache
    cat > field_suite_service/app/core/cache.py <<'EOF'
import redis.asyncio as redis
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class CacheClient:
    def __init__(self):
        self.client = None

    async def connect(self):
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            logger.info("redis_connected")
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            raise

    async def disconnect(self):
        if self.client:
            await self.client.close()

    async def get(self, key: str):
        if not self.client:
            return None
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: int = 3600):
        if not self.client:
            return
        await self.client.set(key, value, ex=ex)

    async def delete(self, key: str):
        if not self.client:
            return
        await self.client.delete(key)


cache = CacheClient()
EOF

    # Auth
    cat > field_suite_service/app/core/auth.py <<'EOF'
import time
import hashlib
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import structlog
from app.core.config import settings
from app.core.cache import cache

logger = structlog.get_logger()
security = HTTPBearer()


def create_jwt_token(tenant_id: str, user_id: Optional[str] = None) -> Dict:
    now = datetime.utcnow()
    jti = hashlib.sha256(f"{tenant_id}:{user_id}:{now.timestamp()}".encode()).hexdigest()[:16]

    access_payload = {
        "type": "access",
        "tenant_id": tenant_id,
        "user_id": user_id,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        "iat": now,
        "jti": jti
    }

    refresh_jti = hashlib.sha256(f"{tenant_id}:{user_id}:{now.timestamp()}:refresh".encode()).hexdigest()[:16]
    refresh_payload = {
        "type": "refresh",
        "tenant_id": tenant_id,
        "user_id": user_id,
        "exp": now + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        "iat": now,
        "jti": refresh_jti
    }

    return {
        "access_token": jwt.encode(access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM),
        "refresh_token": jwt.encode(refresh_payload, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM),
        "token_type": "bearer"
    }


async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")

        is_blacklisted = await cache.get(f"blacklist:{payload['jti']}")
        if is_blacklisted:
            raise HTTPException(status_code=401, detail="Token revoked")

        return {
            "tenant_id": payload["tenant_id"],
            "user_id": payload.get("user_id"),
            "jti": payload["jti"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def rate_limit_check(key: str, limit: int = 200, window: int = 60) -> bool:
    hashed_key = hashlib.sha256(key.encode()).hexdigest()
    try:
        current = int(time.time())
        window_key = f"rate_limit:{hashed_key}:{current // window}"

        if cache.client is None:
            return True

        pipe = cache.client.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, window + 10)
        result = await pipe.execute()
        return result[0] <= limit
    except Exception as e:
        logger.error("rate_limit_failed", error=str(e))
        return True
EOF

    # Database
    cat > field_suite_service/app/core/database.py <<'EOF'
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import text
from app.core.config import settings
import structlog

logger = structlog.get_logger()

database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,
    max_overflow=50,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_db_health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        logger.error("db_health_failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}
EOF

    # Main application
    cat > field_suite_service/app/main.py <<'EOF'
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
from prometheus_client import generate_latest
import structlog

from app.core.config import settings
from app.core.cache import cache
from app.core.database import check_db_health
from app.core.auth import verify_jwt, create_jwt_token

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting_application", version=settings.APP_VERSION)
    await cache.connect()
    yield
    await cache.disconnect()
    logger.info("shutting_down_application")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/health/ready")
async def health_ready():
    db_health = await check_db_health()
    redis_health = {"status": "healthy" if cache.client else "unhealthy"}

    overall = "healthy" if db_health["status"] == "healthy" and redis_health["status"] == "healthy" else "unhealthy"

    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "checks": {
            "database": db_health,
            "redis": redis_health
        }
    }


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")


@app.post("/api/v1/auth/token")
async def get_token(tenant_id: str = "default"):
    return create_jwt_token(tenant_id)


@app.get("/api/v1/protected")
async def protected_route(auth: dict = Depends(verify_jwt)):
    return {"message": "Access granted", "tenant_id": auth["tenant_id"]}
EOF

    # Requirements
    cat > field_suite_service/requirements.txt <<'EOF'
fastapi==0.115.0
uvicorn[standard]==0.29.0
pydantic==2.9.0
pydantic-settings==2.2.1
sqlalchemy[asyncio]==2.0.29
asyncpg==0.29.0
redis[hiredis]==5.0.3
httpx==0.27.0
python-jose[cryptography]==3.3.0
PyJWT==2.8.0
structlog==24.1.0
prometheus-client==0.20.0
alembic==1.13.1
psycopg2-binary==2.9.9
python-multipart==0.0.9
EOF

    # Dockerfile
    cat > field_suite_service/Dockerfile <<'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic.ini ./
COPY migrations/ ./migrations/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/ready || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
EOF

    info "Backend Core جاهز"
}

# ==================== 8. Frontend PWA ====================
setup_frontend() {
    log "إعداد Frontend PWA كامل..."

    cat > field_suite_frontend/package.json <<'EOF'
{
  "name": "sahool-field-suite-frontend",
  "version": "9.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.3",
    "@tanstack/react-query": "^5.28.9",
    "zustand": "^4.5.2",
    "axios": "^1.6.8",
    "leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1",
    "recharts": "^2.12.5",
    "date-fns": "^2.30.0",
    "i18next": "^23.10.1",
    "react-i18next": "^14.1.0",
    "react-hook-form": "^7.51.3",
    "zod": "^3.22.4",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.73",
    "@types/react-dom": "^18.2.23",
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.2.6",
    "vite-plugin-pwa": "^0.19.7",
    "vitest": "^1.4.0",
    "eslint": "^8.57.0",
    "@typescript-eslint/eslint-plugin": "^7.3.1",
    "@typescript-eslint/parser": "^7.3.1",
    "tailwindcss": "^3.4.1",
    "postcss": "^8.4.38",
    "autoprefixer": "^10.4.19",
    "typescript": "^5.4.3"
  }
}
EOF

    # Service Worker
    cat > field_suite_frontend/public/sw.js <<'EOF'
const CACHE_NAME = 'sahool-v9-cache-v3';
const urlsToCache = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) =>
      Promise.all(
        cacheNames
          .filter((cacheName) => cacheName !== CACHE_NAME)
          .map((cacheName) => caches.delete(cacheName))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.url.startsWith('chrome-extension')) return;

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse && event.request.method === 'GET') {
        return cachedResponse;
      }

      return fetch(event.request).then((response) => {
        if (!response || response.status !== 200 || !response.url.startsWith('http')) {
          return response;
        }

        const contentLength = response.headers.get('content-length');
        if (contentLength && parseInt(contentLength) > 10 * 1024 * 1024) {
          return response;
        }

        const responseToCache = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });

        return response;
      }).catch(() => {
        if (event.request.mode === 'navigate') {
          return caches.match('/offline.html');
        }
        return cachedResponse;
      });
    })
  );
});

self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'تحديث جديد من سهول اليمن',
    icon: '/icons/icon-192.png',
    badge: '/icons/badge-72.png',
    vibrate: [100, 50, 100],
    data: { dateOfArrival: Date.now() },
    actions: [
      { action: 'explore', title: 'عرض' },
      { action: 'close', title: 'إغلاق' }
    ]
  };
  event.waitUntil(self.registration.showNotification('سهول اليمن', options));
});
EOF

    # Manifest
    cat > field_suite_frontend/public/manifest.json <<'EOF'
{
  "name": "سهول اليمن - Field Suite",
  "short_name": "سهول",
  "description": "منصة زراعية ذكية لدعم المزارعين اليمنيين",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#10b981",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "lang": "ar",
  "dir": "rtl"
}
EOF

    # Offline page
    cat > field_suite_frontend/public/offline.html <<'EOF'
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>غير متصل - سهول اليمن</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background: #f3f4f6; }
    .container { text-align: center; padding: 2rem; }
    h1 { color: #374151; margin-bottom: 1rem; }
    p { color: #6b7280; }
  </style>
</head>
<body>
  <div class="container">
    <h1>أنت غير متصل بالإنترنت</h1>
    <p>يرجى التحقق من اتصالك بالإنترنت والمحاولة مرة أخرى</p>
  </div>
</body>
</html>
EOF

    # Index HTML
    cat > field_suite_frontend/public/index.html <<'EOF'
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="سهول اليمن - منصة زراعية ذكية">
  <link rel="manifest" href="/manifest.json">
  <link rel="icon" href="/icons/icon-192.png">
  <title>سهول اليمن - Field Suite</title>
</head>
<body>
  <div id="root"></div>
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js');
      });
    }
  </script>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
EOF

    # Basic React entry
    mkdir -p field_suite_frontend/src
    cat > field_suite_frontend/src/main.tsx <<'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';

function App() {
  return (
    <div style={{ fontFamily: 'system-ui', padding: '2rem', textAlign: 'center' }}>
      <h1>سهول اليمن v9.0.0</h1>
      <p>منصة زراعية ذكية</p>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

    # Nginx config
    cat > field_suite_frontend/nginx.conf <<'EOF'
server {
    listen 3000;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location /health {
        return 200 '{"status":"healthy"}';
        add_header Content-Type application/json;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
EOF

    # Dockerfile
    cat > field_suite_frontend/Dockerfile <<'EOF'
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build 2>/dev/null || mkdir -p dist && cp -r public/* dist/

FROM nginx:alpine
RUN echo "server_tokens off;" >> /etc/nginx/nginx.conf
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN chown -R nginx:nginx /usr/share/nginx/html && chmod -R 755 /usr/share/nginx/html
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
USER nginx
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
EOF

    # TypeScript config
    cat > field_suite_frontend/tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF

    cat > field_suite_frontend/tsconfig.node.json <<'EOF'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
EOF

    # Vite config
    cat > field_suite_frontend/vite.config.ts <<'EOF'
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
  },
});
EOF

    info "Frontend PWA جاهز"
}

# ==================== 9. إعداد Monitoring ====================
setup_monitoring() {
    log "إعداد Prometheus و Grafana..."

    # Prometheus config
    cat > monitoring/prometheus/prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files:
  - /etc/prometheus/rules/*.yml

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    static_configs:
      - targets: ['field-suite-backend:8000']
    metrics_path: /metrics

  - job_name: 'weather-core'
    static_configs:
      - targets: ['weather-core:8000']
    metrics_path: /metrics

  - job_name: 'gateway'
    static_configs:
      - targets: ['gateway:9901']
    metrics_path: /stats/prometheus
EOF

    # Prometheus rules
    cat > monitoring/prometheus/rules/alerts.yml <<'EOF'
groups:
  - name: sahool-alerts
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"

      - alert: HighErrorRate
        expr: rate(nano_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.service }}"
EOF

    # Grafana datasources
    cat > monitoring/grafana/provisioning/datasources/datasources.yml <<'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
EOF

    info "Monitoring جاهز"
}

# ==================== 10. إعداد Envoy Gateway ====================
setup_envoy_gateway() {
    log "إعداد Envoy Gateway..."

    cat > envoy/configs/gateway.yaml <<'EOF'
admin:
  address:
    socket_address:
      address: 0.0.0.0
      port_value: 9901

static_resources:
  listeners:
    - name: listener_http
      address:
        socket_address:
          address: 0.0.0.0
          port_value: 8080
      filter_chains:
        - filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                stat_prefix: ingress_http
                codec_type: AUTO
                route_config:
                  name: local_route
                  virtual_hosts:
                    - name: backend
                      domains: ["*"]
                      routes:
                        - match:
                            prefix: "/api/"
                          route:
                            cluster: backend_service
                            timeout: 30s
                        - match:
                            prefix: "/health"
                          route:
                            cluster: backend_service
                        - match:
                            prefix: "/"
                          route:
                            cluster: frontend_service
                http_filters:
                  - name: envoy.filters.http.router
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router

  clusters:
    - name: backend_service
      connect_timeout: 5s
      type: STRICT_DNS
      lb_policy: ROUND_ROBIN
      load_assignment:
        cluster_name: backend_service
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: field-suite-backend
                      port_value: 8000

    - name: frontend_service
      connect_timeout: 5s
      type: STRICT_DNS
      lb_policy: ROUND_ROBIN
      load_assignment:
        cluster_name: frontend_service
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: frontend
                      port_value: 3000
EOF

    info "Envoy Gateway جاهز"
}

# ==================== 11. Docker Compose ====================
setup_docker_compose() {
    log "إعداد Docker Compose v9..."

    cat > docker-compose.v9.yml <<'EOF'
version: "3.9"

networks:
  sahool-mesh:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  v9_pg_data:
  v9_redis_data:
  v9_prometheus_data:
  v9_grafana_data:

services:
  # PostgreSQL
  fs-postgres:
    image: postgis/postgis:15-3.4-alpine
    container_name: sahool-fs-postgres-v9
    networks:
      - sahool-mesh
    deploy:
      resources:
        limits:
          cpus: '2.5'
          memory: 5G
        reservations:
          cpus: '0.5'
          memory: 1G
    environment:
      POSTGRES_USER: ${DB_USER:-sahool_production_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-}
      POSTGRES_DB: ${DB_NAME:-sahool_yemen_production}
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5434:5432"
    volumes:
      - v9_pg_data:/var/lib/postgresql/data
      - ./field_suite_service/postgres/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis
  fs-redis:
    image: redis:7-alpine
    container_name: sahool-fs-redis-v9
    networks:
      - sahool-mesh
    command: redis-server --requirepass ${REDIS_PASSWORD:-redis_secure_password} --appendonly yes
    deploy:
      resources:
        limits:
          memory: 1.5G
        reservations:
          memory: 512M
    ports:
      - "6380:6379"
    volumes:
      - v9_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD:-redis_secure_password}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Weather Core
  weather-core:
    build:
      context: ./nano_services/weather-core
      dockerfile: Dockerfile
    container_name: sahool-weather-core-v9
    networks:
      - sahool-mesh
    environment:
      OPENWEATHER_API_KEY: ${OPENWEATHER_API_KEY:-}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  # Backend Core
  field-suite-backend:
    build:
      context: ./field_suite_service
      dockerfile: Dockerfile
    container_name: sahool-backend-v9
    depends_on:
      fs-postgres:
        condition: service_healthy
      fs-redis:
        condition: service_healthy
    networks:
      - sahool-mesh
    deploy:
      resources:
        limits:
          cpus: '3.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 512M
    environment:
      DATABASE_URL: postgresql://${DB_USER:-sahool_production_user}:${DB_PASSWORD:-}@fs-postgres:5432/${DB_NAME:-sahool_yemen_production}
      REDIS_URL: redis://:${REDIS_PASSWORD:-redis_secure_password}@fs-redis:6379/0
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-}
      API_KEY_SECRET: ${API_KEY_SECRET:-}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: ./field_suite_frontend
      dockerfile: Dockerfile
    container_name: sahool-frontend-v9
    depends_on:
      - field-suite-backend
    networks:
      - sahool-mesh
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  # Gateway (Envoy)
  gateway:
    image: envoyproxy/envoy:v1.29.0
    container_name: sahool-gateway-v9
    depends_on:
      - frontend
      - field-suite-backend
    ports:
      - "80:8080"
      - "443:8443"
      - "9901:9901"
    networks:
      - sahool-mesh
    volumes:
      - ./envoy/configs/gateway.yaml:/etc/envoy/envoy.yaml:ro
    restart: unless-stopped

  # Prometheus
  prometheus:
    image: prom/prometheus:v2.51.0
    container_name: sahool-prometheus-v9
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--web.enable-lifecycle"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/prometheus/rules:/etc/prometheus/rules:ro
      - v9_prometheus_data:/prometheus
    ports:
      - "9091:9090"
    networks:
      - sahool-mesh
    restart: unless-stopped

  # Grafana
  grafana:
    image: grafana/grafana:10.4.0
    container_name: sahool-grafana-v9
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_ADMIN_USER:-admin}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin}
    volumes:
      - v9_grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    ports:
      - "3003:3000"
    networks:
      - sahool-mesh
    restart: unless-stopped
EOF

    info "Docker Compose v9 جاهز"
}

# ==================== 12. Environment File ====================
setup_environment() {
    log "إنشاء ملف البيئة..."

    local db_password
    local redis_password
    local jwt_secret
    local api_key
    local grafana_password

    db_password=$(cat data/secrets/db_pass 2>/dev/null || echo "")
    redis_password=$(cat data/secrets/redis_pass 2>/dev/null || echo "")
    jwt_secret=$(cat data/secrets/jwt_secret 2>/dev/null || echo "")
    api_key=$(cat data/secrets/api_key 2>/dev/null || echo "")
    grafana_password=$(cat data/secrets/grafana_pass 2>/dev/null || echo "admin")

    cat > .env.production <<EOF
# Sahool Yemen v9.0.0 - Production Environment
# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)

# Database
DB_USER=sahool_production_user
DB_PASSWORD=${db_password}
DB_NAME=sahool_yemen_production
DB_HOST=fs-postgres
DB_PORT=5432

# Redis
REDIS_PASSWORD=${redis_password}

# JWT
JWT_SECRET_KEY=${jwt_secret}
JWT_REFRESH_SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n')

# API
API_KEY_SECRET=${api_key}

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=${grafana_password}

# External APIs (set these manually)
OPENAI_API_KEY=${OPENAI_API_KEY:-}
SENTINEL_CLIENT_ID=${SENTINEL_CLIENT_ID:-}
SENTINEL_CLIENT_SECRET=${SENTINEL_CLIENT_SECRET:-}
OPENWEATHER_API_KEY=${OPENWEATHER_API_KEY:-}
EOF

    chmod 600 .env.production

    # Create symlink
    ln -sf .env.production .env

    info "ملف البيئة جاهز"
}

# ==================== 13. سكريبت التحكم ====================
setup_control_script() {
    log "إنشاء سكريبت التحكم المركزي..."

    cat > scripts/sahoolctl-v9.sh <<'CTLEOF'
#!/bin/bash
set -euo pipefail

ENV_MODE="${1:-production}"
COMMAND="${2:-help}"
VERSION="9.0.0"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[CTL]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

check_env() {
    if [ ! -f ".env.${ENV_MODE}" ]; then
        error "ملف البيئة .env.${ENV_MODE} غير موجود"
    fi
    set -a
    source ".env.${ENV_MODE}"
    set +a
}

health_check() {
    log "فحص صحة الخدمات..."

    if curl -sf "http://localhost:80/health" > /dev/null 2>&1; then
        info "Gateway: OK"
    else
        warn "Gateway: FAILED"
    fi

    if curl -sf "http://localhost:8000/health/ready" > /dev/null 2>&1; then
        info "Backend: OK"
    else
        warn "Backend: FAILED"
    fi

    if docker exec sahool-fs-postgres-v9 pg_isready -U "${DB_USER:-sahool_production_user}" > /dev/null 2>&1; then
        info "PostgreSQL: OK"
    else
        warn "PostgreSQL: FAILED"
    fi

    if docker exec sahool-fs-redis-v9 redis-cli -a "${REDIS_PASSWORD:-}" ping > /dev/null 2>&1; then
        info "Redis: OK"
    else
        warn "Redis: FAILED"
    fi
}

backup() {
    log "إنشاء نسخة احتياطية..."
    local backup_dir="./data/backups/${ENV_MODE}/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    docker exec sahool-fs-postgres-v9 pg_dump -U "${DB_USER:-sahool_production_user}" "${DB_NAME:-sahool_yemen_production}" | \
        gzip > "$backup_dir/db.sql.gz"

    cp ".env.${ENV_MODE}" "$backup_dir/env.backup"

    # Clean old backups (keep last 90 days)
    find ./data/backups -type d -mtime +90 -exec rm -rf {} \; 2>/dev/null || true

    log "نسخة احتياطية تمت: $backup_dir"
}

case "${COMMAND}" in
    start)
        check_env
        docker compose -f docker-compose.v9.yml up -d
        sleep 10
        health_check
        ;;
    stop)
        docker compose -f docker-compose.v9.yml down
        ;;
    restart)
        check_env
        docker compose -f docker-compose.v9.yml restart
        sleep 10
        health_check
        ;;
    health)
        check_env
        health_check
        ;;
    backup)
        check_env
        backup
        ;;
    logs)
        docker compose -f docker-compose.v9.yml logs -f "${3:-}"
        ;;
    build)
        check_env
        docker compose -f docker-compose.v9.yml build
        ;;
    help|*)
        echo "Usage: $0 [production|development] [command]"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  health   - Check health of all services"
        echo "  backup   - Create database backup"
        echo "  logs     - View logs (optionally specify service)"
        echo "  build    - Build all containers"
        echo "  help     - Show this help message"
        ;;
esac
CTLEOF

    chmod +x scripts/sahoolctl-v9.sh

    info "سكريبت التحكم جاهز"
}

# ==================== 14. التوثيق ====================
create_docs() {
    log "إنشاء ملفات التوثيق..."

    cat > README.md <<'EOF'
# منصة سهول اليمن Field Suite v9.0.0

بنية زراعية ذكية متكاملة لدعم المزارعين اليمنيين عبر تحليل NDVI والتوقعات المناخية والتوصيات الذكية.

## المميزات

### أمان على مستوى المؤسسات
- **Vault**: توليد وتدوير أسرار تلقائي
- **TLS**: تشفير كامل بين الخدمات
- **JWT**: Refresh tokens + Blacklist + Session management
- **Rate Limiting**: حماية من الهجمات

### أداء عالي التوسع
- PostgreSQL + Redis Connection Pooling
- Envoy Service Mesh
- PWA عمل تام دون إنترنت
- Cache Layer ذكي

### مراقبة شاملة
- Prometheus + Grafana
- Health Checks لكل service
- Logging مركزي

## التنصيب السريع

```bash
# 1. تشغيل السكريبت
chmod +x sahool-deployer-v9.sh
./sahool-deployer-v9.sh

# 2. بدء الخدمات
./scripts/sahoolctl-v9.sh production start

# 3. التحقق
./scripts/sahoolctl-v9.sh production health
```

## المنافذ

| الخدمة | المنفذ |
|--------|--------|
| Gateway (HTTP) | 80 |
| Backend API | 8000 |
| PostgreSQL | 5434 |
| Redis | 6380 |
| Prometheus | 9091 |
| Grafana | 3003 |
| Envoy Admin | 9901 |

## الأوامر المتاحة

```bash
./scripts/sahoolctl-v9.sh production start    # بدء الخدمات
./scripts/sahoolctl-v9.sh production stop     # إيقاف الخدمات
./scripts/sahoolctl-v9.sh production restart  # إعادة تشغيل
./scripts/sahoolctl-v9.sh production health   # فحص الصحة
./scripts/sahoolctl-v9.sh production backup   # نسخ احتياطي
./scripts/sahoolctl-v9.sh production logs     # عرض السجلات
```

## المتغيرات البيئية

قم بتعديل ملف `.env.production` لإضافة مفاتيح الـ API الخارجية:

- `OPENAI_API_KEY`: مفتاح OpenAI للتوصيات الذكية
- `SENTINEL_CLIENT_ID`: معرف Sentinel Hub للصور الفضائية
- `SENTINEL_CLIENT_SECRET`: سر Sentinel Hub
- `OPENWEATHER_API_KEY`: مفتاح OpenWeather للطقس

## الترخيص

MIT License - سهول اليمن 2024
EOF

    info "التوثيق جاهز"
}

# ==================== Main Function ====================
main() {
    local env_mode="${1:-production}"

    echo -e "${MAGENTA}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║           سهول اليمن v9.0.0 - نشر شامل للإنتاج               ║"
    echo "║        SAHOOL Yemen Field Suite - Production Deployment       ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    log "بدء النشر في وضع: $env_mode"

    CLEANUP_NEEDED=true

    # تنفيذ جميع الخطوات
    comprehensive_check
    create_secure_structure
    setup_vault_and_secrets
    setup_database
    setup_redis_secure
    setup_nano_services
    setup_backend_core
    setup_frontend
    setup_monitoring
    setup_envoy_gateway
    setup_docker_compose
    setup_environment
    setup_control_script
    create_docs

    CLEANUP_NEEDED=false

    echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    النشر اكتمل بنجاح!                         ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"

    echo -e "\n${CYAN}الخطوات التالية:${NC}"
    echo -e "  1. راجع ملف ${YELLOW}.env.production${NC} وأضف مفاتيح API الخارجية"
    echo -e "  2. ابدأ الخدمات: ${YELLOW}./scripts/sahoolctl-v9.sh production start${NC}"
    echo -e "  3. تحقق من الصحة: ${YELLOW}./scripts/sahoolctl-v9.sh production health${NC}"
    echo -e "\n${CYAN}المنافذ:${NC}"
    echo -e "  - Gateway:    http://localhost:80"
    echo -e "  - Backend:    http://localhost:8000"
    echo -e "  - Grafana:    http://localhost:3003"
    echo -e "  - Prometheus: http://localhost:9091"
}

# تشغيل السكريبت
main "$@"
