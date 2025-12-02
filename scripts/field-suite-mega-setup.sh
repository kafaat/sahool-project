#!/bin/bash
set -e

# =====================================
# Field Suite - Mega Setup Script
# من الصفر إلى الإنتاج في أمر واحد
# =====================================

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# المتغيرات
PROJECT_NAME="field_suite_full_project"
BRANCH_NAME="feature/field-suite-generator"
REPO_URL="https://github.com/kafaat/sahool-project.git"

# دالة لكتابة الملفات
write_file() {
    local file_path=$1
    local content=$2
    mkdir -p "$(dirname "$file_path")"
    echo "$content" > "$file_path"
    echo -e "${GREEN}✅ تم إنشاء: ${file_path}${NC}"
}

echo_header() {
    echo -e "${BLUE}"
    echo "====================================="
    echo "$1"
    echo "====================================="
    echo -e "${NC}"
}

# =====================================
# 1️⃣ التحقق من المتطلبات
# =====================================
echo_header "📋 التحقق من المتطلبات المسبقة"

check_requirement() {
    local cmd=$1
    local name=$2
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}❌ $name غير مثبت${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ $name: $(command -v $cmd)${NC}"
    fi
}

check_requirement git "Git"
check_requirement docker "Docker"
check_requirement docker-compose "Docker Compose"

# التحقق من Docker Compose v2+
COMPOSE_VERSION=$(docker-compose version --short 2>&1 | cut -d' ' -f3)
if [[ $(echo "$COMPOSE_VERSION" | cut -d'.' -f1) -lt 2 ]]; then
    echo -e "${RED}❌ يتطلب Docker Compose v2 أو أحدث${NC}"
    exit 1
fi

# =====================================
# 2️⃣ إعداد المستودع
# =====================================
echo_header "📥 إعداد المستودع"

if [ ! -d "sahool-project" ]; then
    echo -e "${YELLOW}📥 استنساخ المستودع...${NC}"
    git clone "$REPO_URL"
else
    echo -e "${YELLOW}⚠️  المجلد موجود، جاري التحديث...${NC}"
    cd sahool-project
    git pull origin main 2>/dev/null || echo -e "${YELLOW}⚠️  لم يتم التحديث (قد يكون الفرع غير موجود)${NC}"
    cd ..
fi

cd sahool-project

# إنشاء/الانتقال للفرع
echo -e "${YELLOW}📂 إعداد الفرع $BRANCH_NAME...${NC}"
git fetch origin 2>/dev/null || true
if git rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1; then
    git checkout "$BRANCH_NAME"
else
    git checkout -b "$BRANCH_NAME" 2>/dev/null || echo -e "${YELLOW}⚠️  إنشاء الفرع تخطي، الاستمرار...${NC}"
fi

# =====================================
# 3️⃣ إنشاء هيكل المجلدات
# =====================================
echo_header "📂 إنشاء هيكل المجلدات"

DIRS=(
    "$PROJECT_NAME/backend/app/{api/v1,middleware,core,services,repositories,schemas,models,tasks,utils}"
    "$PROJECT_NAME/backend/tests/{unit,integration}"
    "$PROJECT_NAME/backend/requirements"
    "$PROJECT_NAME/backend/migrations/versions"
    "$PROJECT_NAME/web/src/{api,components/{advisor,map,fields,common},hooks,store,pages,utils,styles}"
    "$PROJECT_NAME/nginx"
    "$PROJECT_NAME/init-scripts"
    "$PROJECT_NAME/monitoring/grafana-dashboards"
    "$PROJECT_NAME/field_advisor_service/{rules,schemas,tests}"
    "$PROJECT_NAME/docs"
    "$PROJECT_NAME/scripts"
)

for dir in "${DIRS[@]}"; do
    mkdir -p "$PROJECT_NAME/$dir"
done

echo -e "${GREEN}✅ تم إنشاء هيكل المجلدات${NC}"

# =====================================
# 4️⃣ إنشاء docker-compose.yml
# =====================================
echo_header "🐳 إنشاء docker-compose.yml"

