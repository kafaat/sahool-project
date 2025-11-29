from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape

from app.db.session import get_db
from app import schemas
from app.services.field_service import list_fields, create_field, get_field, update_field, delete_field

router = APIRouter(prefix="/api/v1/fields", tags=["fields"])


@router.get("", response_model=List[schemas.FieldOut])
def list_fields_endpoint(
    tenant_id: int = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db),
):
    return list_fields(db, tenant_id)


@router.post("", response_model=schemas.FieldOut, status_code=201)
def create_field_endpoint(
    field_in: schemas.FieldCreate,
    db: Session = Depends(get_db),
):
    return create_field(db, field_in)


@router.get("/{field_id}", response_model=schemas.FieldOut)
def get_field_endpoint(
    field_id: int,
    tenant_id: int = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db),
):
    field = get_field(db, tenant_id, field_id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.put("/{field_id}", response_model=schemas.FieldOut)
def update_field_endpoint(
    field_id: int,
    field_in: schemas.FieldUpdate,
    tenant_id: int = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db),
):
    field = update_field(db, tenant_id, field_id, field_in)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.delete("/{field_id}", status_code=204)
def delete_field_endpoint(
    field_id: int,
    tenant_id: int = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db),
):
    ok = delete_field(db, tenant_id, field_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Field not found")
    return


@router.get("/{field_id}/boundary")
def get_field_boundary(
    field_id: int,
    tenant_id: int = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db),
):
    field = get_field(db, tenant_id, field_id)
    if not field or not field.geometry:
        raise HTTPException(status_code=404, detail="Field or geometry not found")

    geom = to_shape(field.geometry)
    centroid = geom.centroid
    # Leaflet expects [lat, lng]
    vertices = []
    if geom.geom_type == "Polygon":
        exterior = geom.exterior.coords
        vertices = [[float(y), float(x)] for (x, y) in exterior]
    elif geom.geom_type == "MultiPolygon":
        # take first polygon exterior
        poly = list(geom.geoms)[0]
        exterior = poly.exterior.coords
        vertices = [[float(y), float(x)] for (x, y) in exterior]

    return {
        "center": {"lat": float(centroid.y), "lng": float(centroid.x)},
        "vertices": vertices,
    }
