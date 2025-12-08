"""
Imagery Service - خدمة الصور الفضائية
Sahool Yemen Platform v9.0.0

Handles satellite imagery acquisition and processing.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import List, Optional

sys.path.insert(0, "/app/libs-shared")

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

try:
    from sahool_shared.utils import setup_logging, get_logger  # noqa: E402
except ImportError:
    import logging

    def setup_logging(service_name: str):
        pass

    def get_logger(name: str):
        return logging.getLogger(name)

logger = get_logger(__name__)


# ============================================================
# Models
# ============================================================

class BoundingBox(BaseModel):
    """Bounding box for imagery search."""
    min_lat: float
    min_lng: float
    max_lat: float
    max_lng: float


class ImageryRequest(BaseModel):
    """Imagery search/download request."""
    field_id: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    start_date: str
    end_date: str
    max_cloud_cover: float = Field(default=20.0, ge=0, le=100)
    satellite: str = Field(default="sentinel-2", description="Satellite: sentinel-2, landsat-8")


class ImageryMetadata(BaseModel):
    """Imagery metadata."""
    id: str
    satellite: str
    acquisition_date: str
    cloud_cover: float
    resolution_meters: float
    bands: List[str]
    thumbnail_url: Optional[str] = None
    download_url: Optional[str] = None


class ImagerySearchResponse(BaseModel):
    """Imagery search response."""
    success: bool
    images: List[ImageryMetadata]
    total: int


class ProcessingJob(BaseModel):
    """Imagery processing job."""
    job_id: str
    status: str = Field(..., description="Status: pending, processing, completed, failed")
    progress: float = Field(default=0, ge=0, le=100)
    result_url: Optional[str] = None
    error_message: Optional[str] = None


# ============================================================
# Application Setup
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging(service_name="imagery-service")
    logger.info("imagery_service_starting", version="9.0.0")
    yield
    logger.info("imagery_service_stopping")


app = FastAPI(
    title="Sahool Imagery Service",
    description="خدمة الصور الفضائية - Satellite Imagery Service",
    version="9.0.0",
    lifespan=lifespan,
)

# CORS Configuration
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=bool(CORS_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
async def health_check():
    """Service health check."""
    return {"status": "healthy", "service": "imagery-service", "version": "9.0.0"}


# ============================================================
# Imagery Endpoints
# ============================================================

@app.post("/api/v1/imagery/search", response_model=ImagerySearchResponse)
async def search_imagery(request: ImageryRequest):
    """
    Search for satellite imagery.
    البحث عن صور الأقمار الصناعية
    """
    logger.info(
        "search_imagery",
        satellite=request.satellite,
        start_date=request.start_date,
        end_date=request.end_date,
        max_cloud=request.max_cloud_cover
    )
    # TODO: Implement Copernicus CDSE API integration
    return ImagerySearchResponse(success=True, images=[], total=0)


@app.post("/api/v1/imagery/download")
async def download_imagery(
    image_id: str = Query(..., description="Image ID to download"),
    background_tasks: BackgroundTasks = None,
):
    """
    Queue imagery download.
    إضافة صورة لقائمة التحميل
    """
    logger.info("download_imagery", image_id=image_id)
    # TODO: Implement async download with CDSE
    return {
        "success": True,
        "job_id": None,
        "message": "Download queuing not yet implemented"
    }


@app.get("/api/v1/imagery/jobs/{job_id}", response_model=ProcessingJob)
async def get_job_status(job_id: str):
    """
    Get processing job status.
    الحصول على حالة المهمة
    """
    logger.info("get_job_status", job_id=job_id)
    # TODO: Implement job tracking
    raise HTTPException(status_code=404, detail="Job not found")


@app.post("/api/v1/imagery/process")
async def process_imagery(
    image_id: str = Query(...),
    process_type: str = Query(..., description="Process type: ndvi, ndwi, true_color, false_color"),
):
    """
    Queue imagery processing.
    إضافة صورة للمعالجة
    """
    logger.info("process_imagery", image_id=image_id, process_type=process_type)
    return {
        "success": True,
        "job_id": None,
        "message": "Processing not yet implemented"
    }


@app.get("/api/v1/imagery/field/{field_id}/latest")
async def get_latest_imagery(
    field_id: str,
    satellite: str = Query(default="sentinel-2"),
):
    """
    Get latest imagery for a field.
    الحصول على أحدث صورة للحقل
    """
    logger.info("get_latest_imagery", field_id=field_id, satellite=satellite)
    return {
        "success": True,
        "image": None,
        "message": "Latest imagery retrieval not yet implemented"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