write_file "$PROJECT_NAME/docker-compose.yml" 'version: '\''3.8'\''
services:
  postgres:
    image: postgis/postgis:15-3.3-alpine
    container_name: field_suite_postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-field_suite_db}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change_this_in_env}
    ports:
      - "127.0.0.1:5432:5432"
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

  redis:
    image: redis:7-alpine
    container_name: field_suite_redis
    ports:
      - "127.0.0.1:6379:6379"
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

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: field_suite_api
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-change_this_in_env}@postgres:5432/${POSTGRES_DB:-field_suite_db}
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY:-change_this_super_secret_key}
      - TENANT_ID=${TENANT_ID:-default}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - ENV=${ENV:-development}
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

  ndvi-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: field_suite_ndvi_worker
    command: celery -A app.celery worker --loglevel=info --concurrency=2
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-change_this_in_env}@postgres:5432/${POSTGRES_DB:-field_suite_db}
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY:-change_this_super_secret_key}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
      - /app/__pycache__
    networks:
      - field_suite_network
    restart: unless-stopped

  flower:
    image: mher/flower:1.2
    container_name: field_suite_flower
    environment:
      - CELERY_BROKER_URL=redis://redis:6379
      - CELERY_RESULT_BACKEND=redis://redis:6379
      - FLOWER_PORT=5555
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
      - "127.0.0.1:80:80"
    depends_on:
      - api
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_ENV=${ENV:-development}
    volumes:
      - ./web:/app
      - /app/node_modules
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

# =====================================
# 5️⃣ إنشاء docker-compose.dev.yml
# =====================================
write_file "$PROJECT_NAME/docker-compose.dev.yml" 'version: '\''3.8'\''
services:
  api:
    build:
      target: development
    volumes:
      - ./backend:/app
      - ./backend/.venv:/app/.venv
    environment:
      - LOG_LEVEL=DEBUG
      - RELOAD=true
      - ENV=development
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
    ports:
      - "8000:8000"

  ndvi-worker:
    build:
      target: development
    volumes:
      - ./backend:/app
    environment:
      - LOG_LEVEL=DEBUG
      - CELERY_LOG_LEVEL=DEBUG

  web:
    build:
      target: development
    volumes:
      - ./web:/app
      - /app/node_modules
    environment:
      - CHOKIDAR_USEPOLLING=true
    command: npm run dev
    ports:
      - "3000:3000"

  postgres:
    ports:
      - "5432:5432"

  redis:
    ports:
      - "6379:6379"

  nginx:
    ports:
      - "8080:80"'

# =====================================
# 6️⃣ إنشاء .env.example
# =====================================
write_file "$PROJECT_NAME/.env.example" 'POSTGRES_DB=field_suite_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_this_super_secure_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

REDIS_URL=redis://redis:6379
REDIS_CACHE_TTL=3600

SECRET_KEY=change_this_super_secret_key_for_jwt_signing
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

OPENWEATHER_API_KEY=your_openweather_key
SENTINEL_CLIENT_ID=your_sentinel_client_id
SENTINEL_CLIENT_SECRET=your_sentinel_client_secret

TENANT_ID=default

LOG_LEVEL=INFO
LOG_FORMAT=json

ENABLE_ADVISOR=true
ENABLE_NDVI_CACHE=true
ENABLE_RATE_LIMITING=true

ENV=development
DEBUG=true
RELOAD=true'

# =====================================
# 7️⃣ إنشاء Dockerfile الباكند
# =====================================
write_file "$PROJECT_NAME/backend/Dockerfile" 'FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/base.txt
COPY requirements/prod.txt requirements/prod.txt

RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements/prod.txt

FROM python:3.11-slim as development

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=development \
    DEBUG=true

COPY . .

RUN chmod +x scripts/init_db.py

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM python:3.11-slim as production

WORKDIR /app

RUN groupadd -r field_suite && useradd -r -g field_suite field_suite

RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY --chown=field_suite:field_suite . .

RUN mkdir -p /app/logs && chown field_suite:field_suite /app/logs

USER field_suite

CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "60", "--log-level", "info"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

LABEL maintainer="Kafaat <kafaat@sahool.ye>" \
      version="1.0.0" \
      description="Field Suite NDVI Service"'

# =====================================
# 8️⃣ إنشاء nginx.conf
# =====================================
write_file "$PROJECT_NAME/nginx/nginx.conf" 'upstream api_backend {
    server api:8000;
}

