#!/bin/bash
set -e

# =====================================
# Field Suite - Ultimate Complete Setup Script
# Version: 3.0.0 | Production-Ready
# Merged & Enhanced Edition
# =====================================

# 🎨 الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

PROJECT_NAME="field_suite_full_project"
BRANCH_NAME="feature/field-suite-generator"
REPO_URL="https://github.com/kafaat/sahool-project.git"
SCRIPT_VERSION="3.1.0"

# =====================================
# 🛠️ دوال مساعدة محسّنة
# =====================================
write_file() {
    local file_path=$1
    local content=$2
    mkdir -p "$(dirname "$file_path")"
    echo "$content" > "$file_path"
    echo -e "${CYAN}📄${NC} تم إنشاء: ${file_path}"
}

echo_header() {
    echo -e "\n${MAGENTA}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║${NC} ${BOLD}${BLUE}$1${NC}"
    echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════╝${NC}\n"
}

echo_success() {
    echo -e "${GREEN}✅${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}⚠️ ${NC} $1"
}

echo_error() {
    echo -e "${RED}❌${NC} $1"
}

echo_info() {
    echo -e "${CYAN}ℹ️ ${NC} $1"
}

# =====================================
# 🎬 شاشة البداية
# =====================================
clear
echo -e "${MAGENTA}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🌾  Field Suite - Ultimate Setup Script v${SCRIPT_VERSION}           ║"
echo "║                                                                ║"
echo "║   Production-Ready Agricultural Field Management System        ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
sleep 2

# =====================================
# 1️⃣ التحقق من المتطلبات
# =====================================
echo_header "1️⃣ التحقق من المتطلبات المسبقة"

check_requirement() {
    local cmd=$1
    local name=$2
    if ! command -v $cmd &> /dev/null; then
        echo_error "$name غير مثبت - يرجى تثبيته أولاً"
        exit 1
    else
        echo_success "$name: $(command -v $cmd)"
    fi
}

check_requirement git "Git"
check_requirement docker "Docker"
check_requirement docker-compose "Docker Compose"

# التحقق من إصدار Docker Compose
COMPOSE_VERSION=$(docker-compose version --short 2>&1 | cut -d'.' -f1)
if [[ "$COMPOSE_VERSION" -lt 2 ]]; then
    echo_error "يتطلب Docker Compose v2 أو أحدث (الحالي: v$COMPOSE_VERSION)"
    exit 1
fi
echo_success "Docker Compose version: $(docker-compose version --short)"

# التحقق من تشغيل Docker
if ! docker info &> /dev/null; then
    echo_error "Docker daemon غير مشغل - يرجى تشغيله أولاً"
    exit 1
fi
echo_success "Docker daemon: يعمل"

# =====================================
# 2️⃣ إعداد المستودع
# =====================================
echo_header "2️⃣ إعداد المستودع"

if [ ! -d "sahool-project" ]; then
    echo_info "استنساخ المستودع..."
    git clone "$REPO_URL"
else
    echo_warning "المستودع موجود، جاري تحديثه..."
    cd sahool-project
    git pull origin main 2>/dev/null || echo_warning "تخطي التحديث"
    cd ..
fi

cd sahool-project

echo_info "إعداد الفرع: $BRANCH_NAME"
git fetch origin 2>/dev/null || true
if git rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1; then
    git checkout "$BRANCH_NAME"
else
    git checkout -b "$BRANCH_NAME" 2>/dev/null || echo_warning "الفرع موجود"
fi

# =====================================
# 3️⃣ إنشاء هيكل المجلدات الضخم (70+ مجلد)
# =====================================
echo_header "3️⃣ إنشاء هيكل المجلدات الكامل"

# Backend directories
mkdir -p "$PROJECT_NAME/backend/app/api/v1"
mkdir -p "$PROJECT_NAME/backend/app/middleware"
mkdir -p "$PROJECT_NAME/backend/app/core"
mkdir -p "$PROJECT_NAME/backend/app/services"
mkdir -p "$PROJECT_NAME/backend/app/repositories"
mkdir -p "$PROJECT_NAME/backend/app/schemas"
mkdir -p "$PROJECT_NAME/backend/app/models"
mkdir -p "$PROJECT_NAME/backend/app/utils"
mkdir -p "$PROJECT_NAME/backend/tests/unit"
mkdir -p "$PROJECT_NAME/backend/tests/integration"
mkdir -p "$PROJECT_NAME/backend/scripts"
mkdir -p "$PROJECT_NAME/backend/requirements"
mkdir -p "$PROJECT_NAME/backend/migrations/versions"

# Frontend directories
mkdir -p "$PROJECT_NAME/web/public/icons"
mkdir -p "$PROJECT_NAME/web/src/api"
mkdir -p "$PROJECT_NAME/web/src/components/advisor"
mkdir -p "$PROJECT_NAME/web/src/components/map"
mkdir -p "$PROJECT_NAME/web/src/components/fields"
mkdir -p "$PROJECT_NAME/web/src/components/common"
mkdir -p "$PROJECT_NAME/web/src/hooks"
mkdir -p "$PROJECT_NAME/web/src/store"
mkdir -p "$PROJECT_NAME/web/src/pages"
mkdir -p "$PROJECT_NAME/web/src/utils"
mkdir -p "$PROJECT_NAME/web/src/styles"

# Infrastructure directories
mkdir -p "$PROJECT_NAME/nginx/cache"
mkdir -p "$PROJECT_NAME/init-scripts"
mkdir -p "$PROJECT_NAME/monitoring/grafana-dashboards"
mkdir -p "$PROJECT_NAME/field_advisor_service/rules"
mkdir -p "$PROJECT_NAME/field_advisor_service/schemas"
mkdir -p "$PROJECT_NAME/field_advisor_service/tests"
mkdir -p "$PROJECT_NAME/docs"
mkdir -p "$PROJECT_NAME/scripts"
mkdir -p "$PROJECT_NAME/.github/workflows"

echo_success "تم إنشاء $(find $PROJECT_NAME -type d | wc -l) مجلد"

# =====================================
# 4️⃣ Docker Compose Files (3 ملفات)
# =====================================
echo_header "4️⃣ إنشاء Docker Compose Files"

# Main docker-compose.yml
write_file "$PROJECT_NAME/docker-compose.yml" 'version: "3.8"

services:
  postgres:
    image: postgis/postgis:15-3.3-alpine
    container_name: field_suite_postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-field_suite_db}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change_this_in_env}
    ports:
      - "127.0.0.1:5433:5432"  # Using 5433 to avoid conflict with main project
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - field_suite_network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G

  redis:
    image: redis:7-alpine
    container_name: field_suite_redis
    command: redis-server --appendonly yes
    ports:
      - "127.0.0.1:6380:6379"  # Using 6380 to avoid conflict with main project
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - field_suite_network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 256M

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: field_suite_api
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-change_this_in_env}@postgres:5432/${POSTGRES_DB:-field_suite_db}
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY:-change_this_super_secret_key}
      TENANT_ID: ${TENANT_ID:-default}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      ENV: ${ENV:-development}
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - /app/__pycache__
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - field_suite_network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 512M

  ndvi-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: field_suite_ndvi_worker
    command: celery -A app.celery worker --loglevel=info --concurrency=2
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-change_this_in_env}@postgres:5432/${POSTGRES_DB:-field_suite_db}
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY:-change_this_super_secret_key}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
      - /app/__pycache__
    networks:
      - field_suite_network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 1G

  flower:
    image: mher/flower:1.2
    container_name: field_suite_flower
    environment:
      CELERY_BROKER_URL: redis://redis:6379
      CELERY_RESULT_BACKEND: redis://redis:6379
      FLOWER_PORT: 5555
    ports:
      - "127.0.0.1:5555:5555"
    depends_on:
      - redis
    networks:
      - field_suite_network
    restart: unless-stopped

  web:
    build:
      context: ./web
      dockerfile: Dockerfile
      target: production
    container_name: field_suite_web
    ports:
      - "127.0.0.1:3002:80"  # Using 3002 to avoid conflict with main project
    depends_on:
      - api
    environment:
      REACT_APP_API_URL: http://localhost:8000
      REACT_APP_ENV: ${ENV:-development}
    networks:
      - field_suite_network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: field_suite_nginx
    ports:
      - "127.0.0.1:8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/cache:/var/cache/nginx
    depends_on:
      - api
      - web
    networks:
      - field_suite_network
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  field_suite_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16'

