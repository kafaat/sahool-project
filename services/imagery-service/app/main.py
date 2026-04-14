"""
Imagery Service - خدمة الصور الفضائية
Sahool Yemen Platform v9.0.0

Handles satellite imagery acquisition and processing with Copernicus CDSE integration.
"""

import sys
sys.path.insert(0, "/app/libs-shared")

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
import hashlib

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field as PydanticField
from prometheus_client import Counter, Histogram, generate_latest
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_AsText, ST_X, ST_Y

from sahool_shared.models import Field, NDVIResult
from sahool_shared.schemas.common import HealthResponse
from sahool_shared.auth import get_current_user, AuthenticatedUser
from sahool_shared.utils import get_db, setup_logging, get_logger

# Metrics
REQUEST_COUNT = Counter("imagery_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("imagery_request_latency_seconds", "Request latency", ["endpoint"])

logger = get_logger(__name__)


# =============================================================================
# Schemas
# =============================================================================

class BoundingBox(BaseModel):
    """Bounding box for imagery search."""
    min_lat: float = PydanticField(..., ge=-90, le=90)
    min_lng: float = PydanticField(..., ge=-180, le=180)
    max_lat: float = PydanticField(..., ge=-90, le=90)
    max_lng: float = PydanticField(..., ge=-180, le=180)


class ImagerySearchRequest(BaseModel):
    """Imagery search request."""
    field_id: Optional[UUID] = None
    bbox: Optional[BoundingBox] = None
    start_date: datetime
    end_date: datetime
    max_cloud_cover: float = PydanticField(default=20.0, ge=0, le=100)
    satellite: str = PydanticField(default="sentinel-2", description="sentinel-2, landsat-8, landsat-9")


class ImageryMetadata(BaseModel):
    """Satellite imagery metadata."""
    id: str
    satellite: str
    product_type: str
    acquisition_date: datetime
    cloud_cover: float
    resolution_meters: float
    bands: List[str]
    bbox: BoundingBox
    thumbnail_url: Optional[str] = None
    download_url: Optional[str] = None
    file_size_mb: Optional[float] = None


class ImagerySearchResponse(BaseModel):
    """Imagery search response."""
    images: List[ImageryMetadata]
    total: int
    query_bbox: Optional[BoundingBox]


class ProcessingJob(BaseModel):
    """Imagery processing job status."""
    job_id: str
    field_id: Optional[UUID]
    status: str
    progress: float
    created_at: datetime
    updated_at: datetime
    process_type: str
    result_url: Optional[str] = None
    error_message: Optional[str] = None


class DownloadRequest(BaseModel):
    """Imagery download request."""
    image_id: str
    field_id: Optional[UUID] = None
    bands: List[str] = PydanticField(default=["B02", "B03", "B04", "B08"])


class ProcessingRequest(BaseModel):
    """Imagery processing request."""
    image_id: str
    field_id: UUID
    process_type: str = PydanticField(..., description="ndvi, ndwi, true_color, false_color, evi")


class FieldImagery(BaseModel):
    """Latest imagery for a field."""
    field_id: UUID
    field_name: str
    latest_acquisition: Optional[datetime]
    latest_ndvi: Optional[float]
    cloud_cover: Optional[float]
    satellite: Optional[str]
    imagery_count: int


class BandInfo(BaseModel):
    """Satellite band information."""
    band_id: str
    name: str
    wavelength_nm: str
    resolution_m: int
    description: str


# =============================================================================
# Constants
# =============================================================================

# Sentinel-2 bands information
SENTINEL2_BANDS = [
    BandInfo(band_id="B01", name="Coastal aerosol", wavelength_nm="443", resolution_m=60, description="Aerosol detection"),
    BandInfo(band_id="B02", name="Blue", wavelength_nm="490", resolution_m=10, description="Blue visible"),
    BandInfo(band_id="B03", name="Green", wavelength_nm="560", resolution_m=10, description="Green visible"),
    BandInfo(band_id="B04", name="Red", wavelength_nm="665", resolution_m=10, description="Red visible"),
    BandInfo(band_id="B05", name="Vegetation Red Edge", wavelength_nm="705", resolution_m=20, description="Red edge 1"),
    BandInfo(band_id="B06", name="Vegetation Red Edge", wavelength_nm="740", resolution_m=20, description="Red edge 2"),
    BandInfo(band_id="B07", name="Vegetation Red Edge", wavelength_nm="783", resolution_m=20, description="Red edge 3"),
    BandInfo(band_id="B08", name="NIR", wavelength_nm="842", resolution_m=10, description="Near infrared"),
    BandInfo(band_id="B8A", name="Vegetation Red Edge", wavelength_nm="865", resolution_m=20, description="Narrow NIR"),
    BandInfo(band_id="B09", name="Water Vapour", wavelength_nm="945", resolution_m=60, description="Water vapour"),
    BandInfo(band_id="B10", name="SWIR - Cirrus", wavelength_nm="1375", resolution_m=60, description="Cirrus"),
    BandInfo(band_id="B11", name="SWIR", wavelength_nm="1610", resolution_m=20, description="Short-wave infrared 1"),
    BandInfo(band_id="B12", name="SWIR", wavelength_nm="2190", resolution_m=20, description="Short-wave infrared 2"),
]

# In-memory job storage (in production, use Redis or DB)
_processing_jobs: Dict[str, ProcessingJob] = {}


# =============================================================================
# Application Setup
# =============================================================================

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
CDSE_CLIENT_ID = os.getenv("CDSE_CLIENT_ID", "")
CDSE_CLIENT_SECRET = os.getenv("CDSE_CLIENT_SECRET", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging(service_name="imagery-service")
    logger.info("imagery_service_starting", version="9.0.0")
    if CDSE_CLIENT_ID:
        logger.info("cdse_configured", client_id_present=True)
    else:
        logger.warning("cdse_not_configured", message="CDSE credentials not set")
    yield
    logger.info("imagery_service_stopping")


app = FastAPI(
    title="Sahool Imagery Service",
    description="خدمة الصور الفضائية - Satellite Imagery Service",
    version="9.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=bool(CORS_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health & Metrics
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="9.0.0", service="imagery-service")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


# =============================================================================
# Helper Functions
# =============================================================================

def generate_mock_imagery(bbox: BoundingBox, start_date: datetime, end_date: datetime, satellite: str, max_cloud: float) -> List[ImageryMetadata]:
    """Generate mock imagery results for development/testing."""
    # Generate deterministic mock data based on bbox
    seed = hashlib.md5(f"{bbox.min_lat}{bbox.max_lng}{start_date}".encode()).hexdigest()

    results = []
    current = start_date
    while current < end_date:
        # Skip some days to simulate realistic acquisition
        if int(seed[:2], 16) % 5 != current.day % 5:
            current += timedelta(days=5)
            continue

        cloud_cover = (int(seed[2:4], 16) % 40)
        if cloud_cover <= max_cloud:
            image_id = f"S2A_MSIL2A_{current.strftime('%Y%m%d')}_{seed[:8]}"
            results.append(ImageryMetadata(
                id=image_id,
                satellite=satellite,
                product_type="L2A",
                acquisition_date=current.replace(hour=10, minute=30),
                cloud_cover=cloud_cover,
                resolution_meters=10.0,
                bands=["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"],
                bbox=bbox,
                file_size_mb=round(800 + (int(seed[4:6], 16) % 400), 1),
            ))

        current += timedelta(days=5)

    return results[:20]  # Limit to 20 results


# =============================================================================
# Imagery Endpoints
# =============================================================================

@app.post("/api/v1/imagery/search", response_model=ImagerySearchResponse)
async def search_imagery(
    request: ImagerySearchRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Search for satellite imagery.
    البحث عن صور الأقمار الصناعية
    """
    with REQUEST_LATENCY.labels(endpoint="search").time():
        bbox = request.bbox

        # If field_id provided, get field bbox
        if request.field_id:
            tenant_id = UUID(user.tenant_id)
            result = await db.execute(
                select(
                    ST_X(Field.coordinates).label("lng"),
                    ST_Y(Field.coordinates).label("lat"),
                    Field.area_hectares,
                )
                .where(and_(Field.id == request.field_id, Field.tenant_id == tenant_id))
            )
            row = result.one_or_none()

            if not row:
                raise HTTPException(status_code=404, detail="الحقل غير موجود")

            # Create bbox from field centroid (approximate)
            lat, lng = row.lat, row.lng
            # Rough estimate: 1 degree ~ 111km
            buffer = 0.01 * (float(row.area_hectares) ** 0.5)  # Scale buffer with field size
            bbox = BoundingBox(
                min_lat=lat - buffer,
                max_lat=lat + buffer,
                min_lng=lng - buffer,
                max_lng=lng + buffer,
            )

        if not bbox:
            raise HTTPException(status_code=400, detail="يجب تحديد field_id أو bbox")

        # Search CDSE API (or use mock data if not configured)
        if CDSE_CLIENT_ID:
            # TODO: Implement actual CDSE API call
            # https://dataspace.copernicus.eu/
            logger.info("cdse_search", bbox=bbox.model_dump(), dates=f"{request.start_date} - {request.end_date}")
            images = []
        else:
            # Use mock data for development
            images = generate_mock_imagery(
                bbox=bbox,
                start_date=request.start_date,
                end_date=request.end_date,
                satellite=request.satellite,
                max_cloud=request.max_cloud_cover,
            )

        REQUEST_COUNT.labels(method="POST", endpoint="search", status="success").inc()

        return ImagerySearchResponse(
            images=images,
            total=len(images),
            query_bbox=bbox,
        )


@app.post("/api/v1/imagery/download", response_model=ProcessingJob)
async def queue_download(
    request: DownloadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Queue imagery download.
    إضافة صورة لقائمة التحميل
    """
    with REQUEST_LATENCY.labels(endpoint="download").time():
        job_id = str(uuid4())
        now = datetime.now(timezone.utc)

        job = ProcessingJob(
            job_id=job_id,
            field_id=request.field_id,
            status="pending",
            progress=0.0,
            created_at=now,
            updated_at=now,
            process_type="download",
        )

        _processing_jobs[job_id] = job

        # In production, this would trigger actual download
        logger.info("download_queued", job_id=job_id, image_id=request.image_id, bands=request.bands)

        REQUEST_COUNT.labels(method="POST", endpoint="download", status="success").inc()

        return job


@app.post("/api/v1/imagery/process", response_model=ProcessingJob)
async def queue_processing(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Queue imagery processing (NDVI calculation, etc.).
    إضافة صورة للمعالجة
    """
    with REQUEST_LATENCY.labels(endpoint="process").time():
        # Validate process type
        valid_types = ["ndvi", "ndwi", "evi", "true_color", "false_color"]
        if request.process_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"نوع المعالجة غير صالح. الأنواع المتاحة: {', '.join(valid_types)}"
            )

        # Verify field exists
        tenant_id = UUID(user.tenant_id)
        result = await db.execute(
            select(Field.id).where(and_(Field.id == request.field_id, Field.tenant_id == tenant_id))
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="الحقل غير موجود")

        job_id = str(uuid4())
        now = datetime.now(timezone.utc)

        job = ProcessingJob(
            job_id=job_id,
            field_id=request.field_id,
            status="pending",
            progress=0.0,
            created_at=now,
            updated_at=now,
            process_type=request.process_type,
        )

        _processing_jobs[job_id] = job

        logger.info(
            "processing_queued",
            job_id=job_id,
            image_id=request.image_id,
            process_type=request.process_type,
            field_id=str(request.field_id),
        )

        REQUEST_COUNT.labels(method="POST", endpoint="process", status="success").inc()

        return job


@app.get("/api/v1/imagery/jobs/{job_id}", response_model=ProcessingJob)
async def get_job_status(
    job_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get processing job status.
    الحصول على حالة المهمة
    """
    with REQUEST_LATENCY.labels(endpoint="job_status").time():
        job = _processing_jobs.get(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="المهمة غير موجودة")

        REQUEST_COUNT.labels(method="GET", endpoint="job_status", status="success").inc()

        return job


@app.get("/api/v1/imagery/jobs", response_model=List[ProcessingJob])
async def list_jobs(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    List processing jobs.
    عرض قائمة المهام
    """
    with REQUEST_LATENCY.labels(endpoint="list_jobs").time():
        jobs = list(_processing_jobs.values())

        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        REQUEST_COUNT.labels(method="GET", endpoint="list_jobs", status="success").inc()

        return jobs[:limit]


@app.get("/api/v1/imagery/field/{field_id}/latest", response_model=FieldImagery)
async def get_latest_field_imagery(
    field_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get latest imagery information for a field.
    الحصول على أحدث معلومات الصور للحقل
    """
    with REQUEST_LATENCY.labels(endpoint="field_latest").time():
        tenant_id = UUID(user.tenant_id)

        # Get field with latest NDVI
        result = await db.execute(
            select(Field.id, Field.name_ar)
            .where(and_(Field.id == field_id, Field.tenant_id == tenant_id))
        )
        field = result.one_or_none()

        if not field:
            raise HTTPException(status_code=404, detail="الحقل غير موجود")

        # Get latest NDVI result
        ndvi_result = await db.execute(
            select(
                NDVIResult.ndvi_value,
                NDVIResult.acquisition_date,
                NDVIResult.cloud_cover_percentage,
                NDVIResult.satellite_id,
            )
            .where(NDVIResult.field_id == field_id)
            .order_by(NDVIResult.acquisition_date.desc())
            .limit(1)
        )
        latest = ndvi_result.one_or_none()

        # Count total imagery records
        count_result = await db.execute(
            select(func.count(NDVIResult.id)).where(NDVIResult.field_id == field_id)
        )
        imagery_count = count_result.scalar() or 0

        REQUEST_COUNT.labels(method="GET", endpoint="field_latest", status="success").inc()

        return FieldImagery(
            field_id=field_id,
            field_name=field.name_ar,
            latest_acquisition=latest[1] if latest else None,
            latest_ndvi=float(latest[0]) if latest else None,
            cloud_cover=float(latest[2]) if latest and latest[2] else None,
            satellite=latest[3] if latest else None,
            imagery_count=imagery_count,
        )


@app.get("/api/v1/imagery/bands", response_model=List[BandInfo])
async def get_band_info(
    satellite: str = Query(default="sentinel-2"),
):
    """
    Get satellite band information.
    الحصول على معلومات نطاقات القمر الصناعي
    """
    if satellite.lower() == "sentinel-2":
        return SENTINEL2_BANDS

    raise HTTPException(status_code=400, detail="القمر الصناعي غير مدعوم حالياً")


@app.get("/api/v1/imagery/coverage")
async def get_yemen_coverage():
    """
    Get imagery coverage statistics for Yemen.
    إحصائيات تغطية الصور لليمن
    """
    # Yemen approximate bounds
    return {
        "region": "Yemen",
        "bbox": {
            "min_lat": 12.1,
            "max_lat": 19.0,
            "min_lng": 42.5,
            "max_lng": 54.5,
        },
        "satellites": {
            "sentinel-2": {
                "revisit_days": 5,
                "resolution_m": 10,
                "available_since": "2015-06-23",
                "bands_count": 13,
            },
            "landsat-8": {
                "revisit_days": 16,
                "resolution_m": 30,
                "available_since": "2013-02-11",
                "bands_count": 11,
            },
            "landsat-9": {
                "revisit_days": 16,
                "resolution_m": 30,
                "available_since": "2021-09-27",
                "bands_count": 11,
            },
        },
        "data_source": "Copernicus CDSE",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