upstream web_frontend {
    server web:80;
}

limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=ndvi_tiles:10m rate=200r/m;

proxy_cache_path /var/cache/nginx/ndvi levels=1:2 keys_zone=ndvi_cache:10m inactive=60m;

server {
    listen 80;
    server_name localhost;

    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src '\''self'\''; script-src '\''self'\''; style-src '\''self'\'' '\''unsafe-inline'\'';" always;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    location /api/ {
        limit_req zone=api burst=20 nodelay;

        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
    }

    location /api/v1/ndvi/tiles/ {
        limit_req zone=ndvi_tiles burst=50 nodelay;

        proxy_cache ndvi_cache;
        proxy_cache_valid 200 302 1h;
        proxy_cache_valid 404 1m;
        proxy_cache_use_stale error timeout invalid_header updating;

        add_header X-Cache-Status $upstream_cache_status;

        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://web_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /healthz {
        access_log off;
        proxy_pass http://api_backend/health;
    }

    location ~ /\. {
        deny all;
        return 404;
    }

    location ~* \.(env|git|svn|htaccess|htpasswd)$ {
        deny all;
        return 404;
    }
}'

# =====================================
# 9️⃣ إنشاء ملفات SQL
# =====================================
echo_header "🗄️ إنشاء ملفات قواعد البيانات"

write_file "$PROJECT_NAME/init-scripts/01-create-extensions.sql" 'CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;'

write_file "$PROJECT_NAME/init-scripts/02-create-tables.sql" 'CREATE TABLE IF NOT EXISTS fields (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    crop_type VARCHAR(100),
    geometry GEOMETRY(Polygon, 4326) NOT NULL,
    area_ha DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

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
    tile_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(field_id, date)
);

CREATE TABLE IF NOT EXISTS advisor_sessions (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    tenant_id INTEGER NOT NULL,
    recommendations JSONB,
    confidence_score DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    tmax DOUBLE PRECISION,
    tmin DOUBLE PRECISION,
    tmean DOUBLE PRECISION,
    rain_mm DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(field_id, date)
);'

write_file "$PROJECT_NAME/init-scripts/03-create-indexes.sql" 'CREATE INDEX IF NOT EXISTS idx_fields_tenant_id ON fields(tenant_id);
CREATE INDEX IF NOT EXISTS idx_fields_crop_type ON fields(crop_type);
CREATE INDEX IF NOT EXISTS idx_fields_geometry_gist ON fields USING GIST(geometry);