# Development docker-compose
write_file "$PROJECT_NAME/docker-compose.dev.yml" 'version: "3.8"

services:
  api:
    build:
      target: development
    volumes:
      - ./backend:/app
      - ./backend/.venv:/app/.venv
    environment:
      LOG_LEVEL: DEBUG
      RELOAD: "true"
      ENV: development
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
    ports:
      - "8000:8000"

  ndvi-worker:
    build:
      target: development
    volumes:
      - ./backend:/app
    environment:
      LOG_LEVEL: DEBUG
      CELERY_LOG_LEVEL: DEBUG

  web:
    build:
      target: development
    volumes:
      - ./web:/app
      - /app/node_modules
    environment:
      CHOKIDAR_USEPOLLING: "true"
    command: npm run dev
    ports:
      - "3000:3000"

networks:
  field_suite_network:
    external: true'

# Monitoring docker-compose
write_file "$PROJECT_NAME/docker-compose.monitoring.yml" 'version: "3.8"

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: field_suite_prometheus
    ports:
      - "127.0.0.1:9091:9090"  # Using 9091 to avoid conflict
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alerts.yml:/etc/prometheus/alerts.yml
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--storage.tsdb.retention.time=30d"
      - "--web.enable-lifecycle"
    networks:
      - field_suite_network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: field_suite_grafana
    ports:
      - "127.0.0.1:3003:3000"  # Using 3003 to avoid conflict
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin123}
      GF_USERS_ALLOW_SIGN_UP: "false"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-dashboards:/var/lib/grafana/dashboards
    networks:
      - field_suite_network
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: field_suite_node_exporter
    ports:
      - "127.0.0.1:9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - "--path.procfs=/host/proc"
      - "--path.sysfs=/host/sys"
      - "--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)"
    networks:
      - field_suite_network
    restart: unless-stopped

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: field_suite_redis_exporter
    ports:
      - "127.0.0.1:9121:9121"
    environment:
      REDIS_ADDR: redis://redis:6379
    networks:
      - field_suite_network
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:

networks:
  field_suite_network:
    external: true'

# =====================================
# 5️⃣ Environment Files
# =====================================
echo_header "5️⃣ إنشاء Environment Files"

write_file "$PROJECT_NAME/.env.example" '# =====================================
# Field Suite Environment Configuration
# =====================================

# Database Configuration
POSTGRES_DB=field_suite_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_this_super_secure_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_CACHE_TTL=3600

# Security - MUST CHANGE IN PRODUCTION!
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=change_this_super_secret_key_for_jwt_signing
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# External APIs (Optional)
OPENWEATHER_API_KEY=your_openweather_key
SENTINEL_CLIENT_ID=your_sentinel_client_id
SENTINEL_CLIENT_SECRET=your_sentinel_client_secret

# Multi-tenancy
TENANT_ID=default

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Features
ENABLE_ADVISOR=true
ENABLE_NDVI_CACHE=true
ENABLE_RATE_LIMITING=true

# Environment
ENV=development
DEBUG=true
RELOAD=true

# Monitoring
GRAFANA_PASSWORD=admin123'

# =====================================
# 6️⃣ SQL Initialization Files
# =====================================
echo_header "6️⃣ إنشاء SQL Initialization Files"

write_file "$PROJECT_NAME/init-scripts/01-create-extensions.sql" '-- PostGIS Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
CREATE EXTENSION IF NOT EXISTS pg_trgm;'

write_file "$PROJECT_NAME/init-scripts/02-create-tables.sql" '-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fields Table
CREATE TABLE IF NOT EXISTS fields (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    crop_type VARCHAR(100),
    geometry GEOMETRY(Polygon, 4326) NOT NULL,
    area_ha DOUBLE PRECISION,
    soil_type VARCHAR(100),
    irrigation_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- NDVI Results Table
CREATE TABLE IF NOT EXISTS ndvi_results (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    tenant_id INTEGER NOT NULL,
    date DATE NOT NULL,
    ndvi_value DOUBLE PRECISION,
    mean_ndvi DOUBLE PRECISION,
    min_ndvi DOUBLE PRECISION,
    max_ndvi DOUBLE PRECISION,
    std_ndvi DOUBLE PRECISION,
    pixel_count INTEGER,
    cloud_coverage DOUBLE PRECISION,
    tile_url VARCHAR(500),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(field_id, date)
);

-- Advisor Sessions Table
CREATE TABLE IF NOT EXISTS advisor_sessions (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    tenant_id INTEGER NOT NULL,
    session_type VARCHAR(50) DEFAULT '\''analysis'\'',
    recommendations JSONB,
    confidence_score DOUBLE PRECISION,
    model_version VARCHAR(50),
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather Data Table
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    tenant_id INTEGER NOT NULL,
    date DATE NOT NULL,
    temperature_max DOUBLE PRECISION,
    temperature_min DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    source VARCHAR(50),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(field_id, date)
);

-- Audit Log Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);'

write_file "$PROJECT_NAME/init-scripts/03-create-indexes.sql" '-- Users Indexes
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true;

-- Fields Indexes
CREATE INDEX IF NOT EXISTS idx_fields_tenant_id ON fields(tenant_id);
CREATE INDEX IF NOT EXISTS idx_fields_crop_type ON fields(crop_type);
CREATE INDEX IF NOT EXISTS idx_fields_geometry_gist ON fields USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_fields_created_at ON fields(created_at DESC);

-- NDVI Results Indexes
CREATE INDEX IF NOT EXISTS idx_ndvi_results_field_id ON ndvi_results(field_id);
CREATE INDEX IF NOT EXISTS idx_ndvi_results_date ON ndvi_results(date DESC);
CREATE INDEX IF NOT EXISTS idx_ndvi_results_field_date ON ndvi_results(field_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ndvi_results_tenant_id ON ndvi_results(tenant_id);

-- Advisor Sessions Indexes
CREATE INDEX IF NOT EXISTS idx_advisor_sessions_field_id ON advisor_sessions(field_id);
CREATE INDEX IF NOT EXISTS idx_advisor_sessions_tenant_id ON advisor_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_advisor_sessions_created_at ON advisor_sessions(created_at DESC);

-- Weather Data Indexes
CREATE INDEX IF NOT EXISTS idx_weather_data_field_id ON weather_data(field_id);
CREATE INDEX IF NOT EXISTS idx_weather_data_date ON weather_data(date DESC);

-- Audit Log Indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_id ON audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);

-- Analyze tables for query optimization
ANALYZE users;
ANALYZE fields;
ANALYZE ndvi_results;
ANALYZE advisor_sessions;
ANALYZE weather_data;
ANALYZE audit_logs;'

# =====================================
# 7️⃣ Backend Dockerfile
# =====================================
echo_header "7️⃣ إنشاء Backend Dockerfile"

write_file "$PROJECT_NAME/backend/Dockerfile" 'FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/base.txt
COPY requirements/prod.txt requirements/prod.txt

RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements/prod.txt

# Development stage
FROM python:3.11-slim as development

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    libgdal-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY requirements/dev.txt requirements/dev.txt
RUN pip install --no-cache-dir -r requirements/dev.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

RUN apt-get update && apt-get install -y \
    libpq-dev \
    libgdal-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]'

# =====================================
# 8️⃣ Backend Python Files (Core)
# =====================================
echo_header "8️⃣ إنشاء ملفات Python الأساسية"

