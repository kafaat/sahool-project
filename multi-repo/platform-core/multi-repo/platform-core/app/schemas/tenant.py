from pydantic import BaseModel, ConfigDict


class TenantBase(BaseModel):
    code: str
    name: str


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class TenantInDBBase(TenantBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class Tenant(TenantInDBBase):
    pass