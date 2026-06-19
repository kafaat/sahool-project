"""
Field Service - خدمة إدارة الحقول
Sahool Yemen v9.0.0

CRUD operations for agricultural fields with geospatial support.
"""

import sys
sys.path.insert(0, "/app/libs-shared")

from contextlib import asynccontextmanager
from datetime import date, timezone, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field as PydanticField
from prometheus_client import Counter, Histogram, generate_latest
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_AsGeoJSON, ST_GeomFromGeoJSON, ST_MakePoint

from sahool_shared.models import Field
from sahool_shared.schemas.common import HealthResponse, PaginatedResponse
from sahool_shared.auth import get_current_user, AuthenticatedUser
from sahool_shared.utils import get_db, setup_logging, get_logger

import os

# Metrics
REQUEST_COUNT = Counter("field_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("field_request_latency_seconds", "Request latency", ["endpoint"])

logger = get_logger(__name__)


# =============================================================================
# Schemas
# =============================================================================

class FieldCreate(BaseModel):
    """Create field request."""
    name_ar: str = PydanticField(..., min_length=2, max_length=200)
    name_en: Optional[str] = None
    area_hectares: float = PydanticField(..., gt=0)
    crop_type: Optional[str] = None
    crop_variety: Optional[str] = None
    planting_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    latitude: float = PydanticField(..., ge=-90, le=90)
    longitude: float = PydanticField(..., ge=-180, le=180)
    elevation_meters: Optional[int] = None
    soil_type: Optional[str] = None
    soil_ph: Optional[float] = PydanticField(None, ge=0, le=14)
    irrigation_type: Optional[str] = None
    farmer_id: Optional[UUID] = None
    region_id: Optional[int] = None


class FieldUpdate(BaseModel):
    """Update field request."""
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    area_hectares: Optional[float] = None
    crop_type: Optional[str] = None
    crop_variety: Optional[str] = None
    planting_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_meters: Optional[int] = None
    soil_type: Optional[str] = None
    soil_ph: Optional[float] = None
    irrigation_type: Optional[str] = None
    status: Optional[str] = None


class FieldResponse(BaseModel):
    """Field response."""
    id: UUID
    tenant_id: UUID
    name_ar: str
    name_en: Optional[str]
    area_hectares: float
    crop_type: Optional[str]
    crop_variety: Optional[str]
    planting_date: Optional[date]
    expected_harvest_date: Optional[date]
    latitude: float
    longitude: float
    elevation_meters: Optional[int]
    soil_type: Optional[str]
    soil_ph: Optional[float]
    irrigation_type: Optional[str]
    status: str
    farmer_id: Optional[UUID]
    region_id: Optional[int]
    health_status: str
    latest_ndvi: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FieldListResponse(BaseModel):
    """Paginated field list."""
    items: List[FieldResponse]
    total: int
    page: int
    page_size: int


class FieldStats(BaseModel):
    """Field statistics."""
    total_fields: int
    total_area_hectares: float
    active_fields: int
    avg_ndvi: Optional[float]
    crops_distribution: dict


# =============================================================================
# Application Setup
# =============================================================================

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = bool(CORS_ORIGINS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging(service_name="field-service")
    logger.info("field_service_starting", version="9.0.0")
    yield
    logger.info("field_service_stopping")


app = FastAPI(
    title="Sahool Field Service",
    description="خدمة إدارة الحقول الزراعية",
    version="9.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health & Metrics
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="9.0.0", service="field-service")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


# =============================================================================
# Field CRUD Endpoints
# =============================================================================

@app.get("/api/v1/fields", response_model=FieldListResponse)
async def list_fields(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    crop_type: Optional[str] = None,
    status: Optional[str] = None,
    region_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    List all fields for the current tenant.
    عرض جميع الحقول للمستأجر الحالي
    """
    with REQUEST_LATENCY.labels(endpoint="list_fields").time():
        query = select(Field).where(Field.tenant_id == UUID(user.tenant_id))

        if crop_type:
            query = query.where(Field.crop_type == crop_type)
        if status:
            query = query.where(Field.status == status)
        if region_id:
            query = query.where(Field.region_id == region_id)

        # Count total
        count_query = select(func.count(Field.id)).where(Field.tenant_id == UUID(user.tenant_id))
        if crop_type:
            count_query = count_query.where(Field.crop_type == crop_type)
        if status:
            count_query = count_query.where(Field.status == status)
        if region_id:
            count_query = count_query.where(Field.region_id == region_id)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(Field.created_at.desc())

        result = await db.execute(query)
        fields = result.scalars().all()

        # Get coordinates from geography
        items = []
        for field in fields:
            coords_result = await db.execute(
                select(
                    func.ST_X(func.ST_GeomFromWKB(field.coordinates)),
                    func.ST_Y(func.ST_GeomFromWKB(field.coordinates))
                )
            )
            coords = coords_result.first()
            lon, lat = (coords[0], coords[1]) if coords else (0, 0)

            items.append(FieldResponse(
                id=field.id,
                tenant_id=field.tenant_id,
                name_ar=field.name_ar,
                name_en=field.name_en,
                area_hectares=float(field.area_hectares),
                crop_type=field.crop_type,
                crop_variety=field.crop_variety,
                planting_date=field.planting_date,
                expected_harvest_date=field.expected_harvest_date,
                latitude=lat,
                longitude=lon,
                elevation_meters=field.elevation_meters,
                soil_type=field.soil_type,
                soil_ph=float(field.soil_ph) if field.soil_ph else None,
                irrigation_type=field.irrigation_type,
                status=field.status,
                farmer_id=field.farmer_id,
                region_id=field.region_id,
                health_status=field.health_status,
                latest_ndvi=field.latest_ndvi,
                created_at=field.created_at,
                updated_at=field.updated_at,
            ))

        REQUEST_COUNT.labels(method="GET", endpoint="list_fields", status="success").inc()

        return FieldListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )


@app.post("/api/v1/fields", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
async def create_field(
    data: FieldCreate,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Create a new field.
    إنشاء حقل جديد
    """
    with REQUEST_LATENCY.labels(endpoint="create_field").time():
        # Create point from coordinates
        point_wkt = f"POINT({data.longitude} {data.latitude})"

        field = Field(
            tenant_id=UUID(user.tenant_id),
            name_ar=data.name_ar,
            name_en=data.name_en,
            area_hectares=data.area_hectares,
            crop_type=data.crop_type,
            crop_variety=data.crop_variety,
            planting_date=data.planting_date,
            expected_harvest_date=data.expected_harvest_date,
            coordinates=point_wkt,
            elevation_meters=data.elevation_meters,
            soil_type=data.soil_type,
            soil_ph=data.soil_ph,
            irrigation_type=data.irrigation_type,
            farmer_id=data.farmer_id,
            region_id=data.region_id,
            status="active",
        )

        db.add(field)
        await db.commit()
        await db.refresh(field)

        logger.info("field_created", field_id=str(field.id), tenant_id=user.tenant_id)
        REQUEST_COUNT.labels(method="POST", endpoint="create_field", status="success").inc()

        return FieldResponse(
            id=field.id,
            tenant_id=field.tenant_id,
            name_ar=field.name_ar,
            name_en=field.name_en,
            area_hectares=float(field.area_hectares),
            crop_type=field.crop_type,
            crop_variety=field.crop_variety,
            planting_date=field.planting_date,
            expected_harvest_date=field.expected_harvest_date,
            latitude=data.latitude,
            longitude=data.longitude,
            elevation_meters=field.elevation_meters,
            soil_type=field.soil_type,
            soil_ph=float(field.soil_ph) if field.soil_ph else None,
            irrigation_type=field.irrigation_type,
            status=field.status,
            farmer_id=field.farmer_id,
            region_id=field.region_id,
            health_status="unknown",
            latest_ndvi=None,
            created_at=field.created_at,
            updated_at=field.updated_at,
        )


@app.get("/api/v1/fields/{field_id}", response_model=FieldResponse)
async def get_field(
    field_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get a specific field.
    الحصول على حقل محدد
    """
    result = await db.execute(
        select(Field).where(
            and_(Field.id == field_id, Field.tenant_id == UUID(user.tenant_id))
        )
    )
    field = result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=404, detail="الحقل غير موجود")

    # Get coordinates
    coords_result = await db.execute(
        select(
            func.ST_X(func.ST_GeomFromWKB(field.coordinates)),
            func.ST_Y(func.ST_GeomFromWKB(field.coordinates))
        )
    )
    coords = coords_result.first()
    lon, lat = (coords[0], coords[1]) if coords else (0, 0)

    return FieldResponse(
        id=field.id,
        tenant_id=field.tenant_id,
        name_ar=field.name_ar,
        name_en=field.name_en,
        area_hectares=float(field.area_hectares),
        crop_type=field.crop_type,
        crop_variety=field.crop_variety,
        planting_date=field.planting_date,
        expected_harvest_date=field.expected_harvest_date,
        latitude=lat,
        longitude=lon,
        elevation_meters=field.elevation_meters,
        soil_type=field.soil_type,
        soil_ph=float(field.soil_ph) if field.soil_ph else None,
        irrigation_type=field.irrigation_type,
        status=field.status,
        farmer_id=field.farmer_id,
        region_id=field.region_id,
        health_status=field.health_status,
        latest_ndvi=field.latest_ndvi,
        created_at=field.created_at,
        updated_at=field.updated_at,
    )


@app.patch("/api/v1/fields/{field_id}", response_model=FieldResponse)
async def update_field(
    field_id: UUID,
    data: FieldUpdate,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Update a field.
    تحديث حقل
    """
    result = await db.execute(
        select(Field).where(
            and_(Field.id == field_id, Field.tenant_id == UUID(user.tenant_id))
        )
    )
    field = result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=404, detail="الحقل غير موجود")

    # Update fields
    update_data = data.model_dump(exclude_unset=True)

    # Handle coordinates update
    if "latitude" in update_data or "longitude" in update_data:
        lat = update_data.pop("latitude", None)
        lon = update_data.pop("longitude", None)
        if lat and lon:
            field.coordinates = f"POINT({lon} {lat})"

    for key, value in update_data.items():
        setattr(field, key, value)

    await db.commit()
    await db.refresh(field)

    # Get coordinates
    coords_result = await db.execute(
        select(
            func.ST_X(func.ST_GeomFromWKB(field.coordinates)),
            func.ST_Y(func.ST_GeomFromWKB(field.coordinates))
        )
    )
    coords = coords_result.first()
    lon, lat = (coords[0], coords[1]) if coords else (0, 0)

    logger.info("field_updated", field_id=str(field.id))

    return FieldResponse(
        id=field.id,
        tenant_id=field.tenant_id,
        name_ar=field.name_ar,
        name_en=field.name_en,
        area_hectares=float(field.area_hectares),
        crop_type=field.crop_type,
        crop_variety=field.crop_variety,
        planting_date=field.planting_date,
        expected_harvest_date=field.expected_harvest_date,
        latitude=lat,
        longitude=lon,
        elevation_meters=field.elevation_meters,
        soil_type=field.soil_type,
        soil_ph=float(field.soil_ph) if field.soil_ph else None,
        irrigation_type=field.irrigation_type,
        status=field.status,
        farmer_id=field.farmer_id,
        region_id=field.region_id,
        health_status=field.health_status,
        latest_ndvi=field.latest_ndvi,
        created_at=field.created_at,
        updated_at=field.updated_at,
    )


@app.delete("/api/v1/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field(
    field_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Delete a field (soft delete).
    حذف حقل
    """
    result = await db.execute(
        select(Field).where(
            and_(Field.id == field_id, Field.tenant_id == UUID(user.tenant_id))
        )
    )
    field = result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=404, detail="الحقل غير موجود")

    field.status = "deleted"
    await db.commit()

    logger.info("field_deleted", field_id=str(field.id))


@app.get("/api/v1/fields/stats", response_model=FieldStats)
async def get_field_stats(
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get field statistics for the current tenant.
    إحصائيات الحقول للمستأجر الحالي
    """
    tenant_id = UUID(user.tenant_id)

    # Total fields and area
    stats_result = await db.execute(
        select(
            func.count(Field.id),
            func.sum(Field.area_hectares),
            func.count(Field.id).filter(Field.status == "active")
        ).where(Field.tenant_id == tenant_id)
    )
    stats = stats_result.first()

    # Crop distribution
    crops_result = await db.execute(
        select(Field.crop_type, func.count(Field.id))
        .where(and_(Field.tenant_id == tenant_id, Field.crop_type.isnot(None)))
        .group_by(Field.crop_type)
    )
    crops = {row[0]: row[1] for row in crops_result.all()}

    return FieldStats(
        total_fields=stats[0] or 0,
        total_area_hectares=float(stats[1] or 0),
        active_fields=stats[2] or 0,
        avg_ndvi=None,
        crops_distribution=crops,
    )


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
