"""
Optimized Fields API Routes with Streaming, Security, and Performance
Version: 3.2.0
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from geoalchemy2.shape import to_shape
from geoalchemy2.functions import ST_AsGeoJSON

from app.db.session import get_db
from app import models, schemas
from app.core.security import (
    get_current_user,
    TokenData,
    require_permission,
    require_spatial_access,
    spatial_validator,
    geo_limiter,
    TenantIsolation,
    audit_logger
)
from app.services.field_service import (
    list_fields,
    create_field,
    get_field,
    update_field,
    delete_field
)

router = APIRouter(prefix="/api/v2/fields", tags=["fields-optimized"])

# ===================================================================
# LIST FIELDS - With Pagination and Filtering
# ===================================================================

@router.get("", response_model=schemas.FieldListResponse)
@geo_limiter.limiter.limit(geo_limiter.get_limit("standard"))
async def list_fields_paginated(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    crop: Optional[str] = Query(None, description="Filter by crop type"),
    min_area: Optional[float] = Query(None, ge=0, description="Minimum area (hectares)"),
    max_area: Optional[float] = Query(None, ge=0, description="Maximum area (hectares)"),
    search: Optional[str] = Query(None, description="Search in field name"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """
    List fields with advanced filtering and pagination

    - Tenant isolation enforced
    - Rate limited
    - Optimized with indexes
    """

    # Validate pagination
    page, page_size = spatial_validator.validate_pagination(page, page_size)

    # Validate tenant access
    TenantIsolation.validate_tenant_access(current_user, str(current_user.tenant_id))

    # Build query with filters
    query = db.query(models.Field).filter(
        and_(
            models.Field.tenant_id == current_user.tenant_id,
            models.Field.deleted_at.is_(None)  # Only active fields
        )
    )

    # Apply filters
    if crop:
        query = query.filter(models.Field.crop == crop)

    if min_area is not None:
        query = query.filter(models.Field.area_ha >= min_area)

    if max_area is not None:
        query = query.filter(models.Field.area_ha <= max_area)

    if search:
        query = query.filter(models.Field.name.ilike(f"%{search}%"))

    # Count total
    total = query.count()

    # Apply sorting
    sort_column = getattr(models.Field, sort_by, models.Field.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    offset = (page - 1) * page_size
    fields = query.offset(offset).limit(page_size).all()

    # Audit log
    audit_logger.log_access(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        action="list_fields",
        resource="fields",
        details={"page": page, "page_size": page_size, "total": total}
    )

    return {
        "items": fields,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }

# ===================================================================
# EXPORT FIELDS - Streaming for Large Datasets
# ===================================================================

@router.get("/export")
@geo_limiter.limiter.limit(geo_limiter.get_limit("export"))
async def export_fields_streaming(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    format: str = Query("geojson", regex="^(geojson|csv)$"),
    crop: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Export fields with streaming for large datasets

    - Prevents memory overflow
    - Streams data in chunks
    - Rate limited (5 exports/minute)
    """

    # Validate tenant access
    TenantIsolation.validate_tenant_access(current_user, str(current_user.tenant_id))

    # Build base query
    query = db.query(models.Field).filter(
        and_(
            models.Field.tenant_id == current_user.tenant_id,
            models.Field.deleted_at.is_(None)
        )
    )

    if crop:
        query = query.filter(models.Field.crop == crop)

    # Count total for audit
    total = query.count()

    if format == "geojson":
        return StreamingResponse(
            _stream_geojson(db, current_user.tenant_id, crop),
            media_type="application/geo+json",
            headers={
                "Content-Disposition": f"attachment; filename=fields_{current_user.tenant_id}.geojson",
                "X-Total-Count": str(total)
            }
        )
    else:  # CSV
        return StreamingResponse(
            _stream_csv(db, current_user.tenant_id, crop),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=fields_{current_user.tenant_id}.csv",
                "X-Total-Count": str(total)
            }
        )

async def _stream_geojson(db: Session, tenant_id: str, crop: Optional[str] = None):
    """Stream GeoJSON features in chunks"""

    # Start FeatureCollection
    yield '{"type": "FeatureCollection", "features": ['

    page_size = 100
    offset = 0
    first = True

    while True:
        # Query chunk
        query = db.query(
            models.Field.id,
            models.Field.name,
            models.Field.crop,
            models.Field.area_ha,
            models.Field.created_at,
            ST_AsGeoJSON(models.Field.geometry).label('geometry_json')
        ).filter(
            and_(
                models.Field.tenant_id == tenant_id,
                models.Field.deleted_at.is_(None)
            )
        )

        if crop:
            query = query.filter(models.Field.crop == crop)

        rows = query.offset(offset).limit(page_size).all()

        if not rows:
            break

        for row in rows:
            if not first:
                yield ','
            else:
                first = False

            feature = {
                "type": "Feature",
                "id": str(row.id),
                "geometry": json.loads(row.geometry_json),
                "properties": {
                    "name": row.name,
                    "crop": row.crop,
                    "area_ha": float(row.area_ha) if row.area_ha else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                }
            }

            yield json.dumps(feature)

        if len(rows) < page_size:
            break

        offset += page_size

    # End FeatureCollection
    yield ']}'

async def _stream_csv(db: Session, tenant_id: str, crop: Optional[str] = None):
    """Stream CSV in chunks"""

    # CSV header
    yield 'id,name,crop,area_ha,centroid_lat,centroid_lon,created_at\n'

    page_size = 100
    offset = 0

    while True:
        query = db.query(
            models.Field.id,
            models.Field.name,
            models.Field.crop,
            models.Field.area_ha,
            models.Field.centroid_lat,
            models.Field.centroid_lon,
            models.Field.created_at
        ).filter(
            and_(
                models.Field.tenant_id == tenant_id,
                models.Field.deleted_at.is_(None)
            )
        )

        if crop:
            query = query.filter(models.Field.crop == crop)

        rows = query.offset(offset).limit(page_size).all()

        if not rows:
            break

        for row in rows:
            yield f'"{row.id}","{row.name}","{row.crop or ""}",{row.area_ha or ""},{row.centroid_lat or ""},{row.centroid_lon or ""},{row.created_at.isoformat() if row.created_at else ""}\n'

        if len(rows) < page_size:
            break

        offset += page_size