CREATE INDEX IF NOT EXISTS idx_ndvi_results_field_id ON ndvi_results(field_id);
CREATE INDEX IF NOT EXISTS idx_ndvi_results_date ON ndvi_results(date DESC);
CREATE INDEX IF NOT EXISTS idx_ndvi_results_field_date ON ndvi_results(field_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ndvi_results_tenant_id ON ndvi_results(tenant_id) WHERE tenant_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_advisor_sessions_field_id ON advisor_sessions(field_id);
CREATE INDEX IF NOT EXISTS idx_advisor_sessions_tenant_id ON advisor_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_advisor_sessions_created_at ON advisor_sessions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_weather_data_field_id ON weather_data(field_id);
CREATE INDEX IF NOT EXISTS idx_weather_data_date ON weather_data(date DESC);
CREATE INDEX IF NOT EXISTS idx_weather_data_field_date ON weather_data(field_id, date DESC);

ANALYZE fields;
ANALYZE ndvi_results;
ANALYZE advisor_sessions;'

# =====================================
# 10️⃣ إنشيل ملفات الباكند الأساسية
# =====================================
echo_header "🐍 إنشاء ملفات الباكند"

# main.py
write_file "$PROJECT_NAME/backend/app/main.py" 'from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1 import fields, ndvi, satellite, weather, advisor

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Field Suite NDVI API",
    description="API for NDVI analysis and field advisor",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

setup_logging()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(fields.router, prefix="/api/v1", tags=["fields"])
app.include_router(ndvi.router, prefix="/api/v1", tags=["ndvi"])
app.include_router(satellite.router, prefix="/api/v1", tags=["satellite"])
app.include_router(weather.router, prefix="/api/v1", tags=["weather"])
app.include_router(advisor.router, prefix="/api/v1", tags=["advisor"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ndvi-api", "version": "1.0.0"}

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(f"{process_time:.4f}s")
    return response'

# core/config.py
write_file "$PROJECT_NAME/backend/app/core/config.py" 'from pydantic import BaseSettings
from typing import List
import secrets

class Settings(BaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "field_suite_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = ""

    REDIS_URL: str = "redis://localhost:6379"
    REDIS_CACHE_TTL: int = 3600

    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]

    OPENWEATHER_API_KEY: str = ""
    SENTINEL_CLIENT_ID: str = ""
    SENTINEL_CLIENT_SECRET: str = ""

    ENABLE_ADVISOR: bool = True
    ENABLE_NDVI_CACHE: bool = True
    ENABLE_RATE_LIMITING: bool = True

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    ENV: str = "development"
    DEBUG: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()'

# core/logging_config.py
write_file "$PROJECT_NAME/backend/app/core/logging_config.py" 'import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict

def setup_logging():
    class JSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_obj: Dict[str, Any] = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            if hasattr(record, "extra"):
                log_obj.update(record.extra)

            if record.exc_info:
                log_obj["exception"] = self.formatException(record.exc_info)

            return json.dumps(log_obj)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)'

# core/database.py
write_file "$PROJECT_NAME/backend/app/core/database.py" 'from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()'

# =====================================
# 11️⃣ إنشاء API Routers
# =====================================
# api/v1/fields.py
write_file "$PROJECT_NAME/backend/app/api/v1/fields.py" 'from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.field import FieldResponse, FieldCreate
from app.services.field_service import FieldService
from app.dependencies import get_field_service, get_current_user

router = APIRouter()

@router.get("/fields", response_model=List[FieldResponse])
async def get_fields(
    skip: int = 0,
    limit: int = 100,
    field_service: FieldService = Depends(get_field_service),
    current_user=Depends(get_current_user)
):
    return await field_service.get_fields(current_user.tenant_id, skip, limit)

@router.post("/fields", response_model=FieldResponse)
async def create_field(
    field: FieldCreate,
    field_service: FieldService = Depends(get_field_service),
    current_user=Depends(get_current_user)
):
    return await field_service.create_field(field, current_user.tenant_id)'

# api/v1/ndvi.py
write_file "$PROJECT_NAME/backend/app/api/v1/ndvi.py" 'from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import date
from app.schemas.ndvi import NDVIResponse, NDVITimelineResponse, NDVIComputeRequest
from app.services.ndvi_service import NDVIService
from app.dependencies import get_ndvi_service, get_current_user, rate_limiter

router = APIRouter()

@router.get("/ndvi/{field_id}", response_model=NDVIResponse)
@rate_limiter.limit("100/minute")
async def get_ndvi(
    field_id: int,
    target_date: Optional[date] = Query(None),
    ndvi_service: NDVIService = Depends(get_ndvi_service),
    current_user=Depends(get_current_user)
):
    result = await ndvi_service.get_ndvi(field_id, target_date, current_user.tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="NDVI data not found")
    return result

@router.post("/ndvi/compute", status_code=202)
@rate_limiter.limit("10/minute")
async def trigger_ndvi_computation(
    request: NDVIComputeRequest,
    ndvi_service: NDVIService = Depends(get_ndvi_service),
    current_user=Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    job_id = await ndvi_service.trigger_computation(request.field_ids, request.date_range, current_user.tenant_id)
    return {"job_id": job_id, "status": "queued"}'

# api/v1/advisor.py
write_file "$PROJECT_NAME/backend/app/api/v1/advisor.py" 'from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.advisor import FieldContext, Recommendation, AdvisorRequest
from app.services.advisor_service import AdvisorService
from app.dependencies import get_advisor_service, get_current_user

router = APIRouter()

@router.post("/advisor/analyze-field", response_model=List[Recommendation])
async def analyze_field(
    request: AdvisorRequest,
    advisor_service: AdvisorService = Depends(get_advisor_service),
    current_user=Depends(get_current_user)
):
    context = await advisor_service.build_context(request.field_id, current_user.tenant_id)
    return await advisor_service.analyze(context)'

# =====================================
# 12️⃣ إنشاء Schemas
# =====================================
# schemas/field.py
write_file "$PROJECT_NAME/backend/app/schemas/field.py" 'from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class FieldCreate(BaseModel):
    name: str
    crop_type: str
    geometry: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class FieldResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    crop_type: str
    geometry: Dict[str, Any]
    area_ha: Optional[float]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True'

# schemas/ndvi.py
write_file "$PROJECT_NAME/backend/app/schemas/ndvi.py" 'from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date

class NDVIZones(BaseModel):
    low: Dict[str, float]
    medium: Dict[str, float]
    high: Dict[str, float]

class NDVIResponse(BaseModel):
    field_id: int
    date: date
    mean_ndvi: float
    min_ndvi: float
    max_ndvi: float
    std_ndvi: float
    pixel_count: int
    zones: NDVIZones
    tile_url: Optional[str] = None

class NDVIComputeRequest(BaseModel):
    field_ids: List[int]
    date_range: Dict[str, date]'

# schemas/advisor.py
write_file "$PROJECT_NAME/backend/app/schemas/advisor.py" 'from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class NDVIContext(BaseModel):
    mean: float
    min: float
    max: float
    zones: Dict[str, float]

class WeatherContext(BaseModel):
    tmax: float
    tmin: float
    tmean: float
    rain_mm: float
    humidity: float
    wind_speed: float

class CropContext(BaseModel):
    type: str
    growth_stage: Optional[str] = None
    planting_date: Optional[str] = None

class FieldContext(BaseModel):
    field_id: int
    tenant_id: int
    name: str
    ndvi: NDVIContext
    weather: WeatherContext
    crop: CropContext
    timestamp: datetime = datetime.utcnow()

class Recommendation(BaseModel):
    id: str
    rule_name: str
    priority: str
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    actions: List[Dict[str, Any]]
    field_id: int
    timestamp: datetime

class AdvisorRequest(BaseModel):
    field_id: int'

# =====================================
# 13️⃣ إنشاء Services
# =====================================
# services/field_service.py
write_file "$PROJECT_NAME/backend/app/services/field_service.py" 'from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.field import Field
from app.schemas.field import FieldCreate

class FieldService:
    def __init__(self, db: Session):
        self.db = db

    async def get_fields(self, tenant_id: int, skip: int = 0, limit: int = 100) -> List[Field]:
        return self.db.query(Field).filter(Field.tenant_id == tenant_id).offset(skip).limit(limit).all()

    async def create_field(self, field_data: FieldCreate, tenant_id: int) -> Field:
        field = Field(**field_data.dict(), tenant_id=tenant_id)
        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)
        return field'

# services/ndvi_service.py
write_file "$PROJECT_NAME/backend/app/services/ndvi_service.py" 'from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date
import redis
import json
from celery import Celery
from app.repositories.ndvi_repository import NDVIRepository
from app.repositories.field_repository import FieldRepository

class NDVIService:
    def __init__(self, db: Session, cache: redis.Redis):
        self.db = db
        self.cache = cache
        self.ndvi_repo = NDVIRepository(db)
        self.field_repo = FieldRepository(db)
        self.celery_app = Celery('\''ndvi_tasks'\'', broker='\''redis://redis:6379'\'', backend='\''redis://redis:6379'\'')

    async def get_ndvi(self, field_id: int, target_date: Optional[date] = None, tenant_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        cache_key = f"ndvi:{field_id}:{target_date or '\''latest'\''}"

        cached_data = self.cache.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        result = await self.ndvi_repo.get_ndvi(field_id, target_date)

        if result and tenant_id:
            field = await self.field_repo.get_field(field_id, tenant_id)
            if not field:
                return None

        if result:
            self.cache.setex(cache_key, 3600, json.dumps(result))

        return result

    async def trigger_computation(self, field_ids: List[int], date_range: Dict[str, date], tenant_id: int) -> str:
        for field_id in field_ids:
            field = await self.field_repo.get_field(field_id, tenant_id)
            if not field:
                raise ValueError(f"Field {field_id} not found or not owned by tenant")

        task = self.celery_app.send_task('\''tasks.compute_ndvi_batch'\'', args=[field_ids, date_range, tenant_id], queue='\''ndvi'\'')
        return task.id'

# =====================================
# 14️⃣ إنشاء Repositories
# =====================================
# repositories/field_repository.py
write_file "$PROJECT_NAME/backend/app/repositories/field_repository.py" 'from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.field import Field

class FieldRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_field(self, field_id: int, tenant_id: int) -> Optional[Field]:
        return self.db.query(Field).filter(Field.id == field_id, Field.tenant_id == tenant_id).first()'

# repositories/ndvi_repository.py
write_file "$PROJECT_NAME/backend/app/repositories/ndvi_repository.py" 'from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import date
from app.models.ndvi import NDVIResult

class NDVIRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_ndvi(self, field_id: int, target_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        query = self.db.query(NDVIResult).filter(NDVIResult.field_id == field_id)

        if target_date:
            query = query.filter(NDVIResult.date == target_date)
        else:
            query = query.order_by(NDVIResult.date.desc())

        result = query.first()

        if not result:
            return None

        return {
            "field_id": result.field_id,
            "date": result.date,
            "mean_ndvi": result.mean_ndvi,
            "min_ndvi": result.min_ndvi,
            "max_ndvi": result.max_ndvi,
            "std_ndvi": result.std_ndvi,
            "pixel_count": result.pixel_count,
            "tile_url": result.tile_url,
            "zones": {"low": {"percentage": 30, "area_ha": 15.2}, "medium": {"percentage": 50, "area_ha": 25.4}, "high": {"percentage": 20, "area_ha": 10.1}}
        }'

# =====================================
# 15️⃣ إنشاء Models
# =====================================
# models/field.py
write_file "$PROJECT_NAME/backend/app/models/field.py" 'from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, JSON, func
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
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    metadata = Column(JSON)'

# models/ndvi.py
write_file "$PROJECT_NAME/backend/app/models/ndvi.py" 'from sqlalchemy import Column, Integer, ForeignKey, Date, Float, TIMESTAMP, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class NDVIResult(Base):
    __tablename__ = "ndvi_results"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    ndvi_value = Column(Float)
    mean_ndvi = Column(Float)
    min_ndvi = Column(Float)
    max_ndvi = Column(Float)
    std_ndvi = Column(Float)
    pixel_count = Column(Integer)
    tile_url = Column(String(500))
    created_at = Column(TIMESTAMP, server_default="now()")

    field = relationship("Field", back_populates="ndvi_results")'

# =====================================
# 16️⃣ إنشاء Dependencies
# =====================================
write_file "$PROJECT_NAME/backend/app/dependencies.py" 'from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.services.ndvi_service import NDVIService
from app.services.field_service import FieldService
from app.services.advisor_service import AdvisorService
import redis

security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)

class MockUser:
    def __init__(self):
        self.id = 1
        self.tenant_id = 1
        self.is_admin = True

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token != "fake-super-secret-token":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return MockUser()

def get_ndvi_service(db: Session = Depends(get_db)):
    cache = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return NDVIService(db, cache)

def get_field_service(db: Session = Depends(get_db)):
    return FieldService(db)

def get_advisor_service(db: Session = Depends(get_db)):
    return AdvisorService(db)'

# =====================================
# 17️⃣ إنشاء ملفات الواجهة الأمامية
# =====================================
echo_header "⚛️ إنشاء ملفات الواجهة الأمامية"

# package.json
write_file "$PROJECT_NAME/web/package.json" '{
  "name": "field-suite-web",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "@tanstack/react-query": "^4.32.0",
    "axios": "^1.4.0",
    "lucide-react": "^0.263.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.14.2",
    "leaflet": "^1.9.4",
    "@types/leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1"
  },
  "scripts": {
    "dev": "vite --port 3000",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "format": "prettier --write src"
  },
  "devDependencies": {
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.0.3",
    "eslint": "^8.45.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.3",
    "prettier": "^3.0.0",
    "typescript": "^5.0.2",
    "vite": "^4.4.5",
    "vitest": "^0.33.0",
    "@vitest/coverage-v8": "^0.33.0"
  }
}'

# tsconfig.json
write_file "$PROJECT_NAME/web/tsconfig.json" '{
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
}'

# API Client
write_file "$PROJECT_NAME/web/src/api/client.ts" 'import axios, { AxiosInstance } from '\''axios'\'';
import { QueryClient } from '\''@tanstack/react-query'\'';

export const API_BASE_URL = process.env.REACT_APP_API_URL || '\''http://localhost:8000'\'';

export interface Field {
  id: number;
  tenant_id: number;
  name: string;
  crop_type: string;
  geometry: any;
  area_ha?: number;
  created_at: string;
}

export interface NDVIData {
  field_id: number;
  date: string;
  mean_ndvi: number;
  min_ndvi: number;
  max_ndvi: number;
  std_ndvi: number;
  pixel_count: number;
  zones: {
    low: { percentage: number; area_ha: number };
    medium: { percentage: number; area_ha: number };
    high: { percentage: number; area_ha: number };
  };
  tile_url?: string;
}

export interface Recommendation {
  id: string;
  rule_name: string;
  priority: '\''critical'\'' | '\''high'\'' | '\''medium'\'' | '\''low'\'';
  title_ar: string;
  title_en: string;
  description_ar: string;
  description_en: string;
  actions: Array<{
    action_ar: string;
    action_en: string;
    urgency: string;
  }>;
  timestamp: string;
  metadata?: Record<string, any>;
}

class FieldSuiteAPI {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: { '\''Content-Type'\'': '\''application/json'\'' },
    });

    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('\''token'\'');
      if (token) config.headers.Authorization = `Bearer ${token}`;
      return config;
    });
  }

  async getFields(): Promise<Field[]> {
    const { data } = await this.client.get('\''/api/v1/fields'\'');
    return data;
  }

  async getNDVI(fieldId: number, targetDate?: string): Promise<NDVIData> {
    const params = targetDate ? { target_date: targetDate } : {};
    const { data } = await this.client.get(`/api/v1/ndvi/${fieldId}`, { params });
    return data;
  }

  async analyzeField(fieldId: number): Promise<Recommendation[]> {
    const { data } = await this.client.post('\''/api/v1/advisor/analyze-field'\'', { field_id: fieldId });
    return data;
  }
}

