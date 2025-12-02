#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Part 5: Backend API Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

log_info "إنشاء نقاط نهاية API..."

# ─────────────────────────────────────────────────────────────────────────────
# Fields API
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/api/v1/endpoints/fields.py" << 'EOF'
"""
Fields API Endpoints
نقاط نهاية الحقول
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from app.models.user import User
from app.schemas.field import FieldCreate, FieldUpdate, FieldResponse, FieldListResponse
from app.services.field_service import FieldService
from app.api.deps import get_current_user, get_field_service

router = APIRouter(prefix="/fields", tags=["Fields"])


@router.get("", response_model=FieldListResponse)
async def list_fields(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    crop_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    field_service: FieldService = Depends(get_field_service)
):
    """
    قائمة الحقول
    List all fields for current tenant
    """
    fields, total = await field_service.get_fields(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size,
        crop_type=crop_type,
        status=status
    )

    return FieldListResponse(
        items=fields,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{field_id}", response_model=FieldResponse)
async def get_field(
    field_id: int,
    current_user: User = Depends(get_current_user),
    field_service: FieldService = Depends(get_field_service)
):
    """
    الحصول على حقل
    Get a specific field by ID
    """
    field = await field_service.get_field(field_id, current_user.tenant_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found"
        )
    return field


@router.post("", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
async def create_field(
    field_data: FieldCreate,
    current_user: User = Depends(get_current_user),
    field_service: FieldService = Depends(get_field_service)
):
    """
    إنشاء حقل جديد
    Create a new field
    """
    field = await field_service.create_field(
        field_data=field_data,
        tenant_id=current_user.tenant_id,
        owner_id=current_user.id
    )
    return field


@router.put("/{field_id}", response_model=FieldResponse)
async def update_field(
    field_id: int,
    field_data: FieldUpdate,
    current_user: User = Depends(get_current_user),
    field_service: FieldService = Depends(get_field_service)
):
    """
    تحديث حقل
    Update an existing field
    """
    field = await field_service.update_field(
        field_id=field_id,
        tenant_id=current_user.tenant_id,
        update_data=field_data
    )
    return field


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field(
    field_id: int,
    current_user: User = Depends(get_current_user),
    field_service: FieldService = Depends(get_field_service)
):
    """
    حذف حقل
    Delete a field
    """
    await field_service.delete_field(field_id, current_user.tenant_id)
EOF

# ─────────────────────────────────────────────────────────────────────────────
# NDVI API
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/api/v1/endpoints/ndvi.py" << 'EOF'
"""
NDVI API Endpoints
نقاط نهاية NDVI
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import Optional
from datetime import date

from app.models.user import User
from app.schemas.ndvi import (
    NDVIResponse, NDVITimelineResponse,
    NDVIComputeRequest, NDVIComputeResponse
)
from app.services.ndvi_service import NDVIService
from app.api.deps import get_current_user, get_ndvi_service, require_manager

router = APIRouter(prefix="/ndvi", tags=["NDVI"])


@router.get("/{field_id}", response_model=NDVIResponse)
async def get_ndvi(
    field_id: int,
    target_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    ndvi_service: NDVIService = Depends(get_ndvi_service)
):
    """
    الحصول على بيانات NDVI
    Get NDVI data for a field
    """
    if target_date:
        ndvi = await ndvi_service.get_ndvi_by_date(
            field_id, current_user.tenant_id, target_date
        )
    else:
        ndvi = await ndvi_service.get_latest_ndvi(
            field_id, current_user.tenant_id
        )

    if not ndvi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NDVI data not found"
        )

    return ndvi


@router.get("/{field_id}/timeline", response_model=NDVITimelineResponse)
async def get_ndvi_timeline(
    field_id: int,
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user),
    ndvi_service: NDVIService = Depends(get_ndvi_service)
):
    """
    الحصول على سجل NDVI
    Get NDVI timeline for a field
    """
    data = await ndvi_service.get_ndvi_timeline(
        field_id, current_user.tenant_id, start_date, end_date
    )

    return NDVITimelineResponse(
        field_id=field_id,
        start_date=start_date,
        end_date=end_date,
        data=data
    )


