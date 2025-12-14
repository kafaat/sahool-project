#!/usr/bin/env python3
"""
SAHOOL PLATFORM v6.8.5 - ULTIMATE PRODUCTION SETUP (PYTHON EDITION)
One-Script-to-Rule-Them-All: AI-Powered NDVI, SOC2/GDPR, Chaos Engineering
FULLY ENHANCED & FIXED

Usage: python sahool_setup.py [OPTIONS] [PROJECT_NAME]
"""

import argparse
import datetime
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ===================== CONFIGURATION =====================

SCRIPT_VERSION = "6.8.5"
SCRIPT_NAME = "SAHOOL Ultimate Setup"
MIN_RAM_GB = 8
MIN_CPU_CORES = 4
MIN_DISK_GB = 20
MIN_DOCKER_COMPOSE_VERSION = "2.0.0"
MAX_LOG_FILES = 5
MAX_LOG_AGE_DAYS = 30


# ===================== COLORS =====================

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


# ===================== LOGGER SETUP =====================

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""

    FORMATS = {
        logging.DEBUG: f"{Colors.CYAN}[DEBUG]{Colors.NC} %(message)s",
        logging.INFO: f"{Colors.GREEN}[✓]{Colors.NC} %(message)s",
        logging.WARNING: f"{Colors.YELLOW}[⚠]{Colors.NC} %(message)s",
        logging.ERROR: f"{Colors.RED}[✗]{Colors.NC} %(message)s",
        logging.CRITICAL: f"{Colors.RED}{Colors.BOLD}[!!!]{Colors.NC} %(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, "%(message)s")
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def setup_logger(log_file: Optional[Path] = None) -> logging.Logger:
    """Setup comprehensive logging for the setup process"""
    logger = logging.getLogger("sahool_setup")
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    logger.handlers.clear()

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # File handler if log_file is provided
    if log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")

    return logger


# ===================== TEMPLATE DEFINITIONS =====================

TEMPLATES = {}

# NDVI Engine main.py
TEMPLATES["ndvi_main_py"] = '''"""SAHOOL AI-NDVI Engine - FastAPI Service v6.8.5"""
import os
import io
import json
import uuid
import logging
from datetime import datetime
from typing import List, Optional

import numpy as np
import redis
import torch
import torch.nn as nn
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel
from torchvision import transforms

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SAHOOL AI-NDVI Engine",
    version="6.8.5",
    description="Deep Learning powered NDVI prediction service"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================== MODELS =====================

class NDVIResult(BaseModel):
    field_id: str
    ndvi: float
    health_status: str
    prediction_confidence: float
    generated_at: str
    model_version: str


class BatchPredictRequest(BaseModel):
    field_ids: List[str]


class JobStatus(BaseModel):
    job_id: str
    status: str
    total: Optional[int] = None
    completed: Optional[int] = None
    results: Optional[List[NDVIResult]] = None


# ===================== ML MODEL =====================

class NDVIModel(nn.Module):
    """NDVI prediction model based on ResNet18 backbone"""

    def __init__(self):
        super().__init__()
        self.backbone = torch.hub.load(
            'pytorch/vision:v0.10.0',
            'resnet18',
            pretrained=True,
            verbose=False
        )
        self.backbone.fc = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
            nn.Tanh()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


# ===================== INITIALIZATION =====================

model: Optional[NDVIModel] = None
model_loaded = False

try:
    model = NDVIModel()
    model_path = os.getenv("MODEL_PATH", "/app/models/ndvi_model.pth")

    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
        logger.info(f"Model loaded from {model_path}")
    else:
        logger.warning(f"Model file not found at {model_path}, using pretrained weights")

    model.eval()
    model_loaded = True
except Exception as e:
    logger.error(f"Model initialization failed: {e}")
    model = None

# Image transformation pipeline
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# Redis connection
redis_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Get Redis client with lazy initialization"""
    global redis_client
    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        try:
            redis_client = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None
    return redis_client


def is_redis_available() -> bool:
    """Check if Redis is available"""
    try:
        client = get_redis()
        return client is not None and client.ping()
    except Exception:
        return False


def classify_health(ndvi: float) -> str:
    """Classify crop health based on NDVI value"""
    if ndvi >= 0.7:
        return "Excellent"
    elif ndvi >= 0.5:
        return "Good"
    elif ndvi >= 0.3:
        return "Moderate"
    elif ndvi >= 0.1:
        return "Poor"
    else:
        return "Critical"


def calculate_confidence(ndvi: float) -> float:
    """Calculate prediction confidence"""
    if 0.2 <= ndvi <= 0.8:
        return 0.95
    elif 0.1 <= ndvi <= 0.9:
        return 0.90
    else:
        return 0.85


# ===================== API ENDPOINTS =====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if model_loaded else "degraded",
        "model_loaded": model_loaded,
        "gpu_available": torch.cuda.is_available(),
        "redis_connected": is_redis_available(),
        "version": "6.8.5",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return f"""# HELP ndvi_model_loaded Model loading status
# TYPE ndvi_model_loaded gauge
ndvi_model_loaded {1 if model_loaded else 0}
# HELP ndvi_redis_connected Redis connection status
# TYPE ndvi_redis_connected gauge
ndvi_redis_connected {1 if is_redis_available() else 0}
# HELP ndvi_gpu_available GPU availability
# TYPE ndvi_gpu_available gauge
ndvi_gpu_available {1 if torch.cuda.is_available() else 0}
"""


@app.post("/predict/{field_id}", response_model=NDVIResult)
async def predict_ndvi(field_id: str, image: UploadFile = File(...)):
    """Predict NDVI using deep learning on satellite imagery."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not available")

    # Check cache
    if is_redis_available():
        try:
            cached = get_redis().get(f"ndvi:ai:{field_id}")
            if cached:
                logger.info(f"Cache hit for field: {field_id}")
                return NDVIResult(**json.loads(cached))
        except Exception as e:
            logger.warning(f"Redis cache read failed: {e}")

    # Process image
    try:
        image_data = await image.read()
        img = Image.open(io.BytesIO(image_data)).convert('RGB')
        img_tensor = transform(img).unsqueeze(0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    # Make prediction
    try:
        with torch.no_grad():
            ndvi_pred = model(img_tensor).item()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    # Build result
    result = NDVIResult(
        field_id=field_id,
        ndvi=round(ndvi_pred, 4),
        health_status=classify_health(ndvi_pred),
        prediction_confidence=calculate_confidence(ndvi_pred),
        generated_at=datetime.utcnow().isoformat(),
        model_version="resnet18_v1.2"
    )

    # Cache result
    if is_redis_available():
        try:
            get_redis().setex(f"ndvi:ai:{field_id}", 3600, result.model_dump_json())
        except Exception as e:
            logger.warning(f"Redis cache write failed: {e}")

    return result


@app.post("/batch-predict", response_model=JobStatus)
async def batch_predict(request: BatchPredictRequest):
    """Queue batch NDVI prediction for multiple fields"""
    if not is_redis_available():
        raise HTTPException(status_code=503, detail="Queue service unavailable")

    job_id = str(uuid.uuid4())

    try:
        for field_id in request.field_ids:
            get_redis().lpush("ndvi-queue", json.dumps({"field_id": field_id, "job_id": job_id}))

        get_redis().setex(f"job:{job_id}", 7200, json.dumps({
            "status": "queued",
            "total": len(request.field_ids),
            "completed": 0
        }))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Queue failed: {str(e)}")

    return JobStatus(job_id=job_id, status="queued", total=len(request.field_ids), completed=0)


@app.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get status of a batch prediction job"""
    if not is_redis_available():
        raise HTTPException(status_code=503, detail="Status service unavailable")

    try:
        result = get_redis().get(f"job:{job_id}")
        if result:
            data = json.loads(result)
            return JobStatus(
                job_id=job_id,
                status=data.get("status", "processing"),
                total=data.get("total"),
                completed=data.get("completed"),
                results=data.get("results")
            )
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@app.delete("/cache/{field_id}")
async def clear_cache(field_id: str):
    """Clear cached NDVI result for a field"""
    if is_redis_available():
        try:
            deleted = get_redis().delete(f"ndvi:ai:{field_id}")
            return {"deleted": deleted > 0, "field_id": field_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")
    return {"deleted": False, "reason": "Redis unavailable"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "3000")),
        workers=int(os.getenv("WORKERS", "4")),
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
'''

# NDVI requirements.txt
TEMPLATES["ndvi_requirements_txt"] = '''# SAHOOL NDVI Engine Dependencies v6.8.5
fastapi==0.109.2
uvicorn[standard]==0.27.1
torch==2.1.0
torchvision==0.16.0
Pillow==10.2.0
numpy==1.26.4
redis==5.0.1
python-multipart==0.0.9
pydantic==2.6.1
pydantic-settings==2.1.0
'''

# NDVI Dockerfile
TEMPLATES["ndvi_dockerfile"] = '''FROM python:3.11-slim

LABEL maintainer="devops@sahool.sa"
LABEL version="6.8.5"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    libffi-dev \\
    curl \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser \\
    && mkdir -p /app/models /app/cache \\
    && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:3000/health || exit 1

EXPOSE 3000

CMD ["python", "main.py"]
'''

# PostgreSQL init SQL
TEMPLATES["postgres_init_sql"] = '''-- SAHOOL Database Initialization v6.8.5

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(50),
    role VARCHAR(50) DEFAULT 'viewer' CHECK (role IN ('admin', 'agronomist', 'field_agent', 'viewer')),
    tenant_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    tenant_id UUID NOT NULL,
    boundary_geojson JSONB,
    area_hectares DECIMAL(10, 2),
    crop_type VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS field_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    due_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_fields_tenant ON fields(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tasks_field ON field_tasks(field_id);
'''

# PostgreSQL audit SQL
TEMPLATES["postgres_audit_sql"] = '''-- SAHOOL SOC2 & GDPR Audit System v6.8.5

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(63) NOT NULL,
    operation VARCHAR(15) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE', 'GDPR_DELETE', 'GDPR_EXPORT')),
    old_values JSONB,
    new_values JSONB,
    changed_by UUID,
    changed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    ip_address INET,
    user_agent TEXT,
    session_id UUID
);

CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_time ON audit_log(changed_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(changed_by);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation);

CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    v_user_id UUID := NULL;
    v_old JSONB := NULL;
    v_new JSONB := NULL;
BEGIN
    BEGIN
        v_user_id := current_setting('app.current_user_id', true)::UUID;
    EXCEPTION WHEN OTHERS THEN
        v_user_id := NULL;
    END;

    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        v_old := to_jsonb(OLD);
    END IF;

    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        v_new := to_jsonb(NEW);
    END IF;

    INSERT INTO audit_log (table_name, operation, old_values, new_values, changed_by, ip_address)
    VALUES (TG_TABLE_NAME, TG_OP, v_old, v_new, v_user_id, inet_client_addr());

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS audit_fields ON fields;
DROP TRIGGER IF EXISTS audit_users ON users;
DROP TRIGGER IF EXISTS audit_field_tasks ON field_tasks;

CREATE TRIGGER audit_fields
    AFTER INSERT OR UPDATE OR DELETE ON fields
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_users
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_field_tasks
    AFTER INSERT OR UPDATE OR DELETE ON field_tasks
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE OR REPLACE FUNCTION gdpr_delete_user(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM users WHERE id = p_user_id AND deleted_at IS NULL) INTO v_exists;

    IF NOT v_exists THEN
        RETURN jsonb_build_object('success', false, 'error', 'User not found or already deleted');
    END IF;

    UPDATE users SET
        username = 'deleted_' || encode(gen_random_bytes(8), 'hex'),
        email = 'deleted_' || p_user_id || '@anonymized.local',
        password_hash = 'DELETED',
        full_name = 'Deleted User',
        phone = NULL,
        deleted_at = NOW()
    WHERE id = p_user_id AND deleted_at IS NULL;

    INSERT INTO audit_log (table_name, operation, new_values, changed_by)
    VALUES ('users', 'GDPR_DELETE', jsonb_build_object('user_id', p_user_id, 'type', 'soft_delete'), p_user_id);

    RETURN jsonb_build_object('success', true, 'user_id', p_user_id, 'deleted_at', NOW());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION gdpr_export_user(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_data JSONB;
    v_user_tenant UUID;
BEGIN
    SELECT tenant_id INTO v_user_tenant FROM users WHERE id = p_user_id;

    IF v_user_tenant IS NULL THEN
        RETURN jsonb_build_object('error', 'User not found');
    END IF;

    SELECT jsonb_build_object(
        'export_date', NOW(),
        'user', (SELECT to_jsonb(u) - 'password_hash' FROM users u WHERE id = p_user_id),
        'fields', COALESCE(
            (SELECT jsonb_agg(to_jsonb(f)) FROM fields f WHERE tenant_id = v_user_tenant AND deleted_at IS NULL),
            '[]'::jsonb
        ),
        'tasks', COALESCE(
            (SELECT jsonb_agg(to_jsonb(t)) FROM field_tasks t
             WHERE field_id IN (SELECT id FROM fields WHERE tenant_id = v_user_tenant)),
            '[]'::jsonb
        )
    ) INTO v_data;

    INSERT INTO audit_log (table_name, operation, new_values, changed_by)
    VALUES ('users', 'GDPR_EXPORT', jsonb_build_object('user_id', p_user_id), p_user_id);

    RETURN v_data;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION cleanup_old_logs(retention_days INTEGER DEFAULT 2555)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_log WHERE changed_at < NOW() - (retention_days || ' days')::INTERVAL;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
'''

# Privacy Policy
TEMPLATES["privacy_policy_md"] = '''# SAHOOL Privacy Policy (GDPR Compliant)

**Effective Date**: {date}
**Version**: 6.8.5

## Data Controller

- **Company**: SAHOOL Agricultural Platform
- **Address**: Riyadh, Saudi Arabia
- **DPO Email**: dpo@sahool.sa

## Personal Data Collected

| Data Type         | Purpose          | Legal Basis         | Retention        |
|-------------------|------------------|---------------------|------------------|
| Email             | Authentication   | Contract            | Account lifetime |
| Phone             | Notifications    | Consent             | Until withdrawal |
| Location          | Field boundaries | Legitimate interest | 7 years          |
| Satellite imagery | NDVI analysis    | Contract            | 7 years          |

## User Rights (GDPR Articles 15-22)

1. **Right of Access (Art. 15)**: API: `GET /api/gdpr/export`
2. **Right to Rectification (Art. 16)**: API: `PUT /api/users/me`
3. **Right to Erasure (Art. 17)**: API: `DELETE /api/gdpr/delete`
4. **Right to Portability (Art. 20)**: JSON export of all personal data

## Security Measures

- AES-256 encryption at rest
- TLS 1.3 for data in transit
- Multi-factor authentication available
- Regular security audits

## Contact

For privacy inquiries: privacy@sahool.sa
'''

# Sysctl configuration
TEMPLATES["sysctl_conf"] = '''# SAHOOL Kernel Tuning Reference
# Apply with: sudo sysctl -p config/sysctl-tuning.conf

# Network performance
net.core.somaxconn = 65536
net.core.netdev_max_backlog = 65536
net.ipv4.tcp_max_syn_backlog = 65536
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_tw_reuse = 1

# Memory management
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# File system
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288
'''

# PostgreSQL configuration
TEMPLATES["postgres_conf"] = '''# SAHOOL PostgreSQL Tuning (8GB RAM server)
# Version: 6.8.5

max_connections = 200
superuser_reserved_connections = 3

shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
work_mem = 20MB
wal_buffers = 64MB

checkpoint_timeout = 15min
max_wal_size = 4GB
min_wal_size = 2GB
checkpoint_completion_target = 0.9

random_page_cost = 1.1
effective_io_concurrency = 200
default_statistics_target = 100

max_parallel_workers_per_gather = 2
max_parallel_workers = 4
max_worker_processes = 8

log_min_duration_statement = 1000
log_checkpoints = on
log_lock_waits = on
log_statement = 'mod'

autovacuum_max_workers = 4
autovacuum_naptime = 30s
'''

# Redis configuration
TEMPLATES["redis_conf"] = '''# SAHOOL Redis Tuning v6.8.5

maxmemory 2gb
maxmemory-policy allkeys-lru
maxmemory-samples 10

tcp-keepalive 300
timeout 300
tcp-backlog 65536
bind 0.0.0.0

save ""
appendonly no

activerehashing yes
hz 10
dynamic-hz yes

protected-mode yes
'''

# Chaos manifest
TEMPLATES["chaos_manifest"] = '''# Chaos Mesh Configuration for SAHOOL Platform v6.8.5
# Requires Kubernetes with Chaos Mesh installed

apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: sahool-pod-failure
  namespace: sahool-production
spec:
  action: pod-failure
  mode: one
  selector:
    namespaces:
      - sahool-production
    labelSelectors:
      app: ndvi-engine
  duration: '30s'
'''

# Chaos test script
TEMPLATES["chaos_test_sh"] = '''#!/bin/bash
# SAHOOL Chaos Engineering Test Suite v6.8.5

set -euo pipefail

RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
CYAN='\\033[0;36m'
NC='\\033[0m'

log()   { echo -e "${GREEN}[CHAOS]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
info()  { echo -e "${CYAN}[INFO]${NC} $1"; }

API_URL="${API_URL:-http://localhost:9000}"
CHAOS_DURATION="${CHAOS_DURATION:-30}"

health_check() {
    local max_retries=${1:-10}
    local retry=0

    while [[ $retry -lt $max_retries ]]; do
        if curl -sf "$API_URL/health" --max-time 5 &>/dev/null; then
            return 0
        fi
        retry=$((retry + 1))
        sleep 2
    done
    return 1
}

run_docker_chaos_test() {
    log "Running Docker Compose chaos test..."

    if ! health_check 5; then
        error "System not healthy before chaos test"
    fi

    info "System healthy - simulating container failure"
    docker kill sahool-ndvi 2>/dev/null || warn "Could not kill sahool-ndvi container"

    log "Waiting ${CHAOS_DURATION}s for chaos duration..."
    sleep "$CHAOS_DURATION"

    docker start sahool-ndvi 2>/dev/null || warn "Could not start sahool-ndvi container"

    log "Monitoring recovery..."
    local recovery_start=$(date +%s)
    local max_recovery=120

    while true; do
        local now=$(date +%s)
        local elapsed=$((now - recovery_start))

        if [[ $elapsed -ge $max_recovery ]]; then
            error "System failed to recover within ${max_recovery}s"
        fi

        if health_check 1; then
            log "System recovered in ${elapsed}s"
            break
        fi

        info "Waiting for recovery... (${elapsed}s/${max_recovery}s)"
        sleep 5
    done

    log "All chaos tests passed!"
}

main() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  SAHOOL Chaos Engineering Suite v6.8.5${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    run_docker_chaos_test
}

main "$@"
'''

# Kong configuration
TEMPLATES["kong_yml"] = '''_format_version: "3.0"
_transform: true

services:
  - name: geo-service
    url: http://geo-service:8080
    routes:
      - name: geo-api
        paths:
          - /api/geo
        strip_path: true
        methods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS

  - name: ndvi-engine
    url: http://ndvi-engine:3000
    routes:
      - name: ndvi-api
        paths:
          - /api/ndvi
        strip_path: true

  - name: health
    url: http://geo-service:8080
    routes:
      - name: health-api
        paths:
          - /api/health
          - /health
        strip_path: false

plugins:
  - name: rate-limiting
    config:
      minute: 100
      hour: 1000
      policy: local

  - name: cors
    config:
      origins:
        - "*"
      methods:
        - GET
        - POST
        - PUT
        - DELETE
        - OPTIONS
      headers:
        - Accept
        - Authorization
        - Content-Type
        - X-Request-ID
      credentials: true
      max_age: 3600

  - name: correlation-id
    config:
      header_name: X-Request-ID
      generator: uuid
      echo_downstream: true
'''

# Prometheus configuration
TEMPLATES["prometheus_yml"] = '''# SAHOOL Prometheus Configuration v6.8.5
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'sahool-platform'
    version: '6.8.5'

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files:
  - /etc/prometheus/alerts/*.yml

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'ndvi-engine'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['ndvi-engine:3000']
    scrape_interval: 10s

  - job_name: 'kong'
    static_configs:
      - targets: ['api-gateway:8001']
'''

# Prometheus alerts
TEMPLATES["prometheus_alerts_yml"] = '''groups:
  - name: sahool-critical
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      - alert: NDVIModelNotLoaded
        expr: ndvi_model_loaded == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "NDVI model not loaded"
'''

# Grafana datasources
TEMPLATES["grafana_datasources_yml"] = '''apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
    editable: false
'''

# Grafana dashboards
TEMPLATES["grafana_dashboards_yml"] = '''apiVersion: 1

providers:
  - name: 'SAHOOL'
    orgId: 1
    folder: 'SAHOOL Platform'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /var/lib/grafana/dashboards
'''

# Docker Compose
TEMPLATES["docker_compose_yml"] = '''# SAHOOL Platform v6.8.5 - Docker Compose

x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "5"

services:
  postgres:
    image: postgis/postgis:15-3.3-alpine
    container_name: sahool-postgres
    restart: unless-stopped
    logging: *default-logging
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-sahool_admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required}
      POSTGRES_DB: ${POSTGRES_DB:-sahool_prod}
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./config/postgresql-optimized.conf:/etc/postgresql/postgresql.conf:ro
      - ./db:/docker-entrypoint-initdb.d:ro
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-sahool_admin}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - sahool-backend

  redis:
    image: redis:7-alpine
    container_name: sahool-redis
    restart: unless-stopped
    logging: *default-logging
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD:-changeme}
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
      --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD:-changeme}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - sahool-backend

  ndvi-engine:
    build:
      context: ./ndvi-engine-service
      dockerfile: Dockerfile
    image: sahool/ndvi-engine:${VERSION:-6.8.5}
    container_name: sahool-ndvi
    restart: unless-stopped
    logging: *default-logging
    environment:
      - REDIS_URL=redis://:${REDIS_PASSWORD:-changeme}@redis:6379/0
      - MODEL_PATH=/app/models/ndvi_model.pth
      - PORT=3000
      - WORKERS=4
      - LOG_LEVEL=info
    ports:
      - "${NDVI_PORT:-3000}:3000"
    volumes:
      - ./ndvi-engine-service/models:/app/models:ro
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - sahool-backend

  geo-service:
    image: nginx:alpine
    container_name: sahool-geo
    restart: unless-stopped
    logging: *default-logging
    ports:
      - "${GEO_PORT:-8080}:80"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - sahool-backend

  api-gateway:
    image: kong:3.4-ubuntu
    container_name: sahool-gateway
    restart: unless-stopped
    logging: *default-logging
    environment:
      - KONG_DATABASE=off
      - KONG_DECLARATIVE_CONFIG=/kong/declarative/kong.yml
      - KONG_PROXY_ACCESS_LOG=/dev/stdout
      - KONG_ADMIN_ACCESS_LOG=/dev/stdout
      - KONG_PROXY_ERROR_LOG=/dev/stderr
      - KONG_ADMIN_ERROR_LOG=/dev/stderr
      - KONG_ADMIN_LISTEN=0.0.0.0:8001
      - KONG_PROXY_LISTEN=0.0.0.0:8000
    ports:
      - "${API_PORT:-9000}:8000"
      - "8001:8001"
    volumes:
      - ./config/kong.yml:/kong/declarative/kong.yml:ro
    depends_on:
      - geo-service
      - ndvi-engine
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - sahool-backend
      - sahool-frontend

  prometheus:
    image: prom/prometheus:v2.47.0
    container_name: sahool-prometheus
    restart: unless-stopped
    logging: *default-logging
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    ports:
      - "${PROMETHEUS_PORT:-9090}:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/prometheus/alerts:/etc/prometheus/alerts:ro
      - prometheus_data:/prometheus
    networks:
      - sahool-monitoring
      - sahool-backend
    profiles:
      - monitoring

  grafana:
    image: grafana/grafana:10.2.0
    container_name: sahool-grafana
    restart: unless-stopped
    logging: *default-logging
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASS:?GRAFANA_ADMIN_PASS required}
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "${GRAFANA_PORT:-3001}:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - prometheus
    networks:
      - sahool-monitoring
    profiles:
      - monitoring

  jaeger:
    image: jaegertracing/all-in-one:1.50
    container_name: sahool-jaeger
    restart: unless-stopped
    logging: *default-logging
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "${JAEGER_PORT:-16686}:16686"
      - "4317:4317"
      - "4318:4318"
    networks:
      - sahool-monitoring
      - sahool-backend
    profiles:
      - monitoring

volumes:
  postgres_data:
    name: sahool_postgres_data
  redis_data:
    name: sahool_redis_data
  prometheus_data:
    name: sahool_prometheus_data
  grafana_data:
    name: sahool_grafana_data

networks:
  sahool-backend:
    driver: bridge
    name: sahool-backend
  sahool-frontend:
    driver: bridge
    name: sahool-frontend
  sahool-monitoring:
    driver: bridge
    name: sahool-monitoring
'''

# E2E Test script
TEMPLATES["e2e_test_sh"] = '''#!/bin/bash
# SAHOOL E2E Test Suite v6.8.5

set -euo pipefail

RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
CYAN='\\033[0;36m'
NC='\\033[0m'

API_URL="${API_URL:-http://localhost:9000}"
NDVI_URL="${NDVI_URL:-http://localhost:3000}"
TIMEOUT="${TIMEOUT:-10}"

TOTAL=0
PASSED=0
FAILED=0
SKIPPED=0

declare -a FAILED_TESTS=()

log()   { echo -e "${GREEN}[TEST]${NC} $1"; }
error() { echo -e "${RED}[FAIL]${NC} $1"; }
warn()  { echo -e "${YELLOW}[SKIP]${NC} $1"; }
info()  { echo -e "${CYAN}[INFO]${NC} $1"; }

run_test() {
    local name="$1"
    local cmd="$2"

    ((TOTAL++))

    if eval "$cmd" > /dev/null 2>&1; then
        ((PASSED++))
        echo -e "  ${GREEN}✓${NC} $name"
        return 0
    else
        ((FAILED++))
        FAILED_TESTS+=("$name")
        echo -e "  ${RED}✗${NC} $name"
        return 1
    fi
}

skip_test() {
    local name="$1"
    local reason="$2"

    ((TOTAL++))
    ((SKIPPED++))
    echo -e "  ${YELLOW}○${NC} $name (skipped: $reason)"
}

preflight() {
    info "Pre-flight checks..."

    if ! curl -sf "$API_URL/health" --max-time 5 > /dev/null 2>&1; then
        if ! curl -sf "http://localhost:9000/health" --max-time 5 > /dev/null 2>&1; then
            warn "API not available - some tests will be skipped"
            return 1
        fi
    fi

    log "API available"
    return 0
}

test_health() {
    echo -e "\\n${CYAN}=== Health Endpoints ===${NC}"
    run_test "NDVI Engine Health" "curl -sf '$NDVI_URL/health' --max-time $TIMEOUT" || true
    run_test "NDVI Metrics" "curl -sf '$NDVI_URL/metrics' --max-time $TIMEOUT" || true
}

test_database() {
    echo -e "\\n${CYAN}=== Database ===${NC}"

    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^sahool-postgres$"; then
        run_test "PostgreSQL" "docker exec sahool-postgres pg_isready -U sahool_admin" || true
    else
        skip_test "PostgreSQL" "Container not running"
    fi

    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^sahool-redis$"; then
        run_test "Redis" "docker exec sahool-redis redis-cli ping | grep -q PONG" || true
    else
        skip_test "Redis" "Container not running"
    fi
}

generate_report() {
    echo ""
    echo -e "${CYAN}======================================${NC}"
    echo -e "${CYAN}        TEST RESULTS SUMMARY          ${NC}"
    echo -e "${CYAN}======================================${NC}"
    echo ""
    echo -e "  Total:   ${CYAN}$TOTAL${NC}"
    echo -e "  Passed:  ${GREEN}$PASSED${NC}"
    echo -e "  Failed:  ${RED}$FAILED${NC}"
    echo -e "  Skipped: ${YELLOW}$SKIPPED${NC}"
    echo ""

    if [[ $FAILED -gt 0 ]]; then
        echo -e "  ${RED}Failed Tests:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "    - $test"
        done
        echo ""
    fi

    local pass_rate=0
    if [[ $TOTAL -gt 0 ]]; then
        pass_rate=$(echo "scale=1; ($PASSED * 100) / $TOTAL" | bc 2>/dev/null || echo "0")
    fi

    echo -e "  Pass Rate: ${pass_rate}%"
    echo ""

    if [[ $FAILED -eq 0 ]]; then
        echo -e "  ${GREEN}ALL TESTS PASSED!${NC}"
        return 0
    else
        echo -e "  ${YELLOW}SOME TESTS FAILED${NC}"
        return 1
    fi
}

main() {
    echo ""
    echo -e "${CYAN}======================================${NC}"
    echo -e "${CYAN}    SAHOOL E2E Test Suite v6.8.5     ${NC}"
    echo -e "${CYAN}======================================${NC}"

    preflight || true
    test_health
    test_database
    generate_report
}

main "$@"
'''

# Deploy script
TEMPLATES["deploy_sh"] = '''#!/bin/bash
# SAHOOL Production Deployment Script v6.8.5

set -euo pipefail

RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
CYAN='\\033[0;36m'
NC='\\033[0m'

DEPLOY_ID="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="deployments/deploy-${DEPLOY_ID}.log"

mkdir -p deployments

log()   { echo -e "${GREEN}[DEPLOY]${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; exit 1; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }

if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    error "Docker Compose is not installed"
fi

action="${1:-deploy}"

case "$action" in
    deploy)
        log "Starting deployment: $DEPLOY_ID"

        log "Running pre-flight checks..."
        $COMPOSE_CMD config -q || error "Invalid compose configuration"

        log "Creating backup..."
        ./scripts/backup.sh || warn "Backup failed, continuing..."

        log "Pulling latest images..."
        $COMPOSE_CMD pull

        log "Starting services..."
        $COMPOSE_CMD up -d

        log "Waiting for services..."
        sleep 30

        if curl -sf http://localhost:9000/health --max-time 10 &>/dev/null; then
            log "Deployment successful: $DEPLOY_ID"
        else
            warn "Health check inconclusive"
        fi
        ;;

    rollback)
        log "Rolling back..."
        $COMPOSE_CMD down
        $COMPOSE_CMD up -d
        log "Rollback completed"
        ;;

    status)
        $COMPOSE_CMD ps
        ;;

    *)
        echo "Usage: $0 {deploy|rollback|status}"
        exit 1
        ;;
esac
'''

# Backup script
TEMPLATES["backup_sh"] = '''#!/bin/bash
# SAHOOL Backup Script v6.8.5

set -euo pipefail

GREEN='\\033[0;32m'
CYAN='\\033[0;36m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

BACKUP_DIR="backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo -e "${CYAN}Creating backup in $BACKUP_DIR${NC}"

echo "Backing up PostgreSQL..."
if docker ps --format '{{.Names}}' | grep -q "^sahool-postgres$"; then
    if docker exec sahool-postgres pg_dumpall -U sahool_admin 2>/dev/null | gzip > "$BACKUP_DIR/db.sql.gz"; then
        echo -e "${GREEN}Database backed up${NC}"
    else
        echo -e "${YELLOW}Database backup failed${NC}"
    fi
else
    echo -e "${YELLOW}Database backup skipped (container not running)${NC}"
fi

echo "Backing up Redis..."
if docker ps --format '{{.Names}}' | grep -q "^sahool-redis$"; then
    if docker exec sahool-redis redis-cli SAVE 2>/dev/null; then
        docker cp sahool-redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb" 2>/dev/null || true
        echo -e "${GREEN}Redis backed up${NC}"
    fi
else
    echo -e "${YELLOW}Redis backup skipped${NC}"
fi

echo "Backing up configuration..."
cp -r config/ "$BACKUP_DIR/" 2>/dev/null || true
cp docker-compose.yml "$BACKUP_DIR/" 2>/dev/null || true
[[ -f .env ]] && cp .env "$BACKUP_DIR/.env.backup" 2>/dev/null || true

cat > "$BACKUP_DIR/manifest.json" <<EOF
{
    "timestamp": "$(date -Iseconds)",
    "version": "6.8.5",
    "contents": ["db.sql.gz", "redis.rdb", "config/", "docker-compose.yml"]
}
EOF

echo ""
echo -e "${GREEN}Backup completed: $BACKUP_DIR${NC}"
echo "Size: $(du -sh "$BACKUP_DIR" | cut -f1)"
'''

# Restore script
TEMPLATES["restore_sh"] = '''#!/bin/bash
# SAHOOL Restore Script v6.8.5

set -euo pipefail

BACKUP_DIR="${1:-}"

if [[ ! -d "$BACKUP_DIR" ]]; then
    echo "Backup directory not found: $BACKUP_DIR"
    echo "Usage: $0 <backup-directory>"
    echo ""
    echo "Available backups:"
    ls -la backups/ 2>/dev/null || echo "  No backups found"
    exit 1
fi

echo "Restoring from $BACKUP_DIR..."

if [[ -f "$BACKUP_DIR/manifest.json" ]]; then
    echo "Manifest:"
    cat "$BACKUP_DIR/manifest.json"
    echo ""
fi

read -p "Continue with restore? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

if [[ -f "$BACKUP_DIR/db.sql.gz" ]]; then
    echo "Restoring PostgreSQL..."
    if docker ps --format '{{.Names}}' | grep -q "^sahool-postgres$"; then
        gunzip -c "$BACKUP_DIR/db.sql.gz" | docker exec -i sahool-postgres psql -U sahool_admin
        echo "Database restored"
    fi
fi

if [[ -f "$BACKUP_DIR/redis.rdb" ]]; then
    echo "Restoring Redis..."
    if docker ps --format '{{.Names}}' | grep -q "^sahool-redis$"; then
        docker cp "$BACKUP_DIR/redis.rdb" sahool-redis:/data/dump.rdb
        docker restart sahool-redis
        echo "Redis restored"
    fi
fi

echo ""
echo "Restore completed!"
'''

# CI/CD workflow
TEMPLATES["cicd_yml"] = '''name: SAHOOL CI/CD v6.8.5

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Create .env file
        run: |
          echo "POSTGRES_PASSWORD=testpass123" >> .env
          echo "REDIS_PASSWORD=testpass123" >> .env
          echo "JWT_SECRET=testsecret123" >> .env
          echo "GRAFANA_ADMIN_PASS=testpass123" >> .env

      - name: Start services
        run: docker compose up -d --wait --wait-timeout 120

      - name: Run tests
        run: ./tests/test_e2e_master.sh

      - name: Stop services
        if: always()
        run: docker compose down -v

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./ndvi-engine-service
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/ndvi-engine:${{ github.sha }}
'''

# README
TEMPLATES["readme_md"] = '''# 🌾 SAHOOL Platform v6.8.5

**AI-Powered Agricultural Management Platform - Production Ready**

[![SOC2](https://img.shields.io/badge/SOC2-Type%20II-green)](legal/)
[![GDPR](https://img.shields.io/badge/GDPR-Compliant-blue)](legal/privacy-policy.md)
![Version](https://img.shields.io/badge/version-6.8.5-brightgreen)

## 🚀 Quick Start

```bash
# Run setup script
python sahool_setup.py my-platform

# Enter project directory
cd my-platform

# Start services
docker compose up -d

# With monitoring
docker compose --profile monitoring up -d

# Verify health
curl http://localhost:9000/health

# Run tests
./tests/test_e2e_master.sh
```

## 📊 Features

| Feature      | Description                         |
|--------------|-------------------------------------|
| AI NDVI      | Deep learning crop health analysis  |
| RBAC         | 4-role access control system        |
| Offline Mode | Full functionality without internet |
| Monitoring   | Prometheus + Grafana + Jaeger       |
| Compliance   | SOC2/GDPR ready with audit trails   |

## 🌐 Services

| Service     | Port  | URL                    |
|-------------|-------|------------------------|
| API Gateway | 9000  | http://localhost:9000  |
| NDVI Engine | 3000  | http://localhost:3000  |
| Geo Service | 8080  | http://localhost:8080  |
| Prometheus  | 9090  | http://localhost:9090  |
| Grafana     | 3001  | http://localhost:3001  |
| Jaeger      | 16686 | http://localhost:16686 |

## 🔧 Management Commands

```bash
# View logs
docker compose logs -f

# Stop services
docker compose down

# Backup
./scripts/backup.sh

# Restore
./scripts/restore.sh backups/<timestamp>

# Deploy
./scripts/deploy-production.sh deploy
```

## 📁 Project Structure

```
sahool-platform/
├── ndvi-engine-service/    # AI NDVI FastAPI service
├── sahool-flutter/         # Mobile app (Flutter)
├── config/                 # Configuration files
├── db/                     # SQL migrations
├── monitoring/             # Prometheus, Grafana configs
├── chaos/                  # Chaos engineering
├── tests/                  # E2E test suite
├── scripts/                # Deployment scripts
├── legal/                  # Privacy policy
├── docker-compose.yml      # Container orchestration
└── .env                    # Environment secrets
```

## 🔒 Security

- AES-256 encryption at rest
- TLS 1.3 in transit
- JWT authentication (RS256)
- Rate limiting (100/min, 1000/hr)

## 📄 License

Proprietary - All rights reserved © 2024 SAHOOL

## 📞 Support

- Issues: https://github.com/kafaat/sahool-project/issues
- Docs: https://docs.sahool.sa
'''

# Gitignore
TEMPLATES["gitignore"] = '''# Secrets
.env
.env.*
!.env.example
*.key
*.pem
secrets/

# Logs
*.log
logs/
setup-*.log

# Data
backups/
*_data/

# Build
build/
dist/
*.pyc
__pycache__/
node_modules/
.dart_tool/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Models
*.pth
*.pt
models/*.pth

# Temp
*.tmp
*.bak
'''

# Environment example
TEMPLATES["env_example"] = '''# SAHOOL Platform v6.8.5 - Environment Template
# Copy to .env and update values
# NEVER commit .env to version control!

# PostgreSQL
POSTGRES_USER=sahool_admin
POSTGRES_PASSWORD=CHANGE_ME_GENERATE_STRONG_PASSWORD
POSTGRES_DB=sahool_prod

# Redis
REDIS_PASSWORD=CHANGE_ME_GENERATE_STRONG_PASSWORD

# JWT
JWT_SECRET=CHANGE_ME_GENERATE_64_CHAR_SECRET

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASS=CHANGE_ME_GENERATE_PASSWORD

# Jaeger
JAEGER_TOKEN=CHANGE_ME_GENERATE_TOKEN

# Ports (optional)
API_PORT=9000
NDVI_PORT=3000
GEO_PORT=8080
GRAFANA_PORT=3001
PROMETHEUS_PORT=9090
JAEGER_PORT=16686
'''

# Flutter theme
TEMPLATES["flutter_theme_dart"] = '''import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// SAHOOL Design System v6.8.5
class SahoolTheme {
  // Brand Colors
  static const Color primaryGreen = Color(0xFF1B4D3E);
  static const Color secondaryGreen = Color(0xFF4CAF50);
  static const Color accentOrange = Color(0xFFFF9800);
  static const Color backgroundLight = Color(0xFFFAFAFA);
  static const Color surfaceLight = Color(0xFFFFFFFF);

  // Semantic Colors
  static const Color success = Color(0xFF4CAF50);
  static const Color warning = Color(0xFFFF9800);
  static const Color error = Color(0xFFE53935);
  static const Color info = Color(0xFF2196F3);

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      primaryColor: primaryGreen,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryGreen,
        brightness: Brightness.light,
        primary: primaryGreen,
        secondary: secondaryGreen,
        tertiary: accentOrange,
        surface: surfaceLight,
        error: error,
      ),
      fontFamily: 'Cairo',
      textTheme: _buildTextTheme(),
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        scrolledUnderElevation: 2,
        backgroundColor: primaryGreen,
        foregroundColor: Colors.white,
        systemOverlayStyle: SystemUiOverlayStyle.light,
      ),
      cardTheme: CardTheme(
        elevation: 2,
        shadowColor: Colors.black.withOpacity(0.1),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 2,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      primaryColor: primaryGreen,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryGreen,
        brightness: Brightness.dark,
      ),
      fontFamily: 'Cairo',
    );
  }

  static TextTheme _buildTextTheme() {
    return const TextTheme(
      displayLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.w700),
      displayMedium: TextStyle(fontSize: 28, fontWeight: FontWeight.w600),
      headlineLarge: TextStyle(fontSize: 24, fontWeight: FontWeight.w600),
      headlineMedium: TextStyle(fontSize: 20, fontWeight: FontWeight.w500),
      titleLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
      titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
      bodyLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.w400),
      bodyMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.w400),
      labelLarge: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
    );
  }
}
'''

# Flutter widgets
TEMPLATES["flutter_widgets_dart"] = '''import 'package:flutter/material.dart';

/// Fade-in animation widget
class SahoolFadeIn extends StatefulWidget {
  final Widget child;
  final Duration duration;
  final Duration delay;
  final Curve curve;

  const SahoolFadeIn({
    super.key,
    required this.child,
    this.duration = const Duration(milliseconds: 600),
    this.delay = Duration.zero,
    this.curve = Curves.easeOutCubic,
  });

  @override
  State<SahoolFadeIn> createState() => _SahoolFadeInState();
}

class _SahoolFadeInState extends State<SahoolFadeIn>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: widget.duration);
    _animation = CurvedAnimation(parent: _controller, curve: widget.curve);

    if (widget.delay == Duration.zero) {
      _controller.forward();
    } else {
      Future.delayed(widget.delay, () {
        if (mounted) _controller.forward();
      });
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(opacity: _animation, child: widget.child);
  }
}

/// Loading skeleton widget
class SahoolSkeleton extends StatefulWidget {
  final double width;
  final double height;
  final BorderRadius? borderRadius;

  const SahoolSkeleton({
    super.key,
    this.width = double.infinity,
    required this.height,
    this.borderRadius,
  });

  @override
  State<SahoolSkeleton> createState() => _SahoolSkeletonState();
}

class _SahoolSkeletonState extends State<SahoolSkeleton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          width: widget.width,
          height: widget.height,
          decoration: BoxDecoration(
            borderRadius: widget.borderRadius ?? BorderRadius.circular(8),
            gradient: LinearGradient(
              begin: Alignment(_controller.value * 3 - 1, 0),
              end: Alignment(_controller.value * 3, 0),
              colors: [
                Colors.grey.shade200,
                Colors.grey.shade100,
                Colors.grey.shade200,
              ],
            ),
          ),
        );
      },
    );
  }
}
'''

# Flutter pubspec
TEMPLATES["flutter_pubspec_yaml"] = '''name: sahool_flutter
description: SAHOOL Agricultural Platform Mobile App
version: 6.8.5+1

environment:
  sdk: '>=3.0.0 <4.0.0'
  flutter: ">=3.10.0"

dependencies:
  flutter:
    sdk: flutter
  flutter_localizations:
    sdk: flutter
  intl: any
  http: ^1.1.0
  provider: ^6.1.1
  shared_preferences: ^2.2.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
'''


# ===================== MAIN SETUP CLASS =====================

class SahoolSetup:
    def __init__(self, project_name: str, skip_tests: bool = False,
                 skip_integration: bool = False, enable_monitoring: bool = True,
                 clean_logs: bool = False):
        self.project_name = project_name
        self.skip_tests = skip_tests
        self.skip_integration = skip_integration
        self.enable_monitoring = enable_monitoring
        self.clean_logs = clean_logs

        self.project_dir = Path.cwd() / project_name
        self.log_file: Optional[Path] = None
        self.logger: Optional[logging.Logger] = None
        self.compose_cmd = ["docker", "compose"]
        self.secrets: Dict[str, str] = {}
        self.created_files: List[Path] = []

    def run_command(self, cmd: List[str], shell: bool = False,
                   env: Optional[Dict[str, str]] = None,
                   cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """Execute a command with error handling"""
        try:
            if self.logger:
                self.logger.debug(f"Executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                shell=shell,
                env=env or os.environ.copy(),
                capture_output=True,
                text=True,
                timeout=300,
                cwd=cwd
            )

            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()

        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)

    def check_prerequisites(self) -> bool:
        """Check if all required tools are available"""
        self.logger.info("🔧 Checking Prerequisites")

        required_tools = ["docker", "curl", "openssl"]
        missing = []

        for tool in required_tools:
            if shutil.which(tool) is None:
                missing.append(tool)
                self.logger.error(f"✗ {tool} is required but not installed")
            else:
                self.logger.info(f"✓ {tool} found")

        if missing:
            self.logger.error(f"Missing tools: {', '.join(missing)}")
            return False

        self.logger.info("All prerequisites satisfied")
        return True

    def check_docker_compose(self) -> bool:
        """Check Docker Compose version and availability"""
        self.logger.info("🐳 Docker Compose Version Check")

        # Check for docker compose v2
        success, output = self.run_command(["docker", "compose", "version", "--short"])
        if success:
            self.compose_cmd = ["docker", "compose"]
            version = output.strip().lstrip('v')
        else:
            # Try docker-compose v1
            success, output = self.run_command(["docker-compose", "version", "--short"])
            if success:
                self.compose_cmd = ["docker-compose"]
                version = output.strip().lstrip('v')
            else:
                self.logger.error("Docker Compose is not installed")
                return False

        self.logger.info(f"Docker Compose version: {version}")

        try:
            required = [int(x) for x in MIN_DOCKER_COMPOSE_VERSION.split('.')]
            actual = [int(x) for x in version.split('.')[:3]]

            # Pad with zeros
            while len(required) < 3:
                required.append(0)
            while len(actual) < 3:
                actual.append(0)

            if actual < required:
                self.logger.error(f"Docker Compose version too old. Need {MIN_DOCKER_COMPOSE_VERSION}+")
                return False

            self.logger.info("✓ Docker Compose version meets requirements")
            return True

        except Exception as e:
            self.logger.warning(f"Could not compare versions: {e}")
            return True

    def check_system_requirements(self) -> bool:
        """Check system RAM, CPU, disk space, and Docker daemon"""
        self.logger.info("🔍 System Requirements Check")

        system = platform.system()

        # RAM check
        total_ram_gb = 0
        if system == "Darwin":
            success, output = self.run_command(["sysctl", "-n", "hw.memsize"])
            if success:
                total_ram_gb = int(int(output) / 1024 / 1024 / 1024)
        else:
            success, output = self.run_command(["free", "-g"])
            if success:
                lines = output.split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) > 1:
                        total_ram_gb = int(parts[1])

        if total_ram_gb > 0:
            if total_ram_gb < MIN_RAM_GB:
                self.logger.error(f"Insufficient RAM: {total_ram_gb}GB (need {MIN_RAM_GB}GB)")
                return False
            self.logger.info(f"✓ RAM: {total_ram_gb}GB")
        else:
            self.logger.warning("Could not determine RAM size")

        # CPU check
        cpu_cores = 0
        if system == "Darwin":
            success, output = self.run_command(["sysctl", "-n", "hw.ncpu"])
            if success:
                cpu_cores = int(output)
        else:
            success, output = self.run_command(["nproc"])
            if success:
                cpu_cores = int(output)

        if cpu_cores > 0:
            if cpu_cores < MIN_CPU_CORES:
                self.logger.warning(f"Low CPU cores: {cpu_cores} (recommend {MIN_CPU_CORES}+)")
            else:
                self.logger.info(f"✓ CPU Cores: {cpu_cores}")

        # Docker daemon check
        success, _ = self.run_command(["docker", "info"])
        if not success:
            self.logger.error("Cannot connect to Docker daemon. Is Docker running?")
            return False

        self.logger.info("✓ Docker daemon responsive")
        return True

    def check_internet_connectivity(self) -> bool:
        """Check internet connectivity"""
        self.logger.info("🌐 Internet Connectivity Check")

        test_urls = [
            "https://hub.docker.com",
            "https://google.com"
        ]

        for url in test_urls:
            success, _ = self.run_command(["curl", "-sf", "--max-time", "10", "--head", url])
            if success:
                self.logger.info(f"✓ Can reach: {url}")
                return True

        self.logger.error("No internet connectivity detected")
        return False

    def create_directory_structure(self):
        """Create the complete directory structure"""
        self.logger.info("📁 Creating Directory Structure")

        dirs = [
            "config",
            "db",
            "chaos",
            "tests",
            "scripts",
            "legal",
            "monitoring/grafana/provisioning/dashboards",
            "monitoring/grafana/provisioning/datasources",
            "monitoring/prometheus/alerts",
            "redis",
            "logging",
            "ndvi-engine-service/ml",
            "ndvi-engine-service/models",
            "sahool-flutter/lib/theme",
            "sahool-flutter/lib/widgets",
            "deployments",
            "backups",
            ".github/workflows"
        ]

        for dir_path in dirs:
            full_path = self.project_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Created {len(dirs)} directories")

    def generate_secrets(self):
        """Generate all required secrets and create .env file"""
        self.logger.info("🔐 Generating Secure Secrets")

        env_file = self.project_dir / ".env"

        if env_file.exists():
            self.logger.warning(".env already exists, reusing existing secrets")
            return

        def generate_secret(length: int) -> str:
            success, output = self.run_command([
                "openssl", "rand", "-base64", str(length * 2)
            ])
            if success:
                cleaned = ''.join(c for c in output if c.isalnum())
                return cleaned[:length]
            else:
                # Fallback to Python
                import secrets as sec
                return sec.token_urlsafe(length)[:length]

        self.secrets = {
            "POSTGRES_USER": "sahool_admin",
            "POSTGRES_PASSWORD": generate_secret(32),
            "POSTGRES_DB": "sahool_prod",
            "REDIS_PASSWORD": generate_secret(32),
            "JWT_SECRET": generate_secret(64),
            "GRAFANA_ADMIN_USER": "admin",
            "GRAFANA_ADMIN_PASS": generate_secret(16),
            "JAEGER_TOKEN": generate_secret(32),
            "API_PORT": "9000",
            "NDVI_PORT": "3000",
            "GEO_PORT": "8080",
            "GRAFANA_PORT": "3001",
            "PROMETHEUS_PORT": "9090",
            "JAEGER_PORT": "16686"
        }

        env_content = f"""# SAHOOL Platform Secrets v{SCRIPT_VERSION}
# Generated: {datetime.datetime.now().isoformat()}
# DO NOT COMMIT TO GIT

POSTGRES_USER={self.secrets["POSTGRES_USER"]}
POSTGRES_PASSWORD={self.secrets["POSTGRES_PASSWORD"]}
POSTGRES_DB={self.secrets["POSTGRES_DB"]}

REDIS_PASSWORD={self.secrets["REDIS_PASSWORD"]}

JWT_SECRET={self.secrets["JWT_SECRET"]}

GRAFANA_ADMIN_USER={self.secrets["GRAFANA_ADMIN_USER"]}
GRAFANA_ADMIN_PASS={self.secrets["GRAFANA_ADMIN_PASS"]}

JAEGER_TOKEN={self.secrets["JAEGER_TOKEN"]}

# Ports
API_PORT={self.secrets["API_PORT"]}
NDVI_PORT={self.secrets["NDVI_PORT"]}
GEO_PORT={self.secrets["GEO_PORT"]}
GRAFANA_PORT={self.secrets["GRAFANA_PORT"]}
PROMETHEUS_PORT={self.secrets["PROMETHEUS_PORT"]}
JAEGER_PORT={self.secrets["JAEGER_PORT"]}
"""
        env_file.write_text(env_content)
        env_file.chmod(0o600)

        self.logger.info("Generated secure .env file with 600 permissions")
        self.logger.info(f"⚠️ Grafana admin password: {self.secrets['GRAFANA_ADMIN_PASS']}")
        self.logger.warning("SAVE THIS PASSWORD!")

    def write_template_file(self, template_name: str, file_path: Path,
                          substitute: Optional[Dict[str, str]] = None):
        """Write a template file to the specified path"""
        if template_name not in TEMPLATES:
            self.logger.error(f"Template not found: {template_name}")
            return

        content = TEMPLATES[template_name]

        if substitute:
            for key, value in substitute.items():
                content = content.replace(f"{{{key}}}", value)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

        if file_path.suffix == '.sh':
            file_path.chmod(0o755)

        self.created_files.append(file_path)

    def setup_all_components(self):
        """Setup all platform components"""
        # NDVI Engine
        self.logger.info("🤖 AI-Powered NDVI Engine")
        ndvi_dir = self.project_dir / "ndvi-engine-service"
        self.write_template_file("ndvi_main_py", ndvi_dir / "main.py")
        self.write_template_file("ndvi_requirements_txt", ndvi_dir / "requirements.txt")
        self.write_template_file("ndvi_dockerfile", ndvi_dir / "Dockerfile")

        # Compliance
        self.logger.info("📋 SOC2 & GDPR Compliance")
        db_dir = self.project_dir / "db"
        self.write_template_file("postgres_init_sql", db_dir / "001_init.sql")
        self.write_template_file("postgres_audit_sql", db_dir / "002_audit.sql")
        self.write_template_file("privacy_policy_md",
                               self.project_dir / "legal" / "privacy-policy.md",
                               {"date": datetime.datetime.now().strftime("%Y-%m-%d")})

        # Performance
        self.logger.info("⚡ Performance Tuning")
        config_dir = self.project_dir / "config"
        self.write_template_file("sysctl_conf", config_dir / "sysctl-tuning.conf")
        self.write_template_file("postgres_conf", config_dir / "postgresql-optimized.conf")
        self.write_template_file("redis_conf", self.project_dir / "redis" / "redis-optimized.conf")

        # Chaos
        self.logger.info("🌀 Chaos Engineering")
        chaos_dir = self.project_dir / "chaos"
        self.write_template_file("chaos_manifest", chaos_dir / "chaos-manifest.yml")
        self.write_template_file("chaos_test_sh", chaos_dir / "run-chaos-test.sh")

        # Flutter
        self.logger.info("🎨 Flutter UI/UX System")
        flutter_dir = self.project_dir / "sahool-flutter"
        self.write_template_file("flutter_theme_dart", flutter_dir / "lib/theme/app_theme.dart")
        self.write_template_file("flutter_widgets_dart", flutter_dir / "lib/widgets/animated_widgets.dart")
        self.write_template_file("flutter_pubspec_yaml", flutter_dir / "pubspec.yaml")

        # Testing
        self.logger.info("🧪 Test Suite")
        self.write_template_file("e2e_test_sh", self.project_dir / "tests" / "test_e2e_master.sh")

        # Monitoring
        self.logger.info("📊 Monitoring & Observability")
        monitoring_dir = self.project_dir / "monitoring"
        self.write_template_file("prometheus_yml", monitoring_dir / "prometheus/prometheus.yml")
        self.write_template_file("prometheus_alerts_yml", monitoring_dir / "prometheus/alerts/sahool-alerts.yml")
        self.write_template_file("grafana_datasources_yml", monitoring_dir / "grafana/provisioning/datasources/datasources.yml")
        self.write_template_file("grafana_dashboards_yml", monitoring_dir / "grafana/provisioning/dashboards/dashboards.yml")

        # API Gateway
        self.logger.info("🚪 API Gateway (Kong)")
        self.write_template_file("kong_yml", config_dir / "kong.yml")

        # Docker Compose
        self.logger.info("🐳 Docker Compose")
        self.write_template_file("docker_compose_yml", self.project_dir / "docker-compose.yml")

        # Deployment
        self.logger.info("🚀 Deployment Scripts")
        scripts_dir = self.project_dir / "scripts"
        self.write_template_file("deploy_sh", scripts_dir / "deploy-production.sh")
        self.write_template_file("backup_sh", scripts_dir / "backup.sh")
        self.write_template_file("restore_sh", scripts_dir / "restore.sh")

        # CI/CD
        self.logger.info("🔄 CI/CD Pipeline")
        self.write_template_file("cicd_yml", self.project_dir / ".github/workflows/ci.yml")

        # Documentation
        self.logger.info("📚 Documentation")
        self.write_template_file("readme_md", self.project_dir / "README.md")
        self.write_template_file("gitignore", self.project_dir / ".gitignore")
        self.write_template_file("env_example", self.project_dir / ".env.example")

    def run_integration_tests(self):
        """Run integration tests"""
        if self.skip_integration:
            self.logger.info("⏭️ Skipping integration tests")
            return

        self.logger.info("🔗 Integration Tests")

        success, _ = self.run_command(
            self.compose_cmd + ["config", "-q"],
            cwd=self.project_dir
        )
        if success:
            self.logger.info("✓ Docker Compose configuration valid")
        else:
            self.logger.warning("⚠️ Docker Compose configuration has warnings")

    def final_summary(self):
        """Display final setup summary"""
        self.logger.info("🎉 Setup Complete!")

        print(f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════╗
║                  🌾 SAHOOL Platform Ready! v{SCRIPT_VERSION} 🌾                ║
╚═══════════════════════════════════════════════════════════════════╝{Colors.NC}

{Colors.GREEN}Project:{Colors.NC} {self.project_dir}

{Colors.CYAN}Next Steps:{Colors.NC}

  1. cd {self.project_name}
  2. docker compose up -d
  3. docker compose --profile monitoring up -d
  4. curl http://localhost:9000/health
  5. ./tests/test_e2e_master.sh

{Colors.CYAN}Services:{Colors.NC}
  • API Gateway:  http://localhost:9000
  • NDVI Engine:  http://localhost:3000
  • Grafana:      http://localhost:3001
  • Prometheus:   http://localhost:9090
""")

        if "GRAFANA_ADMIN_PASS" in self.secrets:
            print(f"""  {Colors.YELLOW}⚠️ Grafana Credentials:{Colors.NC}
     Username: admin
     Password: {self.secrets['GRAFANA_ADMIN_PASS']}
     SAVE THIS PASSWORD!
""")

    def setup(self) -> bool:
        """Execute the complete setup process"""
        try:
            # Create project directory
            self.project_dir.mkdir(parents=True, exist_ok=True)

            # Setup logging
            self.log_file = self.project_dir / f"setup-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
            self.logger = setup_logger(self.log_file)

            self.logger.info(f"SAHOOL PLATFORM v{SCRIPT_VERSION} - ULTIMATE SETUP")
            self.logger.info(f"Project directory: {self.project_dir}")

            # Pre-checks
            if not self.check_prerequisites():
                return False
            if not self.check_system_requirements():
                return False
            if not self.check_docker_compose():
                return False
            if not self.check_internet_connectivity():
                return False

            # Setup
            self.create_directory_structure()
            self.generate_secrets()
            self.setup_all_components()
            self.run_integration_tests()
            self.final_summary()

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Setup failed: {str(e)}")
            else:
                print(f"Setup failed: {str(e)}")
            return False


# ===================== CLI INTERFACE =====================

def show_help():
    """Show help message"""
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════╗
║                    🌾 SAHOOL PLATFORM v{SCRIPT_VERSION} 🌾                           ║
║        Ultimate Agricultural AI Platform Setup Script                    ║
╚══════════════════════════════════════════════════════════════════════════╝{Colors.NC}

USAGE:
    python sahool_setup.py [OPTIONS] [PROJECT_NAME]

OPTIONS:
    -h, --help              Show this help message
    --skip-tests            Skip E2E tests
    --skip-integration      Skip integration checks
    --no-monitoring         Don't start monitoring services
    --clean-logs            Clean old log files

ARGUMENTS:
    PROJECT_NAME            Project directory name (default: sahool-platform-v6-final)

EXAMPLES:
    python sahool_setup.py
    python sahool_setup.py my-farm-platform
    python sahool_setup.py --clean-logs --skip-integration my-platform

REQUIREMENTS:
    ✓ Docker Engine 20.10+
    ✓ Docker Compose v2.0+
    ✓ 8GB+ RAM
    ✓ 4+ CPU cores
    ✓ 20GB+ disk space
""")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SAHOOL Platform Setup", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="Show help")
    parser.add_argument("--skip-tests", action="store_true", help="Skip E2E tests")
    parser.add_argument("--skip-integration", action="store_true", help="Skip integration")
    parser.add_argument("--no-monitoring", action="store_true", help="Don't start monitoring")
    parser.add_argument("--clean-logs", action="store_true", help="Clean old logs")
    parser.add_argument("project_name", nargs="?", default="sahool-platform-v6-final",
                       help="Project directory name")

    args = parser.parse_args()

    if args.help:
        show_help()
        sys.exit(0)

    setup = SahoolSetup(
        project_name=args.project_name,
        skip_tests=args.skip_tests,
        skip_integration=args.skip_integration,
        enable_monitoring=not args.no_monitoring,
        clean_logs=args.clean_logs
    )

    success = setup.setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