# ===================================================================
# SPATIAL QUERIES - Optimized with Indexes
# ===================================================================

@router.get("/nearby")
@geo_limiter.limiter.limit(geo_limiter.get_limit("heavy"))
async def find_nearby_fields(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    distance: float = Query(..., gt=0, description="Distance in meters"),
    current_user: TokenData = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Find fields within distance of a point

    - Uses spatial index (GIST)
    - Optimized with ST_DWithin
    - Rate limited (10 queries/minute)
    """

    # Validate distance
    distance = spatial_validator.validate_query_distance(distance)

    # Validate tenant access
    TenantIsolation.validate_tenant_access(current_user, str(current_user.tenant_id))

    # Build spatial query
    point_wkt = f'POINT({lon} {lat})'

    results = db.query(
        models.Field,
        func.ST_Distance(
            func.ST_GeogFromText(point_wkt),
            func.ST_GeogFromText(func.ST_AsText(models.Field.geometry))
        ).label('distance_meters')
    ).filter(
        and_(
            models.Field.tenant_id == current_user.tenant_id,
            models.Field.deleted_at.is_(None),
            func.ST_DWithin(
                func.ST_GeogFromText(point_wkt),
                func.ST_GeogFromText(func.ST_AsText(models.Field.geometry)),
                distance
            )
        )
    ).order_by(text('distance_meters')).limit(limit).all()

    # Audit log
    audit_logger.log_access(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        action="spatial_query",
        resource="fields/nearby",
        details={"lat": lat, "lon": lon, "distance": distance, "results": len(results)}
    )

    return {
        "query_point": {"lat": lat, "lon": lon},
        "distance_meters": distance,
        "results": [
            {
                "field": result[0],
                "distance_meters": float(result[1])
            }
            for result in results
        ]
    }

# ===================================================================
# STATISTICS - Aggregations
# ===================================================================

@router.get("/statistics")
@geo_limiter.limiter.limit(geo_limiter.get_limit("standard"))
async def get_field_statistics(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get field statistics for tenant

    - Total fields, area, crops
    - Optimized with indexes
    """

    # Validate tenant access
    TenantIsolation.validate_tenant_access(current_user, str(current_user.tenant_id))

    stats = db.query(
        func.count(models.Field.id).label('total_fields'),
        func.sum(models.Field.area_ha).label('total_area_ha'),
        func.avg(models.Field.area_ha).label('avg_area_ha'),
        func.count(func.distinct(models.Field.crop)).label('distinct_crops')
    ).filter(
        and_(
            models.Field.tenant_id == current_user.tenant_id,
            models.Field.deleted_at.is_(None)
        )
    ).first()

    # Crops breakdown
    crops = db.query(
        models.Field.crop,
        func.count(models.Field.id).label('count'),
        func.sum(models.Field.area_ha).label('total_area')
    ).filter(
        and_(
            models.Field.tenant_id == current_user.tenant_id,
            models.Field.deleted_at.is_(None),
            models.Field.crop.isnot(None)
        )
    ).group_by(models.Field.crop).all()

    return {
        "total_fields": stats.total_fields or 0,
        "total_area_ha": float(stats.total_area_ha) if stats.total_area_ha else 0,
        "avg_area_ha": float(stats.avg_area_ha) if stats.avg_area_ha else 0,
        "distinct_crops": stats.distinct_crops or 0,
        "crops_breakdown": [
            {
                "crop": crop.crop,
                "count": crop.count,
                "total_area_ha": float(crop.total_area) if crop.total_area else 0
            }
            for crop in crops
        ]
    }

# ===================================================================
# SOFT DELETE
# ===================================================================

@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
@geo_limiter.limiter.limit(geo_limiter.get_limit("delete"))
async def soft_delete_field(
    request: Request,
    field_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Soft delete field (set deleted_at timestamp)

    - Preserves data for audit
    - Can be restored
    """

    field = db.query(models.Field).filter(
        and_(
            models.Field.id == field_id,
            models.Field.tenant_id == current_user.tenant_id
        )
    ).first()

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    # Soft delete
    field.soft_delete()
    db.commit()

    # Audit log
    audit_logger.log_access(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        action="soft_delete",
        resource=f"fields/{field_id}",
        details={"field_name": field.name}
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ===================================================================
# RESTORE DELETED FIELD
# ===================================================================

@router.post("/{field_id}/restore")
@geo_limiter.limiter.limit(geo_limiter.get_limit("update"))
async def restore_field(
    request: Request,
    field_id: str,
    current_user: TokenData = Depends(require_permission("fields:restore")),
    db: Session = Depends(get_db),
):
    """
    Restore soft-deleted field

    - Requires special permission
    """

    field = db.query(models.Field).filter(
        and_(
            models.Field.id == field_id,
            models.Field.tenant_id == current_user.tenant_id,
            models.Field.deleted_at.isnot(None)
        )
    ).first()

    if not field:
        raise HTTPException(status_code=404, detail="Deleted field not found")

    # Restore
    field.restore()
    db.commit()

    # Audit log
    audit_logger.log_access(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        action="restore",
        resource=f"fields/{field_id}",
        details={"field_name": field.name}
    )

    return {"message": "Field restored successfully", "field_id": str(field.id)}
