"""
User Model - Sahool Agricultural Platform
Handles user data structure and validation
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    FARMER = "farmer"
    AGRONOMIST = "agronomist"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, regex=r'^\+?[1-9]\d{1,14}$')
    role: UserRole = UserRole.FARMER
    tenant_id: int


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str


class UserUpdate(BaseModel):
    """User update model - all fields optional"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, regex=r'^\+?[1-9]\d{1,14}$')
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserInDB(UserBase):
    """User model as stored in database"""
    id: int
    hashed_password: str
    status: UserStatus = UserStatus.PENDING
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool = False
    
    class Config:
        orm_mode = True


class UserResponse(BaseModel):
    """User response model (without sensitive data)"""
    id: int
    email: EmailStr
    full_name: str
    phone: Optional[str]
    role: UserRole
    status: UserStatus
    tenant_id: int
    created_at: datetime
    last_login: Optional[datetime]
    email_verified: bool
    
    class Config:
        orm_mode = True


class UserProfile(UserResponse):
    """Extended user profile with additional info"""
    fields_count: int = 0
    alerts_count: int = 0
    last_field_update: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Paginated user list response"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str


class EmailVerification(BaseModel):
    """Email verification"""
    token: str


# Database ORM Model (for SQLAlchemy)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.FARMER)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING)
    tenant_id = Column(Integer, nullable=False, index=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
"""
