"""
Geo Service - خدمة البيانات الجغرافية
Sahool Yemen Platform v9.0.0

Handles geographic data processing and spatial operations with PostGIS.
"""

import sys
sys.path.insert(0, "/app/libs-shared")

import os
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field as PydanticField
from prometheus_client import Counter, Histogram, generate_latest
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_AsGeoJSON, ST_Area, ST_Centroid, ST_Contains, ST_Intersects, ST_Within, ST_Distance, ST_X, ST_Y

from sahool_shared.models import Field, Region
from sahool_shared.schemas.common import HealthResponse
from sahool_shared.auth import get_current_user, AuthenticatedUser
from sahool_shared.utils import get_db, setup_logging, get_logger

# Metrics
REQUEST_COUNT = Counter("geo_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("geo_request_latency_seconds", "Request latency", ["endpoint"])

logger = get_logger(__name__)


# =============================================================================
# Schemas
# =============================================================================

class GeoPoint(BaseModel):
    """Geographic point."""
    lat: float = PydanticField(..., ge=-90, le=90)
    lng: float = PydanticField(..., ge=-180, le=180)


class GeoPolygon(BaseModel):
    """Geographic polygon (GeoJSON format)."""
    type: str = "Polygon"
    coordinates: List[List[List[float]]]


class FieldBoundary(BaseModel):
    """Field boundary with geometry."""
    field_id: UUID
    name_ar: str
    name_en: Optional[str]
    geometry: Optional[Dict[str, Any]]
    centroid: Optional[GeoPoint]
    area_hectares: float


class FieldsInAreaResponse(BaseModel):
    """Response for fields in area query."""
    fields: List[FieldBoundary]
    total: int


class GeocodingResult(BaseModel):
    """Geocoding result (Yemen-specific)."""
    governorate: Optional[str]
    district: Optional[str]
    location: GeoPoint
    formatted_address_ar: Optional[str]
    formatted_address_en: Optional[str]


class SpatialQueryRequest(BaseModel):
    """Spatial query request."""
    geometry: GeoPolygon
    operation: str = PydanticField(..., description="intersects, contains, within")


class SpatialQueryResponse(BaseModel):
    """Spatial query response."""
    operation: str
    results: List[FieldBoundary]
    total: int


class AreaCalculation(BaseModel):
    """Area calculation result."""
    area_hectares: float
    area_square_meters: float
    perimeter_meters: float


class DistanceResult(BaseModel):
    """Distance calculation result."""
    distance_meters: float
    distance_km: float


class NearbyFieldsResponse(BaseModel):
    """Nearby fields response."""
    fields: List[FieldBoundary]
    center: GeoPoint
    radius_meters: float


# =============================================================================
# Application Setup
# =============================================================================

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging(service_name="geo-service")
    logger.info("geo_service_starting", version="9.0.0")
    yield
    logger.info("geo_service_stopping")


app = FastAPI(
    title="Sahool Geo Service",
    description="خدمة البيانات الجغرافية - Geographic Data Service",
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
    return HealthResponse(status="healthy", version="9.0.0", service="geo-service")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


# =============================================================================
# Geo Endpoints
# =============================================================================

@app.get("/api/v1/geo/fields", response_model=FieldsInAreaResponse)
async def list_field_geometries(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    List all fields with their geometries.
    عرض جميع الحقول مع أشكالها الهندسية
    """
    with REQUEST_LATENCY.labels(endpoint="list_fields").time():
        tenant_id = UUID(user.tenant_id)

        # Count total
        count_result = await db.execute(
            select(func.count(Field.id))
            .where(and_(Field.tenant_id == tenant_id, Field.status == "active"))
        )
        total = count_result.scalar() or 0

        # Get fields with geometry
        query = (
            select(
                Field.id,
                Field.name_ar,
                Field.name_en,
                Field.area_hectares,
                ST_AsGeoJSON(Field.field_geometry).label("geometry"),
                ST_X(ST_Centroid(Field.coordinates)).label("centroid_lng"),
                ST_Y(ST_Centroid(Field.coordinates)).label("centroid_lat"),
            )
            .where(and_(Field.tenant_id == tenant_id, Field.status == "active"))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(query)
        rows = result.all()

        fields = []
        for row in rows:
            import json
            geometry = json.loads(row.geometry) if row.geometry else None
            centroid = GeoPoint(lat=row.centroid_lat, lng=row.centroid_lng) if row.centroid_lat else None

            fields.append(FieldBoundary(
                field_id=row.id,
                name_ar=row.name_ar,
                name_en=row.name_en,
                geometry=geometry,
                centroid=centroid,
                area_hectares=float(row.area_hectares),
            ))

        REQUEST_COUNT.labels(method="GET", endpoint="list_fields", status="success").inc()

        return FieldsInAreaResponse(fields=fields, total=total)


@app.get("/api/v1/geo/fields/{field_id}/boundary", response_model=FieldBoundary)
async def get_field_boundary(
    field_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get field boundary geometry.
    الحصول على حدود الحقل
    """
    with REQUEST_LATENCY.labels(endpoint="field_boundary").time():
        query = (
            select(
                Field.id,
                Field.name_ar,
                Field.name_en,
                Field.area_hectares,
                ST_AsGeoJSON(Field.field_geometry).label("geometry"),
                ST_X(ST_Centroid(Field.coordinates)).label("centroid_lng"),
                ST_Y(ST_Centroid(Field.coordinates)).label("centroid_lat"),
            )
            .where(and_(Field.id == field_id, Field.tenant_id == UUID(user.tenant_id)))
        )

        result = await db.execute(query)
        row = result.one_or_none()

        if not row:
            raise HTTPException(status_code=404, detail="الحقل غير موجود")

        import json
        geometry = json.loads(row.geometry) if row.geometry else None
        centroid = GeoPoint(lat=row.centroid_lat, lng=row.centroid_lng) if row.centroid_lat else None

        REQUEST_COUNT.labels(method="GET", endpoint="field_boundary", status="success").inc()

        return FieldBoundary(
            field_id=row.id,
            name_ar=row.name_ar,
            name_en=row.name_en,
            geometry=geometry,
            centroid=centroid,
            area_hectares=float(row.area_hectares),
        )


@app.post("/api/v1/geo/spatial-query", response_model=SpatialQueryResponse)
async def spatial_query(
    request: SpatialQueryRequest,
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Perform spatial query on fields.
    تنفيذ استعلام مكاني على الحقول
    """
    with REQUEST_LATENCY.labels(endpoint="spatial_query").time():
        tenant_id = UUID(user.tenant_id)

        # Convert GeoJSON to WKT for PostGIS
        import json
        geojson_str = json.dumps({"type": request.geometry.type, "coordinates": request.geometry.coordinates})

        # Build query based on operation
        base_query = (
            select(
                Field.id,
                Field.name_ar,
                Field.name_en,
                Field.area_hectares,
                ST_AsGeoJSON(Field.field_geometry).label("geometry"),
                ST_X(ST_Centroid(Field.coordinates)).label("centroid_lng"),
                ST_Y(ST_Centroid(Field.coordinates)).label("centroid_lat"),
            )
            .where(and_(Field.tenant_id == tenant_id, Field.status == "active"))
        )

        if request.operation == "intersects":
            base_query = base_query.where(
                ST_Intersects(Field.field_geometry, func.ST_GeomFromGeoJSON(geojson_str))
            )
        elif request.operation == "contains":
            base_query = base_query.where(
                ST_Contains(func.ST_GeomFromGeoJSON(geojson_str), Field.field_geometry)
            )
        elif request.operation == "within":
            base_query = base_query.where(
                ST_Within(Field.field_geometry, func.ST_GeomFromGeoJSON(geojson_str))
            )
        else:
            raise HTTPException(status_code=400, detail="العملية غير معروفة. استخدم: intersects, contains, within")

        result = await db.execute(base_query)
        rows = result.all()

        fields = []
        for row in rows:
            geometry = json.loads(row.geometry) if row.geometry else None
            centroid = GeoPoint(lat=row.centroid_lat, lng=row.centroid_lng) if row.centroid_lat else None

            fields.append(FieldBoundary(
                field_id=row.id,
                name_ar=row.name_ar,
                name_en=row.name_en,
                geometry=geometry,
                centroid=centroid,
                area_hectares=float(row.area_hectares),
            ))

        REQUEST_COUNT.labels(method="POST", endpoint="spatial_query", status="success").inc()

        return SpatialQueryResponse(operation=request.operation, results=fields, total=len(fields))


@app.post("/api/v1/geo/calculate-area", response_model=AreaCalculation)
async def calculate_area(
    geometry: GeoPolygon,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate area of a polygon in hectares.
    حساب مساحة المضلع بالهكتار
    """
    with REQUEST_LATENCY.labels(endpoint="calculate_area").time():
        import json
        geojson_str = json.dumps({"type": geometry.type, "coordinates": geometry.coordinates})

        # Use PostGIS to calculate area (geography type gives meters squared)
        result = await db.execute(
            text("""
                SELECT
                    ST_Area(ST_GeomFromGeoJSON(:geojson)::geography) as area_m2,
                    ST_Perimeter(ST_GeomFromGeoJSON(:geojson)::geography) as perimeter_m
            """),
            {"geojson": geojson_str}
        )
        row = result.one()

        area_m2 = row.area_m2 or 0
        perimeter_m = row.perimeter_m or 0
        area_hectares = area_m2 / 10000  # 1 hectare = 10,000 m²

        REQUEST_COUNT.labels(method="POST", endpoint="calculate_area", status="success").inc()

        return AreaCalculation(
            area_hectares=round(area_hectares, 4),
            area_square_meters=round(area_m2, 2),
            perimeter_meters=round(perimeter_m, 2),
        )


@app.get("/api/v1/geo/distance", response_model=DistanceResult)
async def calculate_distance(
    lat1: float = Query(..., ge=-90, le=90),
    lng1: float = Query(..., ge=-180, le=180),
    lat2: float = Query(..., ge=-90, le=90),
    lng2: float = Query(..., ge=-180, le=180),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate distance between two points.
    حساب المسافة بين نقطتين
    """
    with REQUEST_LATENCY.labels(endpoint="distance").time():
        result = await db.execute(
            text("""
                SELECT ST_Distance(
                    ST_MakePoint(:lng1, :lat1)::geography,
                    ST_MakePoint(:lng2, :lat2)::geography
                ) as distance_m
            """),
            {"lat1": lat1, "lng1": lng1, "lat2": lat2, "lng2": lng2}
        )
        row = result.one()
        distance_m = row.distance_m or 0

        REQUEST_COUNT.labels(method="GET", endpoint="distance", status="success").inc()

        return DistanceResult(
            distance_meters=round(distance_m, 2),
            distance_km=round(distance_m / 1000, 3),
        )


@app.get("/api/v1/geo/nearby", response_model=NearbyFieldsResponse)
async def get_nearby_fields(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_meters: float = Query(5000, ge=100, le=50000),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get fields within radius of a point.
    الحصول على الحقول ضمن نطاق من نقطة
    """
    with REQUEST_LATENCY.labels(endpoint="nearby").time():
        tenant_id = UUID(user.tenant_id)

        query = (
            select(
                Field.id,
                Field.name_ar,
                Field.name_en,
                Field.area_hectares,
                ST_AsGeoJSON(Field.field_geometry).label("geometry"),
                ST_X(ST_Centroid(Field.coordinates)).label("centroid_lng"),
                ST_Y(ST_Centroid(Field.coordinates)).label("centroid_lat"),
            )
            .where(
                and_(
                    Field.tenant_id == tenant_id,
                    Field.status == "active",
                    ST_Distance(
                        Field.coordinates,
                        func.ST_MakePoint(lng, lat).cast(text("geography"))
                    ) <= radius_meters
                )
            )
            .order_by(
                ST_Distance(Field.coordinates, func.ST_MakePoint(lng, lat).cast(text("geography")))
            )
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        import json
        fields = []
        for row in rows:
            geometry = json.loads(row.geometry) if row.geometry else None
            centroid = GeoPoint(lat=row.centroid_lat, lng=row.centroid_lng) if row.centroid_lat else None

            fields.append(FieldBoundary(
                field_id=row.id,
                name_ar=row.name_ar,
                name_en=row.name_en,
                geometry=geometry,
                centroid=centroid,
                area_hectares=float(row.area_hectares),
            ))

        REQUEST_COUNT.labels(method="GET", endpoint="nearby", status="success").inc()

        return NearbyFieldsResponse(
            fields=fields,
            center=GeoPoint(lat=lat, lng=lng),
            radius_meters=radius_meters,
        )


@app.get("/api/v1/geo/regions", response_model=List[Dict[str, Any]])
async def list_regions(
    db: AsyncSession = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    List all Yemen regions/governorates.
    عرض جميع المحافظات والمناطق
    """
    with REQUEST_LATENCY.labels(endpoint="regions").time():
        result = await db.execute(
            select(Region.id, Region.name_ar, Region.name_en, Region.governorate, Region.district)
            .order_by(Region.governorate, Region.district)
        )
        rows = result.all()

        regions = [
            {
                "id": row.id,
                "name_ar": row.name_ar,
                "name_en": row.name_en,
                "governorate": row.governorate,
                "district": row.district,
            }
            for row in rows
        ]

        REQUEST_COUNT.labels(method="GET", endpoint="regions", status="success").inc()

        return regions


@app.get("/api/v1/geo/reverse-geocode", response_model=GeocodingResult)
async def reverse_geocode(
    lat: float = Query(..., ge=12, le=19, description="Latitude (Yemen range: 12-19)"),
    lng: float = Query(..., ge=42, le=55, description="Longitude (Yemen range: 42-55)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Reverse geocode coordinates to nearest region (Yemen-specific).
    تحويل الإحداثيات إلى أقرب منطقة
    """
    with REQUEST_LATENCY.labels(endpoint="reverse_geocode").time():
        # Find nearest region
        result = await db.execute(
            select(Region.governorate, Region.district, Region.name_ar, Region.name_en)
            .where(Region.geometry.isnot(None))
            .order_by(
                ST_Distance(
                    Region.geometry,
                    func.ST_MakePoint(lng, lat).cast(text("geography"))
                )
            )
            .limit(1)
        )
        row = result.one_or_none()

        if row:
            formatted_ar = f"{row.district or ''}, {row.governorate or ''}, اليمن".strip(", ")
            formatted_en = f"{row.name_en or row.district or ''}, {row.governorate or ''}, Yemen".strip(", ")

            return GeocodingResult(
                governorate=row.governorate,
                district=row.district,
                location=GeoPoint(lat=lat, lng=lng),
                formatted_address_ar=formatted_ar,
                formatted_address_en=formatted_en,
            )

        REQUEST_COUNT.labels(method="GET", endpoint="reverse_geocode", status="success").inc()

        return GeocodingResult(
            governorate=None,
            district=None,
            location=GeoPoint(lat=lat, lng=lng),
            formatted_address_ar="موقع في اليمن",
            formatted_address_en="Location in Yemen",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