export const api = new FieldSuiteAPI();
export const queryClient = new QueryClient();'

# =====================================
# 18️⃣ إنشاء سكريبتات المساعدة
# =====================================
echo_header "📜 إنشاء سكريبتات المساعدة"

write_file "$PROJECT_NAME/scripts/health-check.sh" '#!/bin/bash
echo "🔍 فحص صحة Field Suite Services"
echo "================================"

cd "$(dirname "$0")/.."

FAILED=0
for service in api web redis postgres ndvi-worker; do
    if docker-compose ps | grep -q "$service.*Up"; then
        if [ "$service" == "api" ]; then
            PORT=$(docker-compose port api 8000 2>/dev/null | cut -d: -f2)
            if [ -n "$PORT" ] && curl -s -f http://localhost:$PORT/health > /dev/null 2>&1; then
                echo "✅ $service: يعمل والـ health check ناجح"
            else
                echo "⚠️  $service: يعمل لكن health check فشل"
                FAILED=$((FAILED + 1))
            fi
        else
            echo "✅ $service: يعمل"
        fi
    else
        echo "❌ $service: متوقف أو يعطي أخطاء"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "💾 مساحة القرص المستخدمة:"
docker system df

echo ""
echo "🧠 استخدام الذاكرة:"
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"

exit $FAILED'

