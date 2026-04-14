#!/bin/bash
# ==============================================================================
# Part 02: NDVI Service
# Microservice for NDVI processing with Celery workers
# ==============================================================================

generate_ndvi_service() {
    log_info "Creating NDVI Service..."

    local SERVICE_DIR="services/ndvi-service"
    mkdir -p "$SERVICE_DIR"/{app/{api,models,services,workers,core},tests}

    # ------------------------------------------------------------------------------
    # Service Configuration
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/core/config.py" << 'PYEOF'
"""NDVI Service Configuration"""
from functools import lru_cache
import sys
sys.path.insert(0, "/app/shared")

from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """NDVI service specific settings"""
    SERVICE_NAME: str = "ndvi-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8002

    # Satellite API
    SENTINEL_CLIENT_ID: str = ""
    SENTINEL_CLIENT_SECRET: str = ""

    # Processing
    NDVI_CACHE_TTL: int = 3600  # 1 hour
    MAX_CONCURRENT_JOBS: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
PYEOF

    # ------------------------------------------------------------------------------
    # Celery App (FIXED - Module level, not in service)
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/workers/celery_app.py" << 'PYEOF'
"""
Celery Application - Module level configuration
FIXED: Celery app should be global, not inside a service class
"""
from celery import Celery
from kombu import Queue

from ..core.config import settings

# Create Celery app at module level
celery_app = Celery(
    "ndvi_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_queues=[
        Queue("default", routing_key="default"),
        Queue("ndvi", routing_key="ndvi.#"),
        Queue("priority", routing_key="priority.#"),
    ],
    task_default_queue="default",
    task_routes={
        "app.workers.tasks.compute_ndvi": {"queue": "ndvi"},
        "app.workers.tasks.compute_ndvi_batch": {"queue": "ndvi"},
        "app.workers.tasks.priority_compute": {"queue": "priority"},
    },

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,

    # Result settings
    result_expires=86400,  # 24 hours

    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-old-results": {
            "task": "app.workers.tasks.cleanup_old_results",
            "schedule": 3600.0,  # Every hour
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.workers"])
PYEOF

    # ------------------------------------------------------------------------------
    # Celery Tasks (FIXED - Proper implementation)
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/workers/tasks.py" << 'PYEOF'
"""
NDVI Celery Tasks
Actual processing logic for NDVI computation
"""
import logging
from datetime import datetime, date
from typing import List, Optional
import asyncio

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
import numpy as np

from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.compute_ndvi",
    max_retries=3,
    soft_time_limit=300,
    time_limit=360,
)
def compute_ndvi(
    self,
    field_id: int,
    tenant_id: str,
    target_date: Optional[str] = None,
) -> dict:
    """
    Compute NDVI for a single field

    Args:
        field_id: ID of the field
        tenant_id: Tenant ID for isolation
        target_date: Target date for satellite imagery

    Returns:
        NDVI computation result
    """
    try:
        logger.info(f"Starting NDVI computation for field {field_id}")

        # Update task state
        self.update_state(
            state="PROCESSING",
            meta={"progress": 10, "message": "Fetching satellite imagery..."}
        )

        # Simulate satellite data fetch (replace with real API call)
        # In production, this would call Sentinel Hub or similar
        satellite_data = _fetch_satellite_data(field_id, target_date)

        self.update_state(
            state="PROCESSING",
            meta={"progress": 40, "message": "Processing imagery..."}
        )

        # Compute NDVI
        ndvi_result = _calculate_ndvi(satellite_data)

        self.update_state(
            state="PROCESSING",
            meta={"progress": 70, "message": "Analyzing zones..."}
        )

        # Classify zones
        zones = _classify_ndvi_zones(ndvi_result)

        self.update_state(
            state="PROCESSING",
            meta={"progress": 90, "message": "Storing results..."}
        )

        # Store result (would use async DB in real implementation)
        result = {
            "field_id": field_id,
            "tenant_id": tenant_id,
            "capture_date": target_date or datetime.utcnow().date().isoformat(),
            "mean_ndvi": float(np.mean(ndvi_result)),
            "min_ndvi": float(np.min(ndvi_result)),
            "max_ndvi": float(np.max(ndvi_result)),
            "std_ndvi": float(np.std(ndvi_result)),
            "cloud_coverage": satellite_data.get("cloud_coverage", 0),
            "zones": zones,
            "health_score": _calculate_health_score(ndvi_result),
            "computed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"NDVI computation completed for field {field_id}")
        return result

    except SoftTimeLimitExceeded:
        logger.error(f"NDVI computation timed out for field {field_id}")
        raise

    except Exception as exc:
        logger.error(f"NDVI computation failed for field {field_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    bind=True,
    name="app.workers.tasks.compute_ndvi_batch",
)
def compute_ndvi_batch(
    self,
    field_ids: List[int],
    tenant_id: str,
    target_date: Optional[str] = None,
) -> List[dict]:
    """Compute NDVI for multiple fields"""
    results = []
    total = len(field_ids)

    for idx, field_id in enumerate(field_ids):
        self.update_state(
            state="PROCESSING",
            meta={
                "progress": int((idx / total) * 100),
                "message": f"Processing field {idx + 1}/{total}",
                "current_field": field_id,
            }
        )

        # Call single field computation
        result = compute_ndvi.delay(field_id, tenant_id, target_date)
        results.append({"field_id": field_id, "task_id": result.id})

    return results


@celery_app.task(name="app.workers.tasks.cleanup_old_results")
def cleanup_old_results():
    """Periodic task to clean up old NDVI results"""
    logger.info("Running NDVI results cleanup...")
    # Implementation would delete results older than retention period
    return {"cleaned": 0, "timestamp": datetime.utcnow().isoformat()}


# ------------------------------------------------------------------------------
# Helper Functions (would be in separate module in production)
# ------------------------------------------------------------------------------

def _fetch_satellite_data(field_id: int, target_date: Optional[str]) -> dict:
    """
    Fetch satellite data for a field
    In production, this calls Sentinel Hub or similar API
    """
    # Simulated data for demo
    return {
        "nir": np.random.uniform(0.4, 0.8, (100, 100)),
        "red": np.random.uniform(0.1, 0.3, (100, 100)),
        "cloud_coverage": np.random.uniform(0, 20),
        "acquisition_date": target_date or datetime.utcnow().date().isoformat(),
    }


def _calculate_ndvi(satellite_data: dict) -> np.ndarray:
    """
    Calculate NDVI from satellite bands
    NDVI = (NIR - Red) / (NIR + Red)
    """
    nir = satellite_data["nir"]
    red = satellite_data["red"]

    # Avoid division by zero
    denominator = nir + red
    denominator[denominator == 0] = 0.0001

    ndvi = (nir - red) / denominator
    return np.clip(ndvi, -1, 1)


def _classify_ndvi_zones(ndvi: np.ndarray) -> List[dict]:
    """Classify NDVI values into health zones"""
    zones = [
        {"zone": "critical", "min": -1.0, "max": 0.2, "health": "critical"},
        {"zone": "poor", "min": 0.2, "max": 0.4, "health": "poor"},
        {"zone": "moderate", "min": 0.4, "max": 0.6, "health": "moderate"},
        {"zone": "good", "min": 0.6, "max": 0.8, "health": "good"},
        {"zone": "excellent", "min": 0.8, "max": 1.0, "health": "excellent"},
    ]

    total_pixels = ndvi.size
    result = []

    for zone in zones:
        mask = (ndvi >= zone["min"]) & (ndvi < zone["max"])
        percentage = (np.sum(mask) / total_pixels) * 100

        result.append({
            "zone": zone["zone"],
            "min_value": zone["min"],
            "max_value": zone["max"],
            "area_percentage": round(percentage, 2),
            "health_status": zone["health"],
        })

    return result


def _calculate_health_score(ndvi: np.ndarray) -> float:
    """Calculate overall health score (0-100)"""
    mean_ndvi = np.mean(ndvi)
    # Map NDVI (-1 to 1) to health score (0 to 100)
    # Assuming healthy vegetation is 0.4 to 0.8
    score = ((mean_ndvi + 1) / 2) * 100
    return round(min(100, max(0, score)), 1)
PYEOF

    write_heredoc "$SERVICE_DIR/app/workers/__init__.py" << 'PYEOF'
"""Workers module"""
from .celery_app import celery_app
from .tasks import compute_ndvi, compute_ndvi_batch, cleanup_old_results
PYEOF

    # ------------------------------------------------------------------------------
    # NDVI Model
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/models/ndvi.py" << 'PYEOF'
"""NDVI database model"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
import sys
sys.path.insert(0, "/app/shared")

from shared.utils import Base


class NDVIResult(Base):
    """NDVI computation result"""

    __tablename__ = "ndvi_results"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Capture info
    capture_date = Column(Date, nullable=False, index=True)
    cloud_coverage = Column(Float, default=0)

    # NDVI statistics
    mean_ndvi = Column(Float, nullable=False)
    min_ndvi = Column(Float, nullable=False)
    max_ndvi = Column(Float, nullable=False)
    std_ndvi = Column(Float, nullable=False)
    health_score = Column(Float, nullable=False)

    # Zone breakdown (JSONB)
    zones = Column(JSONB, default=[])

    # Processing metadata
    job_id = Column(String(100), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
PYEOF

    write_heredoc "$SERVICE_DIR/app/models/__init__.py" << 'PYEOF'
"""Models module"""
from .ndvi import NDVIResult
PYEOF

    # ------------------------------------------------------------------------------
    # NDVI Service
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/services/ndvi_service.py" << 'PYEOF'
"""NDVI Service - Business logic"""
from datetime import date, datetime
from typing import List, Optional
import uuid

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.ndvi import NDVIResult
from ..workers import compute_ndvi, compute_ndvi_batch
import sys
sys.path.insert(0, "/app/shared")
from shared.utils import get_redis


class NDVIService:
    """Service for NDVI operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = get_redis()

    async def trigger_computation(
        self,
        field_ids: List[int],
        tenant_id: str,
        target_date: Optional[date] = None,
    ) -> str:
        """Trigger NDVI computation for fields"""
        job_id = str(uuid.uuid4())
        target_date_str = target_date.isoformat() if target_date else None

        if len(field_ids) == 1:
            # Single field - direct task
            task = compute_ndvi.apply_async(
                args=[field_ids[0], tenant_id, target_date_str],
                task_id=job_id,
            )
        else:
            # Multiple fields - batch task
            task = compute_ndvi_batch.apply_async(
                args=[field_ids, tenant_id, target_date_str],
                task_id=job_id,
            )

        return job_id

    async def get_job_status(self, job_id: str) -> dict:
        """Get status of an NDVI computation job"""
        from ..workers.celery_app import celery_app

        result = celery_app.AsyncResult(job_id)

        status = {
            "job_id": job_id,
            "status": result.state,
            "progress": 0,
            "message": None,
            "result": None,
        }

        if result.state == "PROCESSING":
            info = result.info or {}
            status["progress"] = info.get("progress", 0)
            status["message"] = info.get("message")
        elif result.state == "SUCCESS":
            status["progress"] = 100
            status["result"] = result.result
        elif result.state == "FAILURE":
            status["message"] = str(result.result)

        return status

    async def get_latest(
        self,
        field_id: int,
        tenant_id: str,
    ) -> Optional[NDVIResult]:
        """Get latest NDVI result for a field"""
        # Try cache first
        cache_key = f"ndvi:latest:{tenant_id}:{field_id}"
        cached = await self.cache.get_json(cache_key)
        if cached:
            return cached

        # Query database
        result = await self.db.execute(
            select(NDVIResult)
            .where(
                NDVIResult.field_id == field_id,
                NDVIResult.tenant_id == tenant_id,
            )
            .order_by(NDVIResult.capture_date.desc())
            .limit(1)
        )
        ndvi = result.scalar_one_or_none()

        if ndvi:
            # Cache for 1 hour
            await self.cache.set_json(cache_key, ndvi.__dict__, expire=3600)

        return ndvi

    async def get_timeline(
        self,
        field_id: int,
        tenant_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30,
    ) -> List[NDVIResult]:
        """Get NDVI timeline for a field"""
        query = select(NDVIResult).where(
            NDVIResult.field_id == field_id,
            NDVIResult.tenant_id == tenant_id,
        )

        if start_date:
            query = query.where(NDVIResult.capture_date >= start_date)
        if end_date:
            query = query.where(NDVIResult.capture_date <= end_date)

        query = query.order_by(NDVIResult.capture_date.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_statistics(
        self,
        field_id: int,
        tenant_id: str,
    ) -> dict:
        """Get aggregated NDVI statistics for a field"""
        result = await self.db.execute(
            select(
                func.avg(NDVIResult.mean_ndvi).label("avg_ndvi"),
                func.min(NDVIResult.min_ndvi).label("min_ndvi"),
                func.max(NDVIResult.max_ndvi).label("max_ndvi"),
                func.avg(NDVIResult.health_score).label("avg_health"),
                func.count(NDVIResult.id).label("total_records"),
            )
            .where(
                NDVIResult.field_id == field_id,
                NDVIResult.tenant_id == tenant_id,
            )
        )

        row = result.first()
        if row:
            return {
                "avg_ndvi": float(row.avg_ndvi) if row.avg_ndvi else 0,
                "min_ndvi": float(row.min_ndvi) if row.min_ndvi else 0,
                "max_ndvi": float(row.max_ndvi) if row.max_ndvi else 0,
                "avg_health_score": float(row.avg_health) if row.avg_health else 0,
                "total_records": row.total_records,
            }
        return {}

    async def store_result(self, data: dict) -> NDVIResult:
        """Store NDVI computation result"""
        ndvi = NDVIResult(**data)
        self.db.add(ndvi)
        await self.db.flush()
        await self.db.refresh(ndvi)

        # Invalidate cache
        cache_key = f"ndvi:latest:{data['tenant_id']}:{data['field_id']}"
        await self.cache.delete(cache_key)

        return ndvi
PYEOF

    write_heredoc "$SERVICE_DIR/app/services/__init__.py" << 'PYEOF'
"""Services module"""
from .ndvi_service import NDVIService
PYEOF

    # ------------------------------------------------------------------------------
    # Dependencies
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/core/deps.py" << 'PYEOF'
"""Dependencies for NDVI Service"""
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sys
sys.path.insert(0, "/app/shared")

from shared.utils import DatabaseManager, decode_token, TokenPayload
from .config import settings

security = HTTPBearer()
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(settings.DATABASE_URL)
    return _db_manager


async def get_db() -> AsyncGenerator:
    db_manager = get_db_manager()
    async with db_manager.session() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    token = credentials.credentials
    payload = decode_token(token, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)

    if payload is None or payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return payload
PYEOF

    # ------------------------------------------------------------------------------
    # API Routes (FIXED - No duplication)
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/api/ndvi.py" << 'PYEOF'
"""NDVI API endpoints"""
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import sys
sys.path.insert(0, "/app/shared")

from shared.schemas.ndvi import (
    NDVIRequest, NDVIResponse, NDVIJobResponse, NDVITimelineResponse,
)
from shared.utils import TokenPayload

from ..core.deps import get_db, get_current_user
from ..services.ndvi_service import NDVIService

router = APIRouter(prefix="/ndvi", tags=["ndvi"])


@router.post("/compute", response_model=NDVIJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_ndvi_computation(
    request: NDVIRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Trigger NDVI computation for fields"""
    service = NDVIService(db)

    job_id = await service.trigger_computation(
        field_ids=request.field_ids,
        tenant_id=current_user.tenant_id,
        target_date=request.target_date,
    )

    return NDVIJobResponse(
        job_id=job_id,
        status="queued",
        message="NDVI computation started",
    )


@router.get("/job/{job_id}", response_model=NDVIJobResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get NDVI computation job status"""
    service = NDVIService(db)
    return await service.get_job_status(job_id)


@router.get("/field/{field_id}/latest", response_model=NDVIResponse)
async def get_latest_ndvi(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get latest NDVI result for a field"""
    service = NDVIService(db)

    result = await service.get_latest(field_id, current_user.tenant_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No NDVI data found for this field",
        )

    return result


@router.get("/field/{field_id}/timeline", response_model=NDVITimelineResponse)
async def get_ndvi_timeline(
    field_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get NDVI timeline for a field"""
    service = NDVIService(db)

    results = await service.get_timeline(
        field_id=field_id,
        tenant_id=current_user.tenant_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    # Determine trend
    if len(results) >= 2:
        recent = results[0].health_score
        older = results[-1].health_score
        if recent > older + 5:
            trend = "improving"
        elif recent < older - 5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    avg_health = sum(r.health_score for r in results) / len(results) if results else 0

    return {
        "field_id": field_id,
        "results": results,
        "trend": trend,
        "average_health_score": round(avg_health, 1),
    }


@router.get("/field/{field_id}/statistics")
async def get_ndvi_statistics(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get aggregated NDVI statistics for a field"""
    service = NDVIService(db)
    return await service.get_statistics(field_id, current_user.tenant_id)
PYEOF

    write_heredoc "$SERVICE_DIR/app/api/__init__.py" << 'PYEOF'
"""API module"""
from .ndvi import router as ndvi_router
PYEOF

    # ------------------------------------------------------------------------------
    # Main Application
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/main.py" << 'PYEOF'
"""NDVI Service - Main Application"""
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .core.config import settings
from .core.deps import get_db_manager
from .api import ndvi_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_manager = get_db_manager()
    await db_manager.create_tables()
    yield
    await db_manager.close()


app = FastAPI(
    title="NDVI Service",
    description="Vegetation Health Analysis Service",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


app.include_router(ndvi_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
PYEOF

    # ------------------------------------------------------------------------------
    # Dockerfile & Requirements
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/Dockerfile" << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../shared /app/shared
COPY . .

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
DOCKERFILE

    write_heredoc "$SERVICE_DIR/Dockerfile.worker" << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../shared /app/shared
COPY . .

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["celery", "-A", "app.workers.celery_app", "worker", "--loglevel=info", "-Q", "ndvi,default"]
DOCKERFILE

    write_heredoc "$SERVICE_DIR/requirements.txt" << 'REQEOF'
# FastAPI
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Database
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0

# Celery
celery==5.3.6
redis==5.0.1

# Auth
python-jose[cryptography]==3.3.0

# Processing
numpy==1.26.3

# HTTP
httpx==0.26.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
REQEOF

    log_success "NDVI Service created"
}
