from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app import schemas
from app.services.tenant_service import get_tenant, get_tenant_by_code, create_tenant

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.post("", response_model=schemas.Tenant, status_code=201)
def create_tenant_endpoint(
    tenant_in: schemas.TenantCreate,
    db: Session = Depends(get_db),
):
    if get_tenant_by_code(db, tenant_in.code):
        raise HTTPException(status_code=400, detail="Tenant code already exists")
    tenant = create_tenant(db, tenant_in)
    return tenant