write_file "$PROJECT_NAME/scripts/stop-cleanup.sh" '#!/bin/bash
echo "🛑 إيقاف Field Suite والتنظيف"
echo "============================="

cd "$(dirname "$0")/.."

read -p "هل أنت متأكد من إيقاف جميع الخدمات؟ (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "إلغاء الإيقاف"
    exit 0
fi

docker-compose down --remove-orphans --volumes

read -p "هل تريد حذف الـ Docker images؟ (y/n): " delete_images
if [ "$delete_images" == "y" ]; then
    docker-compose rm -f
    docker system prune -f --volumes
    echo "✅ تم حذف الـ images والـ volumes"
fi

echo "✅ تم إيقاف المشروع وتنظيف البيئة"'

# =====================================
# 19️⃣ إنشاء ملفات Requirements
# =====================================
echo_header "📦 إنشاء ملفات Requirements"

write_file "$PROJECT_NAME/backend/requirements/base.txt" 'fastapi==0.100.0
uvicorn[standard]==0.22.0
sqlalchemy==2.0.18
alembic==1.11.1
geoalchemy2==0.14.1
psycopg2-binary==2.9.6
redis==4.6.0
celery==5.3.1
pydantic==1.10.11
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
slowapi==0.1.8
python-multipart==0.0.6
email-validator==2.0.0.post2
requests==2.31.0
httpx==0.24.1
pillow==10.0.0
numpy==1.25.1
pandas==2.0.3
shapely==2.0.1
rasterio==1.3.8
sentinelhub==3.9.1'

