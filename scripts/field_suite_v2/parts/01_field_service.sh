#!/bin/bash
# ==============================================================================
# Part 01: Field Service
# Microservice for field management with GIS support
# ==============================================================================

generate_field_service() {
    log_info "Creating Field Service..."

    local SERVICE_DIR="services/field-service"
    mkdir -p "$SERVICE_DIR"/{app/{api,models,services,core},tests,alembic/versions}

    # ------------------------------------------------------------------------------
    # Service Configuration
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/core/config.py" << 'PYEOF'
"""Field Service Configuration"""
from functools import lru_cache
import sys
sys.path.insert(0, "/app/shared")

from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Field service specific settings"""
    SERVICE_NAME: str = "field-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8001

    # Service URLs
    NDVI_SERVICE_URL: str = "http://ndvi-service:8002"
    ADVISOR_SERVICE_URL: str = "http://advisor-service:8003"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
PYEOF

    # ------------------------------------------------------------------------------
    # Database Dependencies
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/core/deps.py" << 'PYEOF'
"""Dependencies for Field Service"""
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sys
sys.path.insert(0, "/app/shared")

from shared.utils import DatabaseManager, get_redis, decode_token, TokenPayload
from .config import settings

# Security
security = HTTPBearer()

# Database manager (singleton)
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get database manager singleton"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(settings.DATABASE_URL)
    return _db_manager


async def get_db() -> AsyncGenerator:
    """Get database session"""
    db_manager = get_db_manager()
    async with db_manager.session() as session:
        yield session


async def get_cache():
    """Get Redis cache client"""
    return get_redis(settings.REDIS_URL)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    """Validate JWT and return user payload"""
    token = credentials.credentials

    payload = decode_token(
        token=token,
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    return payload


def require_roles(*allowed_roles: str):
    """Role-based access control dependency"""
    async def role_checker(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        if not any(role in current_user.roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_checker
PYEOF

    # ------------------------------------------------------------------------------
    # Field Model (FIXED - proper __init__ and async)
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/models/field.py" << 'PYEOF'
"""Field database model"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
import sys
sys.path.insert(0, "/app/shared")

from shared.utils import Base


class Field(Base):
    """Field model with GIS support"""

    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    crop_type = Column(String(100), nullable=True)
    area_hectares = Column(Float, nullable=True)

    # GIS
    geometry = Column(
        Geometry(geometry_type="POLYGON", srid=4326),
        nullable=True
    )
    center_lat = Column(Float, nullable=True)
    center_lng = Column(Float, nullable=True)

    # Metadata
    metadata_json = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_fields_tenant_crop", "tenant_id", "crop_type"),
        Index("ix_fields_geometry", "geometry", postgresql_using="gist"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        result = {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "crop_type": self.crop_type,
            "area_hectares": self.area_hectares,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if self.center_lat and self.center_lng:
            result["center"] = {"lat": self.center_lat, "lng": self.center_lng}

        return result
PYEOF

    write_heredoc "$SERVICE_DIR/app/models/__init__.py" << 'PYEOF'
"""Models module"""
from .field import Field
PYEOF

    # ------------------------------------------------------------------------------
    # Field Service (FIXED - proper async with SQLAlchemy)
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/services/field_service.py" << 'PYEOF'
"""Field Service - Business logic"""
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_AsGeoJSON, ST_Centroid, ST_Area
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
import json

from ..models.field import Field


class FieldService:
    """Service for field operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        tenant_id: str,
        name: str,
        geometry_geojson: dict,
        description: Optional[str] = None,
        crop_type: Optional[str] = None,
    ) -> Field:
        """Create a new field"""
        # Convert GeoJSON to Shapely geometry
        geom = shape(geometry_geojson)

        # Calculate center and area
        centroid = geom.centroid
        area_hectares = geom.area * 111319.9 * 111319.9 / 10000  # Approximate

        field = Field(
            tenant_id=tenant_id,
            name=name,
            description=description,
            crop_type=crop_type,
            geometry=from_shape(geom, srid=4326),
            center_lat=centroid.y,
            center_lng=centroid.x,
            area_hectares=area_hectares,
        )

        self.db.add(field)
        await self.db.flush()
        await self.db.refresh(field)

        return field

    async def get_by_id(
        self,
        field_id: int,
        tenant_id: str,
    ) -> Optional[Field]:
        """Get field by ID"""
        result = await self.db.execute(
            select(Field).where(
                Field.id == field_id,
                Field.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        crop_type: Optional[str] = None,
    ) -> tuple[List[Field], int]:
        """Get all fields for a tenant with pagination"""
        query = select(Field).where(Field.tenant_id == tenant_id)

        if crop_type:
            query = query.where(Field.crop_type == crop_type)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Get page
        query = query.offset(skip).limit(limit).order_by(Field.created_at.desc())
        result = await self.db.execute(query)
        fields = result.scalars().all()

        return list(fields), total

    async def update(
        self,
        field_id: int,
        tenant_id: str,
        **updates,
    ) -> Optional[Field]:
        """Update a field"""
        field = await self.get_by_id(field_id, tenant_id)
        if not field:
            return None

        for key, value in updates.items():
            if value is not None and hasattr(field, key):
                setattr(field, key, value)

        await self.db.flush()
        await self.db.refresh(field)
        return field

    async def delete(
        self,
        field_id: int,
        tenant_id: str,
    ) -> bool:
        """Delete a field"""
        field = await self.get_by_id(field_id, tenant_id)
        if not field:
            return False

        await self.db.delete(field)
        return True

    async def get_geometry_geojson(
        self,
        field_id: int,
        tenant_id: str,
    ) -> Optional[dict]:
        """Get field geometry as GeoJSON"""
        result = await self.db.execute(
            select(ST_AsGeoJSON(Field.geometry)).where(
                Field.id == field_id,
                Field.tenant_id == tenant_id,
            )
        )
        geojson_str = result.scalar_one_or_none()
        if geojson_str:
            return json.loads(geojson_str)
        return None
PYEOF

    write_heredoc "$SERVICE_DIR/app/services/__init__.py" << 'PYEOF'
"""Services module"""
from .field_service import FieldService
PYEOF

    # ------------------------------------------------------------------------------
    # API Routes
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/api/fields.py" << 'PYEOF'
"""Field API endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import sys
sys.path.insert(0, "/app/shared")

from shared.schemas.field import (
    FieldCreate, FieldUpdate, FieldResponse, GeoJSONPolygon,
)
from shared.schemas.base import PaginatedResponse
from shared.utils import TokenPayload

from ..core.deps import get_db, get_current_user, require_roles
from ..services.field_service import FieldService

router = APIRouter(prefix="/fields", tags=["fields"])


@router.post("", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
async def create_field(
    data: FieldCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles("admin", "manager")),
):
    """Create a new field"""
    service = FieldService(db)

    # Validate tenant
    if data.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create field for another tenant",
        )

    field = await service.create(
        tenant_id=data.tenant_id,
        name=data.name,
        geometry_geojson=data.geometry.model_dump(),
        description=data.description,
        crop_type=data.crop_type,
    )

    return field.to_dict()


@router.get("", response_model=PaginatedResponse[FieldResponse])
async def list_fields(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    crop_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """List all fields for the current tenant"""
    service = FieldService(db)

    skip = (page - 1) * size
    fields, total = await service.get_all(
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=size,
        crop_type=crop_type,
    )

    return {
        "items": [f.to_dict() for f in fields],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/{field_id}", response_model=FieldResponse)
async def get_field(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get a specific field"""
    service = FieldService(db)

    field = await service.get_by_id(field_id, current_user.tenant_id)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    result = field.to_dict()

    # Include geometry if available
    geometry = await service.get_geometry_geojson(field_id, current_user.tenant_id)
    if geometry:
        result["geometry"] = geometry

    return result


@router.patch("/{field_id}", response_model=FieldResponse)
async def update_field(
    field_id: int,
    data: FieldUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles("admin", "manager")),
):
    """Update a field"""
    service = FieldService(db)

    field = await service.update(
        field_id=field_id,
        tenant_id=current_user.tenant_id,
        **data.model_dump(exclude_unset=True),
    )

    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )

    return field.to_dict()


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles("admin")),
):
    """Delete a field"""
    service = FieldService(db)

    deleted = await service.delete(field_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found",
        )
PYEOF

    write_heredoc "$SERVICE_DIR/app/api/__init__.py" << 'PYEOF'
"""API module"""
from .fields import router as fields_router
PYEOF

    # ------------------------------------------------------------------------------
    # Main Application (FIXED - proper imports and __name__ == "__main__")
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/app/main.py" << 'PYEOF'
"""Field Service - Main Application"""
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .core.config import settings
from .core.deps import get_db_manager
from .api import fields_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    db_manager = get_db_manager()
    await db_manager.create_tables()
    yield
    # Shutdown
    await db_manager.close()


app = FastAPI(
    title="Field Service",
    description="Agricultural Field Management Service",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc) if settings.DEBUG else "Internal server error",
            "path": str(request.url),
        },
    )


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


# Include routers
app.include_router(fields_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
PYEOF

    # ------------------------------------------------------------------------------
    # Dockerfile
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/Dockerfile" << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared module
COPY ../shared /app/shared

# Copy service code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
DOCKERFILE

    # ------------------------------------------------------------------------------
    # Requirements
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/requirements.txt" << 'REQEOF'
# FastAPI
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Database
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1
geoalchemy2==0.14.3

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Cache
redis==5.0.1

# Utils
httpx==0.26.0
python-multipart==0.0.6

# GIS
shapely==2.0.2

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
REQEOF

    # ------------------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------------------
    write_heredoc "$SERVICE_DIR/tests/__init__.py" << 'PYEOF'
"""Tests module"""
PYEOF

    write_heredoc "$SERVICE_DIR/tests/conftest.py" << 'PYEOF'
"""Test fixtures"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.deps import get_db
import sys
sys.path.insert(0, "/app/shared")
from shared.utils import Base


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_db"


@pytest_asyncio.fixture
async def test_db():
    """Create test database session"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    """Create test client"""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
PYEOF

    write_heredoc "$SERVICE_DIR/tests/test_fields.py" << 'PYEOF'
"""Field API tests"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "field-service"


@pytest.mark.asyncio
async def test_list_fields_unauthorized(client: AsyncClient):
    """Test list fields without auth"""
    response = await client.get("/api/v1/fields")
    assert response.status_code == 403  # No auth header
PYEOF

    log_success "Field Service created"
}
