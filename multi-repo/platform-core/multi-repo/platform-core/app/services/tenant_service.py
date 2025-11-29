from sqlalchemy.orm import Session
from app import models, schemas


def get_tenant(db: Session, tenant_id: int) -> models.Tenant | None:
    return db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()


def get_tenant_by_code(db: Session, code: str) -> models.Tenant | None:
    return db.query(models.Tenant).filter(models.Tenant.code == code).first()


def create_tenant(db: Session, tenant_in: schemas.TenantCreate) -> models.Tenant:
    tenant = models.Tenant(code=tenant_in.code, name=tenant_in.name, is_active=True)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant