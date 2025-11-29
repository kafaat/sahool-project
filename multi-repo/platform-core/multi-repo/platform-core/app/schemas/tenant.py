from pydantic import BaseModel


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

    class Config:
        orm_mode = True


class Tenant(TenantInDBBase):
    pass