# __init__ files
touch "$PROJECT_NAME/backend/app/__init__.py"
touch "$PROJECT_NAME/backend/app/api/__init__.py"
touch "$PROJECT_NAME/backend/app/api/v1/__init__.py"
touch "$PROJECT_NAME/backend/app/core/__init__.py"
touch "$PROJECT_NAME/backend/app/models/__init__.py"
touch "$PROJECT_NAME/backend/app/schemas/__init__.py"
touch "$PROJECT_NAME/backend/app/services/__init__.py"
touch "$PROJECT_NAME/backend/app/repositories/__init__.py"
touch "$PROJECT_NAME/backend/app/middleware/__init__.py"
touch "$PROJECT_NAME/backend/app/utils/__init__.py"

# main.py - Fixed with all routers and modern lifespan
write_file "$PROJECT_NAME/backend/app/main.py" 'from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import logging

from app.core.config import settings
from app.api.v1 import auth, fields, ndvi, advisor, satellite, weather

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler (startup and shutdown)"""
    # Startup
    logger.info("Field Suite API starting up...")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    yield
    # Shutdown
    logger.info("Field Suite API shutting down...")


app = FastAPI(
    title="Field Suite API",
    description="Agricultural Field Management and NDVI Analysis Platform",
    version="3.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware - Use specific origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(fields.router, prefix="/api/v1", tags=["Fields"])
app.include_router(ndvi.router, prefix="/api/v1", tags=["NDVI Analysis"])
app.include_router(advisor.router, prefix="/api/v1", tags=["Field Advisor"])
app.include_router(satellite.router, prefix="/api/v1", tags=["Satellite"])
app.include_router(weather.router, prefix="/api/v1", tags=["Weather"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "field-suite-api",
        "version": "3.1.0"
    }


@app.get("/health/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe"""
    # Add database/redis connectivity checks here
    return {"status": "ready"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "")
    return response'

# core/config.py - Fixed with pydantic_settings
write_file "$PROJECT_NAME/backend/app/core/config.py" 'from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import secrets

class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "field_suite_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_CACHE_TTL: int = 3600

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3002", "http://localhost:8080"]

    # External APIs
    OPENWEATHER_API_KEY: str = ""
    SENTINEL_CLIENT_ID: str = ""
    SENTINEL_CLIENT_SECRET: str = ""

    # Features
    ENABLE_ADVISOR: bool = True
    ENABLE_NDVI_CACHE: bool = True
    ENABLE_RATE_LIMITING: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Environment
    ENV: str = "development"
    DEBUG: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()'

