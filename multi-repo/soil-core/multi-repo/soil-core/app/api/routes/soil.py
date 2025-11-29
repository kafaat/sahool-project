from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.soil import SoilSampleCreate, SoilSampleOut, SoilFieldSummary
from app.services.soil_service import create_sample, list_samples, field_summary

router = APIRouter(prefix="/api/v1/soil", tags=["soil"])

@router.post("/samples", response_model=SoilSampleOut, status_code=201)
def create_sample_endpoint(
    sample_in: SoilSampleCreate,
    db: Session = Depends(get_db),
):
    return create_sample(db, sample_in)

@router.get("/samples", response_model=List[SoilSampleOut])
def list_samples_endpoint(
    tenant_id: int = Query(...),
    field_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    return list_samples(db, tenant_id, field_id)

@router.get("/fields/{field_id}/summary", response_model=SoilFieldSummary)
def field_summary_endpoint(
    field_id: int,
    tenant_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return field_summary(db, tenant_id, field_id)