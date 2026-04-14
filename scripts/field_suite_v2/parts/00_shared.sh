#!/bin/bash
# ==============================================================================
# Part 00: Shared Modules
# Common utilities, schemas, and configurations
# ==============================================================================

generate_shared() {
    log_info "Creating shared modules..."

    mkdir -p shared/{schemas,utils,config}

    # ------------------------------------------------------------------------------
    # Shared Config
    # ------------------------------------------------------------------------------
    write_heredoc "shared/config/settings.py" << 'PYEOF'
"""
Shared Settings - Base configuration for all services
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class BaseServiceSettings(BaseSettings):
    """Base settings inherited by all services"""

    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    SERVICE_NAME: str = "base-service"

    # Database
    POSTGRES_USER: str = "fieldsuite"
    POSTGRES_PASSWORD: str = "fieldsuite_secret"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "fieldsuite_db"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"
        extra = "allow"
PYEOF

    # ------------------------------------------------------------------------------
    # Shared Database Module (FIXED - proper async handling)
    # ------------------------------------------------------------------------------
    write_heredoc "shared/utils/database.py" << 'PYEOF'
"""
Database utilities - Async SQLAlchemy setup
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class DatabaseManager:
    """Manages database connections with proper async handling"""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional scope around operations"""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependency for FastAPI"""
        async with self.session() as session:
            yield session

    async def create_tables(self):
        """Create all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        """Close engine"""
        await self.engine.dispose()
PYEOF

    # ------------------------------------------------------------------------------
    # Redis Client (FIXED - Singleton pattern)
    # ------------------------------------------------------------------------------
    write_heredoc "shared/utils/cache.py" << 'PYEOF'
"""
Redis Cache - Singleton connection pool
"""
from typing import Optional, Any
import json
import redis.asyncio as redis


class RedisClient:
    """Singleton Redis client with connection pooling"""

    _instance: Optional["RedisClient"] = None
    _pool: Optional[redis.ConnectionPool] = None

    def __new__(cls, redis_url: str = "redis://redis:6379/0"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._pool = redis.ConnectionPool.from_url(
                redis_url,
                max_connections=20,
                decode_responses=True,
            )
        return cls._instance

    @property
    def client(self) -> redis.Redis:
        return redis.Redis(connection_pool=self._pool)

    async def get(self, key: str) -> Optional[str]:
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        expire: int = 3600
    ) -> bool:
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await self.client.set(key, value, ex=expire)

    async def delete(self, key: str) -> int:
        return await self.client.delete(key)

    async def get_json(self, key: str) -> Optional[dict]:
        data = await self.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_json(
        self,
        key: str,
        value: dict,
        expire: int = 3600
    ) -> bool:
        return await self.set(key, json.dumps(value), expire)

    async def close(self):
        if self._pool:
            await self._pool.disconnect()


# Global instance (lazy initialization)
_redis_client: Optional[RedisClient] = None


def get_redis(redis_url: str = "redis://redis:6379/0") -> RedisClient:
    """Get or create Redis client singleton"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient(redis_url)
    return _redis_client
PYEOF

    # ------------------------------------------------------------------------------
    # JWT Utilities (FIXED - Real JWT implementation)
    # ------------------------------------------------------------------------------
    write_heredoc "shared/utils/security.py" << 'PYEOF'
"""
Security utilities - JWT, password hashing
"""
from datetime import datetime, timedelta
from typing import Optional, Any

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str
    exp: datetime
    iat: datetime
    type: str
    tenant_id: Optional[str] = None
    roles: list[str] = []


class TokenPair(BaseModel):
    """Access and refresh token pair"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_token(
    subject: str,
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: timedelta = timedelta(minutes=30),
    token_type: str = "access",
    extra_claims: dict[str, Any] = None,
) -> str:
    """Create a JWT token"""
    now = datetime.utcnow()
    expire = now + expires_delta

    payload = {
        "sub": subject,
        "exp": expire,
        "iat": now,
        "type": token_type,
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_token_pair(
    subject: str,
    secret_key: str,
    algorithm: str = "HS256",
    access_expire_minutes: int = 30,
    refresh_expire_days: int = 7,
    extra_claims: dict[str, Any] = None,
) -> TokenPair:
    """Create access and refresh token pair"""
    access_token = create_token(
        subject=subject,
        secret_key=secret_key,
        algorithm=algorithm,
        expires_delta=timedelta(minutes=access_expire_minutes),
        token_type="access",
        extra_claims=extra_claims,
    )

    refresh_token = create_token(
        subject=subject,
        secret_key=secret_key,
        algorithm=algorithm,
        expires_delta=timedelta(days=refresh_expire_days),
        token_type="refresh",
        extra_claims=extra_claims,
    )

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def decode_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
) -> Optional[TokenPayload]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return TokenPayload(**payload)
    except JWTError:
        return None
PYEOF

    # ------------------------------------------------------------------------------
    # Shared Schemas (Pydantic models)
    # ------------------------------------------------------------------------------
    write_heredoc "shared/schemas/__init__.py" << 'PYEOF'
"""Shared schemas for all services"""
from .base import *
from .user import *
from .field import *
from .ndvi import *
from .advisor import *
PYEOF

    write_heredoc "shared/schemas/base.py" << 'PYEOF'
"""Base schemas"""
from datetime import datetime
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common config"""
    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TenantMixin(BaseModel):
    """Mixin for multi-tenant fields"""
    tenant_id: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime
PYEOF

    write_heredoc "shared/schemas/user.py" << 'PYEOF'
"""User schemas"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from .base import BaseSchema, TimestampMixin


class UserBase(BaseModel):
    """Base user fields"""
    email: EmailStr
    full_name: str
    tenant_id: str


class UserCreate(UserBase):
    """User creation schema"""
    password: str
    roles: List[str] = ["viewer"]


class UserLogin(BaseModel):
    """Login request"""
    email: EmailStr
    password: str


class UserResponse(UserBase, TimestampMixin, BaseSchema):
    """User response"""
    id: int
    is_active: bool
    roles: List[str]


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
PYEOF

    write_heredoc "shared/schemas/field.py" << 'PYEOF'
"""Field schemas"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field as PydanticField
from .base import BaseSchema, TimestampMixin, TenantMixin


class Coordinate(BaseModel):
    """Geographic coordinate"""
    lat: float = PydanticField(..., ge=-90, le=90)
    lng: float = PydanticField(..., ge=-180, le=180)


class GeoJSONPolygon(BaseModel):
    """GeoJSON Polygon"""
    type: str = "Polygon"
    coordinates: List[List[List[float]]]


class FieldBase(BaseModel):
    """Base field fields"""
    name: str = PydanticField(..., min_length=1, max_length=200)
    description: Optional[str] = None
    crop_type: Optional[str] = None
    area_hectares: Optional[float] = PydanticField(None, gt=0)


class FieldCreate(FieldBase, TenantMixin):
    """Field creation schema"""
    geometry: GeoJSONPolygon


class FieldUpdate(BaseModel):
    """Field update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    crop_type: Optional[str] = None


class FieldResponse(FieldBase, TimestampMixin, TenantMixin, BaseSchema):
    """Field response"""
    id: int
    geometry: Optional[Dict[str, Any]] = None
    center: Optional[Coordinate] = None
PYEOF

    write_heredoc "shared/schemas/ndvi.py" << 'PYEOF'
"""NDVI schemas"""
from datetime import date, datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from .base import BaseSchema, TimestampMixin


class NDVIZone(BaseModel):
    """NDVI zone classification"""
    zone: str
    min_value: float
    max_value: float
    area_percentage: float
    health_status: str


class NDVIRequest(BaseModel):
    """NDVI computation request"""
    field_ids: List[int]
    target_date: Optional[date] = None
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None


class NDVIResponse(TimestampMixin, BaseSchema):
    """NDVI result response"""
    id: int
    field_id: int
    capture_date: date
    mean_ndvi: float
    min_ndvi: float
    max_ndvi: float
    std_ndvi: float
    cloud_coverage: float
    zones: List[NDVIZone]
    health_score: float = Field(..., ge=0, le=100)


class NDVIJobResponse(BaseModel):
    """NDVI job status"""
    job_id: str
    status: str
    progress: int = 0
    message: Optional[str] = None
    result: Optional[NDVIResponse] = None


class NDVITimelineResponse(BaseModel):
    """NDVI timeline for a field"""
    field_id: int
    results: List[NDVIResponse]
    trend: str  # improving, declining, stable
    average_health_score: float
PYEOF

    write_heredoc "shared/schemas/advisor.py" << 'PYEOF'
"""Advisor schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from .base import BaseSchema, TimestampMixin


class RecommendationType(str, Enum):
    IRRIGATION = "irrigation"
    FERTILIZATION = "fertilization"
    PEST_CONTROL = "pest_control"
    HARVEST = "harvest"
    GENERAL = "general"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationBase(BaseModel):
    """Base recommendation fields"""
    type: RecommendationType
    priority: Priority
    title: str
    description: str
    action_required: str
    expected_impact: str
    estimated_cost: Optional[float] = None


class RecommendationResponse(RecommendationBase, TimestampMixin, BaseSchema):
    """Recommendation response"""
    id: int
    field_id: int
    is_applied: bool = False
    applied_at: Optional[datetime] = None
    confidence_score: float = Field(..., ge=0, le=1)
    supporting_data: Optional[Dict[str, Any]] = None


class AdvisorAnalysisRequest(BaseModel):
    """Advisor analysis request"""
    field_ids: List[int]
    include_weather: bool = True
    include_ndvi: bool = True
    include_historical: bool = True


class AdvisorAnalysisResponse(BaseModel):
    """Advisor analysis response"""
    field_id: int
    analysis_date: datetime
    overall_health_score: float
    recommendations: List[RecommendationResponse]
    alerts: List[Dict[str, Any]]
    next_actions: List[str]
PYEOF

    # ------------------------------------------------------------------------------
    # Shared Utils Init
    # ------------------------------------------------------------------------------
    write_heredoc "shared/utils/__init__.py" << 'PYEOF'
"""Shared utilities"""
from .database import DatabaseManager, Base
from .cache import RedisClient, get_redis
from .security import (
    hash_password,
    verify_password,
    create_token,
    create_token_pair,
    decode_token,
    TokenPayload,
    TokenPair,
)
PYEOF

    write_heredoc "shared/__init__.py" << 'PYEOF'
"""Shared module"""
PYEOF

    write_heredoc "shared/config/__init__.py" << 'PYEOF'
"""Config module"""
from .settings import BaseServiceSettings
PYEOF

    # ------------------------------------------------------------------------------
    # pyproject.toml for shared package
    # ------------------------------------------------------------------------------
    write_heredoc "shared/pyproject.toml" << 'TOMLEOF'
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "field-suite-shared"
version = "1.0.0"
description = "Shared modules for Field Suite Platform"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "redis>=5.0.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
]

[tool.setuptools.packages.find]
include = ["shared*"]
TOMLEOF

    log_success "Shared modules created"
}