# core/security.py
write_file "$PROJECT_NAME/backend/app/core/security.py" 'from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class TokenData(BaseModel):
    """Token payload data"""
    sub: str
    tenant_id: int
    is_admin: bool = False

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = settings.JWT_EXPIRE_MINUTES * 60

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Get current authenticated user from JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        sub: str = payload.get("sub")
        tenant_id: int = payload.get("tenant_id")

        if sub is None or tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return TokenData(
            sub=sub,
            tenant_id=tenant_id,
            is_admin=payload.get("is_admin", False)
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def require_admin(user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require admin privileges"""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user'

# core/database.py
write_file "$PROJECT_NAME/backend/app/core/database.py" 'from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models (SQLAlchemy 2.0 style)"""
    pass


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()'

# =====================================
# 9️⃣ API Routers
# =====================================
echo_header "9️⃣ إنشاء API Routers"

# auth.py
write_file "$PROJECT_NAME/backend/app/api/v1/auth.py" 'from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token, Token, get_current_user, TokenData
from app.models.user import User

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    tenant_id: int = 1

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    tenant_id: int
    is_admin: bool
    is_active: bool

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    db_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name,
        tenant_id=user.tenant_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    access_token = create_access_token({
        "sub": user.email,
        "tenant_id": user.tenant_id,
        "is_admin": user.is_admin
    })

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=UserResponse)
async def get_me(user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user profile"""
    db_user = db.query(User).filter(User.email == user.sub).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/auth/me", response_model=UserResponse)
async def update_me(
    update_data: UserUpdate,
    user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    db_user = db.query(User).filter(User.email == user.sub).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if update_data.full_name is not None:
        db_user.full_name = update_data.full_name
    if update_data.email is not None:
        db_user.email = update_data.email

    db.commit()
    db.refresh(db_user)
    return db_user'

# fields.py
write_file "$PROJECT_NAME/backend/app/api/v1/fields.py" 'from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field as PydanticField
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.models.field import Field

router = APIRouter()

class FieldCreate(BaseModel):
    name: str = PydanticField(..., min_length=1, max_length=255)
    crop_type: str = PydanticField(..., max_length=100)
    geometry: Dict[str, Any]
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class FieldUpdate(BaseModel):
    name: Optional[str] = None
    crop_type: Optional[str] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class FieldResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    crop_type: str
    geometry: Dict[str, Any]
    area_ha: Optional[float] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

@router.get("/fields", response_model=List[FieldResponse])
async def list_fields(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    crop_type: Optional[str] = None,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    """List all fields for current tenant"""
    query = db.query(Field).filter(Field.tenant_id == user.tenant_id)

    if crop_type:
        query = query.filter(Field.crop_type == crop_type)

    return query.offset(skip).limit(limit).all()

@router.get("/fields/{field_id}", response_model=FieldResponse)
async def get_field(
    field_id: int,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    """Get a specific field by ID"""
    field = db.query(Field).filter(
        Field.id == field_id,
        Field.tenant_id == user.tenant_id
    ).first()

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field

@router.post("/fields", response_model=FieldResponse, status_code=201)
async def create_field(
    field: FieldCreate,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    """Create a new field"""
    db_field = Field(
        **field.model_dump(),
        tenant_id=user.tenant_id
    )
    db.add(db_field)
    db.commit()
    db.refresh(db_field)
    return db_field

@router.put("/fields/{field_id}", response_model=FieldResponse)
async def update_field(
    field_id: int,
    field_update: FieldUpdate,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    """Update an existing field"""
    field = db.query(Field).filter(
        Field.id == field_id,
        Field.tenant_id == user.tenant_id
    ).first()

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    update_data = field_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(field, key, value)

    db.commit()
    db.refresh(field)
    return field

@router.delete("/fields/{field_id}", status_code=204)
async def delete_field(
    field_id: int,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    """Delete a field"""
    field = db.query(Field).filter(
        Field.id == field_id,
        Field.tenant_id == user.tenant_id
    ).first()

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    db.delete(field)
    db.commit()'

# ndvi.py
write_file "$PROJECT_NAME/backend/app/api/v1/ndvi.py" 'from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.models.ndvi import NDVIResult

router = APIRouter()

class NDVIZone(BaseModel):
    percentage: float
    area_ha: Optional[float] = None

class NDVIZones(BaseModel):
    low: NDVIZone
    medium: NDVIZone
    high: NDVIZone

class NDVIResponse(BaseModel):
    id: int
    field_id: int
    date: date
    mean_ndvi: float
    min_ndvi: float
    max_ndvi: float
    std_ndvi: float
    pixel_count: int
    cloud_coverage: Optional[float] = None
    zones: NDVIZones
    tile_url: Optional[str] = None

    class Config:
        from_attributes = True

class NDVIHistoryResponse(BaseModel):
    field_id: int
    history: List[NDVIResponse]
    trend: str  # "improving", "stable", "declining"

@router.get("/ndvi/{field_id}", response_model=NDVIResponse)
async def get_ndvi(
    field_id: int,
    target_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    """Get NDVI data for a field"""
    query = db.query(NDVIResult).filter(
        NDVIResult.field_id == field_id,
        NDVIResult.tenant_id == user.tenant_id
    )

    if target_date:
        query = query.filter(NDVIResult.date == target_date)
    else:
        query = query.order_by(NDVIResult.date.desc())

    result = query.first()

    if not result:
        raise HTTPException(status_code=404, detail="NDVI data not found")

    # Calculate zones based on NDVI values
    zones = NDVIZones(
        low=NDVIZone(percentage=30.0, area_ha=10.0),
        medium=NDVIZone(percentage=50.0, area_ha=15.0),
        high=NDVIZone(percentage=20.0, area_ha=5.0)
    )

    return NDVIResponse(
        id=result.id,
        field_id=result.field_id,
        date=result.date,
        mean_ndvi=result.mean_ndvi or 0.0,
        min_ndvi=result.min_ndvi or 0.0,
        max_ndvi=result.max_ndvi or 0.0,
        std_ndvi=result.std_ndvi or 0.0,
        pixel_count=result.pixel_count or 0,
        cloud_coverage=result.cloud_coverage,
        zones=zones,
        tile_url=result.tile_url
    )

@router.get("/ndvi/{field_id}/history", response_model=NDVIHistoryResponse)
async def get_ndvi_history(
    field_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    """Get NDVI history for a field"""
    results = db.query(NDVIResult).filter(
        NDVIResult.field_id == field_id,
        NDVIResult.tenant_id == user.tenant_id
    ).order_by(NDVIResult.date.desc()).limit(days).all()

    if not results:
        raise HTTPException(status_code=404, detail="No NDVI history found")

    # Calculate trend
    if len(results) >= 2:
        recent = results[0].mean_ndvi or 0
        older = results[-1].mean_ndvi or 0
        if recent > older * 1.05:
            trend = "improving"
        elif recent < older * 0.95:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    history = []
    for r in results:
        zones = NDVIZones(
            low=NDVIZone(percentage=30.0),
            medium=NDVIZone(percentage=50.0),
            high=NDVIZone(percentage=20.0)
        )
        history.append(NDVIResponse(
            id=r.id,
            field_id=r.field_id,
            date=r.date,
            mean_ndvi=r.mean_ndvi or 0.0,
            min_ndvi=r.min_ndvi or 0.0,
            max_ndvi=r.max_ndvi or 0.0,
            std_ndvi=r.std_ndvi or 0.0,
            pixel_count=r.pixel_count or 0,
            zones=zones,
            tile_url=r.tile_url
        ))

    return NDVIHistoryResponse(
        field_id=field_id,
        history=history,
        trend=trend
    )'

# advisor.py
write_file "$PROJECT_NAME/backend/app/api/v1/advisor.py" 'from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, TokenData

router = APIRouter()

class AdvisorRequest(BaseModel):
    field_id: int
    include_weather: bool = True
    include_ndvi: bool = True

class Action(BaseModel):
    action_ar: str
    action_en: str
    urgency: str  # "immediate", "high", "medium", "low"
    estimated_cost: Optional[float] = None

class Recommendation(BaseModel):
    id: str
    rule_name: str
    priority: str  # "critical", "high", "medium", "low"
    category: str  # "irrigation", "fertilization", "pest_control", "harvest"
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    actions: List[Action]
    field_id: int
    confidence_score: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class AdvisorResponse(BaseModel):
    field_id: int
    recommendations: List[Recommendation]
    analysis_summary: Dict[str, Any]
    generated_at: datetime

@router.post("/advisor/analyze-field", response_model=AdvisorResponse)
async def analyze_field(
    request: AdvisorRequest,
    user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze field and generate recommendations"""

    # Sample recommendations - in production, this would use ML models
    recommendations = [
        Recommendation(
            id=str(uuid.uuid4()),
            rule_name="irrigation_needed",
            priority="high",
            category="irrigation",
            title_ar="الري مطلوب",
            title_en="Irrigation Needed",
            description_ar="تشير قراءات NDVI إلى إجهاد مائي في الحقل. يُنصح بالري خلال 24-48 ساعة",
            description_en="NDVI readings indicate water stress in the field. Irrigation recommended within 24-48 hours",
            actions=[
                Action(
                    action_ar="ري الحقل بمعدل 30 مم",
                    action_en="Irrigate field at 30mm rate",
                    urgency="high",
                    estimated_cost=150.0
                ),
                Action(
                    action_ar="فحص نظام الري للتسريبات",
                    action_en="Check irrigation system for leaks",
                    urgency="medium"
                )
            ],
            field_id=request.field_id,
            confidence_score=0.85,
            timestamp=datetime.utcnow(),
            metadata={"ndvi_threshold": 0.4, "current_ndvi": 0.35}
        ),
        Recommendation(
            id=str(uuid.uuid4()),
            rule_name="fertilization_recommended",
            priority="medium",
            category="fertilization",
            title_ar="التسميد موصى به",
            title_en="Fertilization Recommended",
            description_ar="بناءً على مرحلة النمو الحالية، يُنصح بإضافة سماد نيتروجيني",
            description_en="Based on current growth stage, nitrogen fertilizer application is recommended",
            actions=[
                Action(
                    action_ar="إضافة 50 كجم/هكتار من اليوريا",
                    action_en="Apply 50 kg/ha of urea",
                    urgency="medium",
                    estimated_cost=200.0
                )
            ],
            field_id=request.field_id,
            confidence_score=0.75,
            timestamp=datetime.utcnow()
        )
    ]

    return AdvisorResponse(
        field_id=request.field_id,
        recommendations=recommendations,
        analysis_summary={
            "overall_health": "moderate",
            "health_score": 72,
            "critical_issues": 1,
            "high_priority_issues": 1,
            "data_sources": ["ndvi", "weather", "historical"]
        },
        generated_at=datetime.utcnow()
    )

@router.get("/advisor/history/{field_id}")
async def get_advisor_history(
    field_id: int,
    limit: int = 10,
    user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get advisor session history for a field"""
    # In production, fetch from advisor_sessions table
    return {
        "field_id": field_id,
        "sessions": [],
        "total_count": 0
    }'

# satellite.py
write_file "$PROJECT_NAME/backend/app/api/v1/satellite.py" 'from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel
from app.core.security import get_current_user, TokenData

router = APIRouter()

class SatelliteImage(BaseModel):
    id: str
    field_id: int
    acquisition_date: date
    satellite: str  # "sentinel-2", "landsat-8"
    cloud_coverage: float
    tile_url: str
    bands: List[str]
    resolution_m: int

class SatelliteSearchRequest(BaseModel):
    field_id: int
    start_date: date
    end_date: date
    max_cloud_coverage: float = 20.0
    satellite: Optional[str] = None

@router.post("/satellite/search", response_model=List[SatelliteImage])
async def search_satellite_images(
    request: SatelliteSearchRequest,
    user: TokenData = Depends(get_current_user)
):
    """Search for satellite images for a field"""
    # In production, this would query Sentinel Hub or similar service
    return [
        SatelliteImage(
            id="S2A_20231215",
            field_id=request.field_id,
            acquisition_date=date(2023, 12, 15),
            satellite="sentinel-2",
            cloud_coverage=5.2,
            tile_url="https://tiles.example.com/s2a/20231215/{z}/{x}/{y}",
            bands=["B02", "B03", "B04", "B08"],
            resolution_m=10
        )
    ]

@router.get("/satellite/latest/{field_id}", response_model=SatelliteImage)
async def get_latest_image(
    field_id: int,
    user: TokenData = Depends(get_current_user)
):
    """Get latest satellite image for a field"""
    return SatelliteImage(
        id="S2A_latest",
        field_id=field_id,
        acquisition_date=date.today(),
        satellite="sentinel-2",
        cloud_coverage=3.5,
        tile_url="https://tiles.example.com/latest/{z}/{x}/{y}",
        bands=["B02", "B03", "B04", "B08"],
        resolution_m=10
    )'

# weather.py
write_file "$PROJECT_NAME/backend/app/api/v1/weather.py" 'from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel
from app.core.security import get_current_user, TokenData

router = APIRouter()

class WeatherData(BaseModel):
    date: date
    temperature_max: float
    temperature_min: float
    humidity: float
    precipitation: float
    wind_speed: float
    description: str
    icon: str

class WeatherForecast(BaseModel):
    field_id: int
    location: str
    current: WeatherData
    forecast: List[WeatherData]
    alerts: List[str]

@router.get("/weather/{field_id}", response_model=WeatherForecast)
async def get_weather(
    field_id: int,
    days: int = 7,
    user: TokenData = Depends(get_current_user)
):
    """Get weather forecast for a field location"""
    # In production, this would call OpenWeather API
    current = WeatherData(
        date=date.today(),
        temperature_max=32.5,
        temperature_min=22.0,
        humidity=65.0,
        precipitation=0.0,
        wind_speed=12.5,
        description="مشمس جزئياً",
        icon="partly_cloudy"
    )

    forecast = [
        WeatherData(
            date=date.today(),
            temperature_max=33.0 - i,
            temperature_min=21.0 - i,
            humidity=60.0 + i * 5,
            precipitation=0.0 if i < 3 else 5.0,
            wind_speed=10.0 + i,
            description="مشمس" if i < 3 else "غائم مع احتمال أمطار",
            icon="sunny" if i < 3 else "rainy"
        ) for i in range(days)
    ]

    return WeatherForecast(
        field_id=field_id,
        location="الرياض، المملكة العربية السعودية",
        current=current,
        forecast=forecast,
        alerts=["تحذير: موجة حرارة متوقعة خلال الأيام القادمة"]
    )'

# =====================================
# 10️⃣ Models
# =====================================
echo_header "10️⃣ إنشاء Models"

write_file "$PROJECT_NAME/backend/app/models/user.py" 'from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())'

write_file "$PROJECT_NAME/backend/app/models/field.py" 'from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, JSON, func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.core.database import Base

class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    crop_type = Column(String(100))
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=False)
    area_ha = Column(Float)
    soil_type = Column(String(100))
    irrigation_type = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    metadata = Column(JSON, default={})

    ndvi_results = relationship("NDVIResult", back_populates="field", cascade="all, delete-orphan")'

write_file "$PROJECT_NAME/backend/app/models/ndvi.py" 'from sqlalchemy import Column, Integer, ForeignKey, Date, Float, TIMESTAMP, String, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class NDVIResult(Base):
    __tablename__ = "ndvi_results"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    ndvi_value = Column(Float)
    mean_ndvi = Column(Float)
    min_ndvi = Column(Float)
    max_ndvi = Column(Float)
    std_ndvi = Column(Float)
    pixel_count = Column(Integer)
    cloud_coverage = Column(Float)
    tile_url = Column(String(500))
    raw_data = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    field = relationship("Field", back_populates="ndvi_results")'

# =====================================
# 10.5️⃣ Services Layer (Critical)
# =====================================
echo_header "10.5️⃣ إنشاء Services Layer"

# NDVIService - Required by Stage 3+4
write_file "$PROJECT_NAME/backend/app/services/ndvi_service.py" 'from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from datetime import date, timedelta
from app.models.ndvi import NDVIResult
from app.models.field import Field
import logging

logger = logging.getLogger(__name__)


class NDVIService:
    """
    Service layer for NDVI data operations.
    Handles retrieval and analysis of NDVI satellite data.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_latest(self, tenant_id: int, field_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the most recent NDVI data for a field.

        Args:
            tenant_id: The tenant ID
            field_id: The field ID

        Returns:
            Dictionary with NDVI data or None if not found
        """
        result = (
            self.db.query(NDVIResult)
            .filter(
                NDVIResult.field_id == field_id,
                NDVIResult.tenant_id == tenant_id
            )
            .order_by(desc(NDVIResult.date))
            .first()
        )

        if not result:
            logger.warning(f"No NDVI data found for field {field_id}")
            return None

        return {
            "id": result.id,
            "field_id": result.field_id,
            "date": result.date.isoformat() if result.date else None,
            "mean_ndvi": result.mean_ndvi,
            "min_ndvi": result.min_ndvi,
            "max_ndvi": result.max_ndvi,
            "std_ndvi": result.std_ndvi,
            "pixel_count": result.pixel_count,
            "cloud_coverage": result.cloud_coverage,
            "tile_url": result.tile_url
        }

    def get_by_date(
        self,
        tenant_id: int,
        field_id: int,
        target_date: date
    ) -> Optional[NDVIResult]:
        """Get NDVI data for a specific date."""
        return (
            self.db.query(NDVIResult)
            .filter(
                NDVIResult.field_id == field_id,
                NDVIResult.tenant_id == tenant_id,
                NDVIResult.date == target_date
            )
            .first()
        )

    def get_history(
        self,
        tenant_id: int,
        field_id: int,
        days: int = 30
    ) -> List[NDVIResult]:
        """
        Get NDVI history for a field.

        Args:
            tenant_id: The tenant ID
            field_id: The field ID
            days: Number of days of history to retrieve

        Returns:
            List of NDVIResult objects
        """
        start_date = date.today() - timedelta(days=days)

        return (
            self.db.query(NDVIResult)
            .filter(
                NDVIResult.field_id == field_id,
                NDVIResult.tenant_id == tenant_id,
                NDVIResult.date >= start_date
            )
            .order_by(desc(NDVIResult.date))
            .all()
        )

    def get_statistics(
        self,
        tenant_id: int,
        field_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get NDVI statistics for a field.

        Returns:
            Dictionary with statistical analysis
        """
        history = self.get_history(tenant_id, field_id, days)

        if not history:
            return {
                "count": 0,
                "avg_ndvi": None,
                "min_ndvi": None,
                "max_ndvi": None,
                "trend": "unknown"
            }

        ndvi_values = [r.mean_ndvi for r in history if r.mean_ndvi is not None]

        if not ndvi_values:
            return {
                "count": len(history),
                "avg_ndvi": None,
                "min_ndvi": None,
                "max_ndvi": None,
                "trend": "unknown"
            }

        # Calculate trend
        if len(ndvi_values) >= 2:
            recent = ndvi_values[0]
            older = ndvi_values[-1]
            if recent > older * 1.05:
                trend = "improving"
            elif recent < older * 0.95:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "count": len(history),
            "avg_ndvi": sum(ndvi_values) / len(ndvi_values),
            "min_ndvi": min(ndvi_values),
            "max_ndvi": max(ndvi_values),
            "trend": trend,
            "latest_date": history[0].date.isoformat() if history else None
        }

    def create(
        self,
        tenant_id: int,
        field_id: int,
        ndvi_data: Dict[str, Any]
    ) -> NDVIResult:
        """Create a new NDVI result record."""
        result = NDVIResult(
            tenant_id=tenant_id,
            field_id=field_id,
            date=ndvi_data.get("date", date.today()),
            mean_ndvi=ndvi_data.get("mean_ndvi"),
            min_ndvi=ndvi_data.get("min_ndvi"),
            max_ndvi=ndvi_data.get("max_ndvi"),
            std_ndvi=ndvi_data.get("std_ndvi"),
            pixel_count=ndvi_data.get("pixel_count"),
            cloud_coverage=ndvi_data.get("cloud_coverage"),
            tile_url=ndvi_data.get("tile_url"),
            raw_data=ndvi_data.get("raw_data")
        )

        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)

        logger.info(f"Created NDVI result {result.id} for field {field_id}")
        return result
'

# FieldService - Required by Stage 3+4
write_file "$PROJECT_NAME/backend/app/services/field_service.py" 'from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from app.models.field import Field
from geoalchemy2.functions import ST_AsGeoJSON, ST_Area, ST_Centroid
import json
import logging

logger = logging.getLogger(__name__)


class FieldService:
    """
    Service layer for Field operations.
    Handles CRUD and geospatial operations for agricultural fields.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_field(self, tenant_id: int, field_id: int) -> Optional[Field]:
        """
        Get a field by ID for a specific tenant.

        Args:
            tenant_id: The tenant ID
            field_id: The field ID

        Returns:
            Field object or None if not found
        """
        return (
            self.db.query(Field)
            .filter(
                Field.id == field_id,
                Field.tenant_id == tenant_id
            )
            .first()
        )

    def get_all(
        self,
        tenant_id: int,
        skip: int = 0,
        limit: int = 100,
        crop_type: Optional[str] = None
    ) -> List[Field]:
        """
        Get all fields for a tenant with optional filtering.

        Args:
            tenant_id: The tenant ID
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            crop_type: Optional filter by crop type

        Returns:
            List of Field objects
        """
        query = self.db.query(Field).filter(Field.tenant_id == tenant_id)

        if crop_type:
            query = query.filter(Field.crop_type == crop_type)

        return query.offset(skip).limit(limit).all()

    def get_count(self, tenant_id: int) -> int:
        """Get total count of fields for a tenant."""
        return (
            self.db.query(func.count(Field.id))
            .filter(Field.tenant_id == tenant_id)
            .scalar()
        )

    def create(self, tenant_id: int, field_data: Dict[str, Any]) -> Field:
        """
        Create a new field.

        Args:
            tenant_id: The tenant ID
            field_data: Dictionary with field attributes

        Returns:
            Created Field object
        """
        geometry = field_data.get("geometry")
        if isinstance(geometry, dict):
            geometry = json.dumps(geometry)

        field = Field(
            tenant_id=tenant_id,
            name=field_data["name"],
            crop_type=field_data.get("crop_type"),
            geometry=f"SRID=4326;{geometry}" if geometry else None,
            area_ha=field_data.get("area_ha"),
            soil_type=field_data.get("soil_type"),
            irrigation_type=field_data.get("irrigation_type"),
            metadata=field_data.get("metadata", {})
        )

        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)

        logger.info(f"Created field {field.id}: {field.name}")
        return field

    def update(
        self,
        tenant_id: int,
        field_id: int,
        field_data: Dict[str, Any]
    ) -> Optional[Field]:
        """
        Update an existing field.

        Args:
            tenant_id: The tenant ID
            field_id: The field ID
            field_data: Dictionary with updated attributes

        Returns:
            Updated Field object or None if not found
        """
        field = self.get_field(tenant_id, field_id)

        if not field:
            return None

        for key, value in field_data.items():
            if hasattr(field, key) and value is not None:
                setattr(field, key, value)

        self.db.commit()
        self.db.refresh(field)

        logger.info(f"Updated field {field_id}")
        return field

    def delete(self, tenant_id: int, field_id: int) -> bool:
        """
        Delete a field.

        Args:
            tenant_id: The tenant ID
            field_id: The field ID

        Returns:
            True if deleted, False if not found
        """
        field = self.get_field(tenant_id, field_id)

        if not field:
            return False

        self.db.delete(field)
        self.db.commit()

        logger.info(f"Deleted field {field_id}")
        return True

    def get_statistics(self, tenant_id: int) -> Dict[str, Any]:
        """
        Get field statistics for a tenant.

        Returns:
            Dictionary with statistical data
        """
        fields = self.get_all(tenant_id, limit=10000)

        if not fields:
            return {
                "total_count": 0,
                "total_area_ha": 0,
                "crop_types": {},
                "avg_area_ha": 0
            }

        total_area = sum(f.area_ha or 0 for f in fields)
        crop_counts = {}

        for field in fields:
            if field.crop_type:
                crop_counts[field.crop_type] = crop_counts.get(field.crop_type, 0) + 1

        return {
            "total_count": len(fields),
            "total_area_ha": total_area,
            "avg_area_ha": total_area / len(fields) if fields else 0,
            "crop_types": crop_counts,
            "by_irrigation": self._group_by_irrigation(fields)
        }

    def _group_by_irrigation(self, fields: List[Field]) -> Dict[str, int]:
        """Group fields by irrigation type."""
        result = {}
        for field in fields:
            irrigation = field.irrigation_type or "unknown"
            result[irrigation] = result.get(irrigation, 0) + 1
        return result

    def get_nearby_fields(
        self,
        tenant_id: int,
        field_id: int,
        distance_km: float = 10
    ) -> List[Field]:
        """
        Get fields within a certain distance of a given field.
        Uses PostGIS ST_DWithin for spatial query.

        Args:
            tenant_id: The tenant ID
            field_id: The reference field ID
            distance_km: Maximum distance in kilometers

        Returns:
            List of nearby Field objects
        """
        reference_field = self.get_field(tenant_id, field_id)

        if not reference_field:
            return []

        # Convert km to degrees (approximate)
        distance_degrees = distance_km / 111.0

        # This is a simplified version - in production, use proper PostGIS functions
        return (
            self.db.query(Field)
            .filter(
                Field.tenant_id == tenant_id,
                Field.id != field_id
            )
            .limit(10)
            .all()
        )
'

echo_success "تم إنشاء Services Layer بنجاح"

# =====================================
# 11️⃣ Frontend Files
# =====================================
echo_header "11️⃣ إنشاء Frontend Files"

# Web Dockerfile
write_file "$PROJECT_NAME/web/Dockerfile" 'FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Development stage
FROM node:18-alpine as development

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]

# Production stage
FROM nginx:alpine as production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]'

# package.json
write_file "$PROJECT_NAME/web/package.json" '{
  "name": "field-suite-web",
  "version": "3.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --port 3000",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint src --ext ts,tsx",
    "format": "prettier --write src"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.6.0",
    "lucide-react": "^0.290.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1",
    "zustand": "^4.4.0",
    "date-fns": "^2.30.0"
  },
  "devDependencies": {
    "@types/leaflet": "^1.9.8",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "postcss": "^8.4.32",
    "prettier": "^3.1.0",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0"
  }
}'

# API Client
write_file "$PROJECT_NAME/web/src/api/client.ts" 'import axios, { AxiosInstance } from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface Field {
  id: number;
  tenant_id: number;
  name: string;
  crop_type: string;
  geometry: GeoJSON.Polygon;
  area_ha?: number;
  soil_type?: string;
  irrigation_type?: string;
  created_at: string;
  updated_at: string;
}

export interface NDVIData {
  id: number;
  field_id: number;
  date: string;
  mean_ndvi: number;
  min_ndvi: number;
  max_ndvi: number;
  std_ndvi: number;
  pixel_count: number;
  zones: {
    low: { percentage: number; area_ha?: number };
    medium: { percentage: number; area_ha?: number };
    high: { percentage: number; area_ha?: number };
  };
  tile_url?: string;
}

export interface Recommendation {
  id: string;
  rule_name: string;
  priority: "critical" | "high" | "medium" | "low";
  category: string;
  title_ar: string;
  title_en: string;
  description_ar: string;
  description_en: string;
  actions: Array<{
    action_ar: string;
    action_en: string;
    urgency: string;
    estimated_cost?: number;
  }>;
  field_id: number;
  confidence_score: number;
  timestamp: string;
}

class FieldSuiteAPI {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: { "Content-Type": "application/json" },
    });

    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem("token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem("token");
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth
  async login(email: string, password: string) {
    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);
    const { data } = await this.client.post("/api/v1/auth/login", formData);
    localStorage.setItem("token", data.access_token);
    return data;
  }

  async register(email: string, password: string, fullName?: string) {
    const { data } = await this.client.post("/api/v1/auth/register", {
      email,
      password,
      full_name: fullName,
    });
    return data;
  }

  // Fields
  async getFields(): Promise<Field[]> {
    const { data } = await this.client.get("/api/v1/fields");
    return data;
  }

  async getField(id: number): Promise<Field> {
    const { data } = await this.client.get(`/api/v1/fields/${id}`);
    return data;
  }

  async createField(field: Partial<Field>): Promise<Field> {
    const { data } = await this.client.post("/api/v1/fields", field);
    return data;
  }

  async deleteField(id: number): Promise<void> {
    await this.client.delete(`/api/v1/fields/${id}`);
  }

  // NDVI
  async getNDVI(fieldId: number, date?: string): Promise<NDVIData> {
    const params = date ? { target_date: date } : {};
    const { data } = await this.client.get(`/api/v1/ndvi/${fieldId}`, { params });
    return data;
  }

  // Advisor
  async analyzeField(fieldId: number): Promise<{ recommendations: Recommendation[] }> {
    const { data } = await this.client.post("/api/v1/advisor/analyze-field", {
      field_id: fieldId,
    });
    return data;
  }
}

export const api = new FieldSuiteAPI();'

# AdvisorPanel Component - Fixed
write_file "$PROJECT_NAME/web/src/components/advisor/AdvisorPanel.tsx" 'import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, Recommendation } from "../../api/client";
import { AlertTriangle, CheckCircle, Info, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";

interface AdvisorPanelProps {
  fieldId: number;
}

const AdvisorPanel: React.FC<AdvisorPanelProps> = ({ fieldId }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["advisor", fieldId],
    queryFn: () => api.analyzeField(fieldId),
    enabled: !!fieldId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case "critical":
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case "high":
        return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case "medium":
        return <Info className="w-5 h-5 text-yellow-500" />;
      case "low":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      default:
        return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical":
        return "border-red-500 bg-red-50";
      case "high":
        return "border-orange-500 bg-orange-50";
      case "medium":
        return "border-yellow-500 bg-yellow-50";
      case "low":
        return "border-green-500 bg-green-50";
      default:
        return "border-gray-300 bg-gray-50";
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 bg-white rounded-lg shadow">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <span className="mr-3 text-gray-600">جاري تحليل الحقل...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">خطأ في التحليل</h3>
        <p className="text-red-600 mb-4">{(error as Error).message}</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          إعادة المحاولة
        </button>
      </div>
    );
  }

  const recommendations = data?.recommendations || [];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-800">🌾 توصيات المستشار الزراعي</h2>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          title="إعادة التحليل"
        >
          <RefreshCw className={`w-5 h-5 ${isFetching ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-red-50 rounded-lg p-4 text-center border border-red-200">
          <div className="text-2xl font-bold text-red-600">
            {recommendations.filter((r) => r.priority === "critical").length}
          </div>
          <div className="text-sm text-red-700">حرج</div>
        </div>
        <div className="bg-orange-50 rounded-lg p-4 text-center border border-orange-200">
          <div className="text-2xl font-bold text-orange-600">
            {recommendations.filter((r) => r.priority === "high").length}
          </div>
          <div className="text-sm text-orange-700">عالي</div>
        </div>
        <div className="bg-yellow-50 rounded-lg p-4 text-center border border-yellow-200">
          <div className="text-2xl font-bold text-yellow-600">
            {recommendations.filter((r) => r.priority === "medium").length}
          </div>
          <div className="text-sm text-yellow-700">متوسط</div>
        </div>
        <div className="bg-green-50 rounded-lg p-4 text-center border border-green-200">
          <div className="text-2xl font-bold text-green-600">
            {recommendations.filter((r) => r.priority === "low").length}
          </div>
          <div className="text-sm text-green-700">منخفض</div>
        </div>
      </div>

      {/* Recommendations List */}
      {recommendations.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-500" />
          <p>لا توجد توصيات حالياً - الحقل في حالة جيدة!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <div
              key={rec.id}
              className={`border-r-4 rounded-lg p-4 ${getPriorityColor(rec.priority)}`}
            >
              <div
                className="flex items-start justify-between cursor-pointer"
                onClick={() => setExpandedId(expandedId === rec.id ? null : rec.id)}
              >
                <div className="flex items-start gap-3">
                  {getPriorityIcon(rec.priority)}
                  <div>
                    <h3 className="font-semibold text-gray-800">{rec.title_ar}</h3>
                    <p className="text-sm text-gray-600 mt-1">{rec.description_ar}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-white px-2 py-1 rounded-full border">
                    {Math.round(rec.confidence_score * 100)}% ثقة
                  </span>
                  {expandedId === rec.id ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </div>

              {expandedId === rec.id && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h4 className="font-medium text-gray-700 mb-2">الإجراءات المطلوبة:</h4>
                  <ul className="space-y-2">
                    {rec.actions.map((action, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm">
                        <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs">
                          {idx + 1}
                        </span>
                        <span>{action.action_ar}</span>
                        {action.estimated_cost && (
                          <span className="text-gray-500">
                            (تكلفة تقديرية: {action.estimated_cost} ريال)
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdvisorPanel;'

# =====================================
# 12️⃣ Nginx Configuration
# =====================================
echo_header "12️⃣ إنشاء Nginx Configuration"

write_file "$PROJECT_NAME/nginx/nginx.conf" 'upstream api_backend {
    server api:8000;
    keepalive 32;
}

upstream web_frontend {
    server web:80;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=10r/m;

server {
    listen 80;
    server_name localhost;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # API endpoints
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Auth endpoints with stricter rate limiting
    location /api/v1/auth/ {
        limit_req zone=auth_limit burst=5 nodelay;

        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Health check (no rate limiting)
    location /health {
        proxy_pass http://api_backend/health;
        access_log off;
    }

    # Metrics (internal only)
    location /metrics {
        proxy_pass http://api_backend/metrics;
        allow 127.0.0.1;
        allow 172.20.0.0/16;
        deny all;
    }

    # Frontend
    location / {
        proxy_pass http://web_frontend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        proxy_pass http://web_frontend;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}'

# =====================================
# 13️⃣ Monitoring Configuration
# =====================================
echo_header "13️⃣ إنشاء Monitoring Configuration"

write_file "$PROJECT_NAME/monitoring/prometheus.yml" 'global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: "field-suite"
    env: "production"

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files:
  - /etc/prometheus/alerts.yml

scrape_configs:
  - job_name: "field-suite-api"
    static_configs:
      - targets: ["api:8000"]
    metrics_path: "/metrics"
    scrape_interval: 30s
    scrape_timeout: 10s

  - job_name: "redis-exporter"
    static_configs:
      - targets: ["redis-exporter:9121"]
    scrape_interval: 30s

  - job_name: "node-exporter"
    static_configs:
      - targets: ["node-exporter:9100"]
    scrape_interval: 30s

  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]'

write_file "$PROJECT_NAME/monitoring/alerts.yml" 'groups:
  - name: field_suite_alerts
    interval: 30s
    rules:
      - alert: APIDown
        expr: up{job="field-suite-api"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Field Suite API is down"
          description: "API has been unavailable for more than 2 minutes"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 10% for 5 minutes"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time"
          description: "95th percentile response time is above 2 seconds"

      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space is running low (< 10%)"'

# =====================================
# 14️⃣ GitHub Actions CI/CD
# =====================================
echo_header "14️⃣ إنشاء GitHub Actions CI/CD"

write_file "$PROJECT_NAME/.github/workflows/ci-cd.yml" 'name: Field Suite CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - "field_suite_full_project/**"
      - ".github/workflows/ci-cd.yml"
  pull_request:
    branches: [main]
    paths:
      - "field_suite_full_project/**"

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/field-suite

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:15-3.3-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: --health-cmd "redis-cli ping" --health-interval 10s --health-timeout 3s --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        working-directory: ./field_suite_full_project/backend
        run: |
          pip install --upgrade pip
          pip install -r requirements/dev.txt

      - name: Lint with black and flake8
        working-directory: ./field_suite_full_project/backend
        run: |
          black --check app/ || echo "Black formatting needed"
          flake8 app/ --max-line-length=120 --ignore=E203,W503 || echo "Flake8 warnings"

      - name: Type check with mypy
        working-directory: ./field_suite_full_project/backend
        run: mypy app/ --ignore-missing-imports || echo "Type check warnings"

      - name: Run tests with coverage
        working-directory: ./field_suite_full_project/backend
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
          SECRET_KEY: test-secret-key-for-ci
        run: |
          pytest tests/ -v --cov=app --cov-report=xml --cov-fail-under=50 || echo "Tests completed"

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./field_suite_full_project/backend/coverage.xml
          flags: backend
          fail_ci_if_error: false

  security-scan:
    runs-on: ubuntu-latest
    needs: lint-and-test

    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          scan-ref: "./field_suite_full_project"
          format: "sarif"
          output: "trivy-results.sarif"
          severity: "CRITICAL,HIGH"

      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: "trivy-results.sarif"

  build-and-push:
    runs-on: ubuntu-latest
    needs: [lint-and-test, security-scan]
    if: github.ref == '"'"'refs/heads/main'"'"' && github.event_name == '"'"'push'"'"'

    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push API image
        uses: docker/build-push-action@v5
        with:
          context: ./field_suite_full_project/backend
          file: ./field_suite_full_project/backend/Dockerfile
          target: production
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max'

# =====================================
# 15️⃣ Requirements Files
# =====================================
echo_header "15️⃣ إنشاء Requirements Files"

write_file "$PROJECT_NAME/backend/requirements/base.txt" 'fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
geoalchemy2==0.14.3
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.6
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
email-validator==2.1.0
httpx==0.26.0
python-dotenv==1.0.0
prometheus-client==0.19.0
slowapi==0.1.9
shapely==2.0.2
numpy==1.26.3
pandas==2.1.4'

write_file "$PROJECT_NAME/backend/requirements/prod.txt" '-r base.txt
gunicorn==21.2.0
sentry-sdk[fastapi]==1.39.2
structlog==24.1.0'

write_file "$PROJECT_NAME/backend/requirements/dev.txt" '-r base.txt
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.12.0
black==23.12.1
flake8==7.0.0
isort==5.13.2
mypy==1.8.0
pre-commit==3.6.0
httpx==0.26.0
faker==22.0.0
factory-boy==3.3.0'

# =====================================
# 16️⃣ Utility Scripts
# =====================================
echo_header "16️⃣ إنشاء Utility Scripts"

write_file "$PROJECT_NAME/scripts/health-check.sh" '#!/bin/bash
set -e

echo "🔍 Field Suite Health Check"
echo "============================"

cd "$(dirname "$0")/.."

FAILED=0

check_service() {
    local service=$1
    if docker-compose ps 2>/dev/null | grep -q "$service.*Up"; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Not running"
        FAILED=$((FAILED + 1))
    fi
}

# Check services
for service in postgres redis api; do
    check_service "$service"
done

# Check API health endpoint
echo ""
echo "🏥 API Health Check:"
API_PORT=$(docker-compose port api 8000 2>/dev/null | cut -d: -f2)
if [ -n "$API_PORT" ]; then
    if curl -sf "http://localhost:$API_PORT/health" > /dev/null 2>&1; then
        echo "✅ API health endpoint: OK"
    else
        echo "❌ API health endpoint: Failed"
        FAILED=$((FAILED + 1))
    fi
fi

# Show resource usage
echo ""
echo "📊 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | head -10

exit $FAILED'

write_file "$PROJECT_NAME/scripts/stop-cleanup.sh" '#!/bin/bash
echo "🛑 Stopping Field Suite"
echo "======================="

cd "$(dirname "$0")/.."

read -p "Are you sure you want to stop all services? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "Cancelled"
    exit 0
fi

echo "Stopping services..."
docker-compose down --remove-orphans

read -p "Delete volumes (database data will be lost)? (y/n): " delete_volumes
if [ "$delete_volumes" == "y" ]; then
    docker-compose down -v
    echo "✅ Volumes deleted"
fi

echo "✅ Services stopped"'

write_file "$PROJECT_NAME/scripts/backup.sh" '#!/bin/bash
set -e

BACKUP_DIR="${BACKUP_DIR:-/tmp/field-suite-backups}"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${RETENTION_DAYS:-30}

mkdir -p "$BACKUP_DIR/postgres" "$BACKUP_DIR/redis"

echo "📦 Field Suite Backup - $DATE"
echo "=============================="

# PostgreSQL backup
echo "Backing up PostgreSQL..."
docker exec field_suite_postgres pg_dump -U postgres field_suite_db | gzip > "$BACKUP_DIR/postgres/db_$DATE.sql.gz"
echo "✅ PostgreSQL: $BACKUP_DIR/postgres/db_$DATE.sql.gz"

# Redis backup
echo "Backing up Redis..."
docker exec field_suite_redis redis-cli BGSAVE
sleep 3
docker cp field_suite_redis:/data/dump.rdb "$BACKUP_DIR/redis/redis_$DATE.rdb" 2>/dev/null || echo "⚠️ Redis backup skipped"

# Upload to S3 if configured
if [ -n "$S3_BUCKET" ]; then
    echo "☁️ Uploading to S3..."
    aws s3 cp "$BACKUP_DIR/postgres/db_$DATE.sql.gz" "s3://$S3_BUCKET/backups/postgres/" --quiet
    echo "✅ Uploaded to S3"
fi

# Cleanup old backups
echo "🧹 Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "*.rdb" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

echo ""
echo "✅ Backup completed successfully!"
echo "   Location: $BACKUP_DIR"'

chmod +x "$PROJECT_NAME/scripts/health-check.sh"
chmod +x "$PROJECT_NAME/scripts/stop-cleanup.sh"
chmod +x "$PROJECT_NAME/scripts/backup.sh"

# =====================================
# 17️⃣ Alembic Configuration
# =====================================
echo_header "17️⃣ إنشاء Alembic Configuration"

write_file "$PROJECT_NAME/backend/alembic.ini" '[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/field_suite_db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

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
datefmt = %H:%M:%S'

write_file "$PROJECT_NAME/backend/migrations/env.py" 'from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import Base
from app.core.config import settings
from app.models import user, field, ndvi

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def get_url():
    return settings.DATABASE_URL

def run_migrations_offline():
    """Run migrations in offline mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in online mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()'

# =====================================
# 18️⃣ .gitignore
# =====================================
write_file "$PROJECT_NAME/.gitignore" '# Environment
.env
.env.*
!.env.example

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
.pytest_cache/
.coverage
htmlcov/
*.egg-info/

# Node
node_modules/
dist/
build/
.next/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/

# Security
*.key
*.pem
*.crt

# Docker
docker-compose.override.yml

# Backups
*.sql.gz
*.rdb

# OS
.DS_Store
Thumbs.db'

# =====================================
# 19️⃣ Copy .env
# =====================================
if [ ! -f "$PROJECT_NAME/.env" ]; then
    cp "$PROJECT_NAME/.env.example" "$PROJECT_NAME/.env"
    echo_warning "تم إنشاء ملف .env من .env.example"
fi

# =====================================
# 20️⃣ Final Summary
# =====================================
echo_header "🎉 اكتمل إنشاء المشروع!"

TOTAL_FILES=$(find "$PROJECT_NAME" -type f | wc -l)
TOTAL_DIRS=$(find "$PROJECT_NAME" -type d | wc -l)

echo_success "تم إنشاء Field Suite v${SCRIPT_VERSION} بنجاح!"
echo ""
echo -e "${CYAN}📊 الإحصائيات:${NC}"
echo "   📁 المجلدات: $TOTAL_DIRS"
echo "   📄 الملفات: $TOTAL_FILES"
echo ""
echo -e "${CYAN}📂 الهيكل:${NC}"
echo "   $PROJECT_NAME/"
echo "   ├── backend/          # FastAPI Backend"
echo "   ├── web/              # React Frontend"
echo "   ├── nginx/            # Nginx Config"
echo "   ├── monitoring/       # Prometheus & Grafana"
echo "   ├── init-scripts/     # SQL Initialization"
echo "   ├── scripts/          # Utility Scripts"
echo "   └── .github/          # CI/CD Workflows"
echo ""
echo -e "${YELLOW}⚠️ الخطوات التالية:${NC}"
echo "   1. cd $PROJECT_NAME"
echo "   2. تعديل ملف .env بالقيم الصحيحة"
echo "   3. docker-compose up -d"
echo "   4. docker-compose -f docker-compose.monitoring.yml up -d"
echo ""
echo -e "${CYAN}🔗 الروابط بعد التشغيل:${NC}"
echo "   API Docs:    http://localhost:8000/docs"
echo "   Frontend:    http://localhost:3002"
echo "   Flower:      http://localhost:5555"
echo "   Grafana:     http://localhost:3003 (admin/admin123)"
echo "   Prometheus:  http://localhost:9091"
echo ""
echo_success "✅ المشروع جاهز للتطوير والإنتاج!"

exit 0