@router.get("/{field_id}/statistics")
async def get_ndvi_statistics(
    field_id: int,
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    ndvi_service: NDVIService = Depends(get_ndvi_service)
):
    """
    إحصائيات NDVI
    Get NDVI statistics for a field
    """
    stats = await ndvi_service.get_ndvi_statistics(
        field_id, current_user.tenant_id, days
    )
    return stats


@router.post("/compute", response_model=NDVIComputeResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_ndvi_computation(
    request: NDVIComputeRequest,
    current_user: User = Depends(require_manager()),
    ndvi_service: NDVIService = Depends(get_ndvi_service)
):
    """
    طلب حساب NDVI
    Trigger NDVI computation for fields (manager+ only)
    """
    job_id = await ndvi_service.trigger_computation(
        request, current_user.tenant_id
    )

    return NDVIComputeResponse(
        job_id=job_id,
        status="queued",
        field_count=len(request.field_ids),
        estimated_time_seconds=len(request.field_ids) * 30
    )
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Advisor API
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/api/v1/endpoints/advisor.py" << 'EOF'
"""
Advisor API Endpoints
نقاط نهاية المستشار
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List

from app.models.user import User
from app.schemas.advisor import (
    AdvisorAnalyzeRequest, AdvisorSessionResponse,
    RecommendationResponse, AlertResponse, RecommendationAction
)
from app.services.advisor_service import AdvisorService
from app.api.deps import get_current_user, get_advisor_service

router = APIRouter(prefix="/advisor", tags=["Advisor"])


@router.post("/analyze", response_model=AdvisorSessionResponse)
async def analyze_field(
    request: AdvisorAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    advisor_service: AdvisorService = Depends(get_advisor_service)
):
    """
    تحليل الحقل
    Analyze a field and generate recommendations
    """
    session = await advisor_service.analyze_field(
        request, current_user.tenant_id
    )
    return session


@router.get("/sessions/{session_id}", response_model=AdvisorSessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    advisor_service: AdvisorService = Depends(get_advisor_service)
):
    """
    الحصول على جلسة التحليل
    Get advisor session by ID
    """
    session = await advisor_service.get_session(
        session_id, current_user.tenant_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.post("/recommendations/{recommendation_id}/action", response_model=RecommendationResponse)
async def take_action_on_recommendation(
    recommendation_id: int,
    action: RecommendationAction,
    current_user: User = Depends(get_current_user),
    advisor_service: AdvisorService = Depends(get_advisor_service)
):
    """
    اتخاذ إجراء على توصية
    Take action on a recommendation
    """
    recommendation = await advisor_service.update_recommendation_status(
        recommendation_id, current_user.tenant_id, action
    )
    return recommendation


@router.get("/rules")
async def get_available_rules(
    current_user: User = Depends(get_current_user),
    advisor_service: AdvisorService = Depends(get_advisor_service)
):
    """
    قائمة القواعد المتاحة
    Get list of available advisor rules
    """
    return {"rules": [r["name"] for r in advisor_service.rules]}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Router Init
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/api/v1/__init__.py" << 'EOF'
"""API v1 Router"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, fields, ndvi, advisor

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(fields.router)
api_router.include_router(ndvi.router)
api_router.include_router(advisor.router)
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/app/main.py" << 'EOF'
"""
Field Suite Pro - Main Application
التطبيق الرئيسي
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import make_asgi_app
import time

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.database import init_db, close_db
from app.core.redis import redis_manager
from app.core.exceptions import AppException
from app.api.v1 import api_router

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await redis_manager.connect()
    await init_db()
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_db()
    await redis_manager.disconnect()
    logger.info("Application shutdown complete")


# Create application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# ─────────────────────────────────────────────────────────────────────────────
# Exception Handlers
# ─────────────────────────────────────────────────────────────────────────────
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle application exceptions"""
    logger.warning(f"AppException: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": exc.errors()
            }
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")

# Prometheus metrics
if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.ENV
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"مرحباً بك في {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }
EOF

log_success "تم إنشاء نقاط نهاية API"
