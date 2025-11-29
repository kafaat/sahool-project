from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str
    tenant_id: int


class UserUpdate(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None


class UserInDBBase(UserBase):
    id: int
    tenant_id: int

    class Config:
        orm_mode = True


class User(UserInDBBase):
    pass