write_file "$PROJECT_NAME/backend/requirements/prod.txt" '-r base.txt
gunicorn==21.2.0
prometheus-client==0.17.1
sentry-sdk[fastapi]==1.28.1
pyyaml==6.0.1'

write_file "$PROJECT_NAME/backend/requirements/dev.txt" '-r base.txt
pytest==7.4.0
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.11.1
black==23.7.0
flake8==6.0.0
isort==5.12.0
mypy==1.4.1
pre-commit==3.3.3
pip-audit==2.6.1
tox==4.6.4'

# =====================================
# 20️⃣ إعطاء صلاحيات التنفيذ ونسخ .env
# =====================================
chmod +x "$PROJECT_NAME/scripts/health-check.sh"
chmod +x "$PROJECT_NAME/scripts/stop-cleanup.sh"

if [ ! -f "$PROJECT_NAME/.env" ]; then
    cp "$PROJECT_NAME/.env.example" "$PROJECT_NAME/.env"
    echo -e "${YELLOW}⚠️  تم إنشاء ملف .env من النموذج${NC}"
fi

# =====================================
# 21️⃣ البناء والتشغيل
# =====================================
echo_header "🔨 بناء وتشغيل المشروع"

cd "$PROJECT_NAME"
docker-compose build --no-cache --parallel

echo -e "${YELLOW}🚀 تشغيل الخدمات...${NC}"
docker-compose up -d --remove-orphans

echo -e "${YELLOW}⏳ انتظار بدء الخدمات (25 ثانية)...${NC}"
sleep 25

# =====================================
# 22️⃣ فحص صحة الخدمات
# =====================================
echo_header "📊 فحص صحة الخدمات"

./scripts/health-check.sh

# =====================================
# 23️⃣ عرض المعلومات النهائية
# =====================================
API_PORT=$(docker-compose port api 8000 2>/dev/null | cut -d: -f2)
WEB_PORT=$(docker-compose port web 80 2>/dev/null | cut -d: -f2)
FLOWER_PORT=$(docker-compose port flower 5555 2>/dev/null | cut -d: -f2)

echo -e "${GREEN}✅ تم الانتهاء! المشروع يعمل على:${NC}"
echo -e "🌐 الواجهة الأمامية: ${BLUE}http://localhost:${WEB_PORT}${NC}"
echo -e "🔌 API Docs: ${BLUE}http://localhost:${API_PORT}/docs${NC}"
echo -e "🌸 Celery Monitor: ${BLUE}http://localhost:${FLOWER_PORT}${NC}"
echo -e "📦 Redis: ${BLUE}localhost:6379${NC}"
echo -e "🐘 PostgreSQL: ${BLUE}localhost:5432${NC}"

echo -e "\n${YELLOW}📋 ملاحظات هامة:${NC}"
echo -e "1. تأكد من تعديل ملف .env قبل الاستخدام الإنتاجي"
echo -e "2. للسجلات المباشرة: ${BLUE}docker-compose logs -f${NC}"
echo -e "3. لإيقاف المشروع: ${BLUE}./scripts/stop-cleanup.sh${NC}"
echo -e "4. لإعادة البناء: ${BLUE}docker-compose build --no-cache${NC}"
echo -e "5. فحص الصحة: ${BLUE}./scripts/health-check.sh${NC}"
echo -e "6. للتطوير: ${BLUE}docker-compose -f docker-compose.yml -f docker-compose.dev.yml up${NC}"

echo -e "\n${GREEN}🎉 تم إعداد Field Suite بنجاح!${NC}"
echo -e " ${GREEN}المشروع جاهز للاستخدام${NC}"

exit 0
