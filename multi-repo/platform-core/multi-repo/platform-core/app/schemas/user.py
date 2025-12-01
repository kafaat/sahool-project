from pydantic import BaseModel, ConfigDict, EmailStr


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

    model_config = ConfigDict(from_attributes=True)


class User(UserInDBBase):
    pass