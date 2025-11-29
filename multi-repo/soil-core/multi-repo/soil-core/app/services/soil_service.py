from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.soil_sample import SoilSample
from app.schemas.soil import SoilSampleCreate, SoilFieldSummary

def create_sample(db: Session, sample_in: SoilSampleCreate) -> SoilSample:
    sample = SoilSample(
        tenant_id=sample_in.tenant_id,
        field_id=sample_in.field_id,
        sample_date=sample_in.sample_date,
        depth_cm=sample_in.depth_cm,
        ph=sample_in.ph,
        ec_ds_m=sample_in.ec_ds_m,
        moisture_pct=sample_in.moisture_pct,
        organic_matter_pct=sample_in.organic_matter_pct,
        lab_ref=sample_in.lab_ref,
        notes=sample_in.notes,
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample

def list_samples(db: Session, tenant_id: int, field_id: Optional[int] = None) -> List[SoilSample]:
    q = db.query(SoilSample).filter(SoilSample.tenant_id == tenant_id)
    if field_id is not None:
        q = q.filter(SoilSample.field_id == field_id)
    return q.order_by(SoilSample.sample_date.desc(), SoilSample.id.desc()).all()

def field_summary(db: Session, tenant_id: int, field_id: int) -> SoilFieldSummary:
    q = (
        db.query(
            func.count(SoilSample.id),
            func.avg(SoilSample.ph),
            func.avg(SoilSample.ec_ds_m),
            func.avg(SoilSample.moisture_pct),
            func.avg(SoilSample.organic_matter_pct),
        )
        .filter(SoilSample.tenant_id == tenant_id, SoilSample.field_id == field_id)
    )
    count, ph_avg, ec_avg, moisture_avg, om_avg = q.one()
    return SoilFieldSummary(
        field_id=field_id,
        tenant_id=tenant_id,
        samples_count=count or 0,
        ph_avg=ph_avg,
        ec_avg=ec_avg,
        moisture_avg=moisture_avg,
        organic_matter_avg=om_avg,
    )