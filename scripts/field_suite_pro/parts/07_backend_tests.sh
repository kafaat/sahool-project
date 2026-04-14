#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Part 7: Backend Tests
# ═══════════════════════════════════════════════════════════════════════════════

log_info "إنشاء الاختبارات..."

# ─────────────────────────────────────────────────────────────────────────────
# Pytest Configuration
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/pytest.ini" << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --cov=app --cov-report=term-missing --cov-report=html
filterwarnings =
    ignore::DeprecationWarning
EOF

cat > "$PROJECT_NAME/backend/conftest.py" << 'EOF'
"""
Pytest Configuration and Fixtures
إعدادات ومثبتات Pytest
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.core.security import hash_password

# Test database URL
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    settings.POSTGRES_DB,
    f"{settings.POSTGRES_DB}_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("Test123!"),
        full_name="Test User",
        tenant_id=1,
        role=UserRole.MANAGER,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(test_user: User) -> dict:
    """Get authentication headers"""
    from app.core.security import create_access_token

    token = create_access_token(
        subject=str(test_user.id),
        extra_data={
            "email": test_user.email,
            "tenant_id": test_user.tenant_id,
            "role": test_user.role.value
        }
    )
    return {"Authorization": f"Bearer {token}"}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests - Auth
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/tests/unit/test_auth.py" << 'EOF'
"""
Authentication Unit Tests
اختبارات وحدة المصادقة
"""
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)


class TestPasswordHashing:
    """Tests for password hashing"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "SecurePass123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "SecurePass123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "SecurePass123!"
        hashed = hash_password(password)

        assert verify_password("WrongPassword", hashed) is False


class TestJWT:
    """Tests for JWT token handling"""

    def test_create_access_token(self):
        """Test creating access token"""
        token = create_access_token(
            subject="123",
            extra_data={"email": "test@example.com"}
        )

        assert token is not None
        assert len(token) > 50

    def test_create_refresh_token(self):
        """Test creating refresh token"""
        token = create_refresh_token(subject="123")

        assert token is not None
        assert len(token) > 50

    def test_decode_valid_token(self):
        """Test decoding valid token"""
        token = create_access_token(
            subject="123",
            extra_data={"email": "test@example.com"}
        )

        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"

    def test_decode_invalid_token(self):
        """Test decoding invalid token"""
        payload = decode_token("invalid.token.here")

        assert payload is None

    def test_decode_refresh_token(self):
        """Test decoding refresh token"""
        token = create_refresh_token(subject="456")

        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "456"
        assert payload["type"] == "refresh"
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests - Services
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/tests/unit/test_advisor_service.py" << 'EOF'
"""
Advisor Service Unit Tests
اختبارات خدمة المستشار
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.advisor_service import AdvisorService
from app.schemas.advisor import (
    FieldContext, NDVIContext, WeatherContext, CropContext
)


class TestAdvisorRules:
    """Tests for advisor rules evaluation"""

    @pytest.fixture
    def advisor_service(self):
        """Create advisor service with mocked dependencies"""
        db = AsyncMock()
        redis = MagicMock()
        return AdvisorService(db, redis)

    def test_critical_low_ndvi_triggers(self, advisor_service):
        """Test that critical low NDVI triggers recommendation"""
        context = FieldContext(
            field_id=1,
            field_name="Test Field",
            tenant_id=1,
            ndvi=NDVIContext(mean=0.15, min=0.1, max=0.2, std=0.05, zones={}),
            weather=WeatherContext(
                temperature_max=30, temperature_min=20, temperature_mean=25,
                humidity=50, precipitation_mm=0, wind_speed=10
            ),
            crop=CropContext(crop_type="wheat")
        )

        # Find rule
        rule = next(r for r in advisor_service.rules if r["name"] == "critical_low_ndvi")
        result = advisor_service._evaluate_conditions(rule["conditions"], context)

        assert result is True

    def test_normal_ndvi_no_trigger(self, advisor_service):
        """Test that normal NDVI doesn't trigger critical alert"""
        context = FieldContext(
            field_id=1,
            field_name="Test Field",
            tenant_id=1,
            ndvi=NDVIContext(mean=0.65, min=0.5, max=0.8, std=0.1, zones={}),
            weather=WeatherContext(
                temperature_max=30, temperature_min=20, temperature_mean=25,
                humidity=50, precipitation_mm=0, wind_speed=10
            ),
            crop=CropContext(crop_type="wheat")
        )

        # Find rule
        rule = next(r for r in advisor_service.rules if r["name"] == "critical_low_ndvi")
        result = advisor_service._evaluate_conditions(rule["conditions"], context)

        assert result is False

    def test_high_temperature_triggers_alert(self, advisor_service):
        """Test that high temperature triggers heat stress alert"""
        context = FieldContext(
            field_id=1,
            field_name="Test Field",
            tenant_id=1,
            ndvi=NDVIContext(mean=0.6, min=0.5, max=0.7, std=0.1, zones={}),
            weather=WeatherContext(
                temperature_max=42, temperature_min=28, temperature_mean=35,
                humidity=30, precipitation_mm=0, wind_speed=15
            ),
            crop=CropContext(crop_type="wheat")
        )

        rule = next(r for r in advisor_service.rules if r["name"] == "high_temp_stress")
        result = advisor_service._evaluate_conditions(rule["conditions"], context)

        assert result is True

    def test_health_score_calculation(self, advisor_service):
        """Test health score calculation"""
        context = FieldContext(
            field_id=1,
            field_name="Test Field",
            tenant_id=1,
            ndvi=NDVIContext(mean=0.7, min=0.6, max=0.8, std=0.05, zones={}),
            weather=WeatherContext(
                temperature_max=28, temperature_min=18, temperature_mean=23,
                humidity=60, precipitation_mm=5, wind_speed=8
            ),
            crop=CropContext(crop_type="wheat")
        )

        score = advisor_service._calculate_health_score(context)

        # NDVI 0.7 = 70 points, optimal temp = 100 points, avg = 85
        assert 80 <= score <= 90
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests - API
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/tests/integration/test_api_auth.py" << 'EOF'
"""
Authentication API Integration Tests
اختبارات تكامل API المصادقة
"""
import pytest
from httpx import AsyncClient


class TestAuthAPI:
    """Tests for authentication endpoints"""

    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient):
        """Test user registration"""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User",
            "tenant_id": 1
        })

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with existing email"""
        response = await client.post("/api/v1/auth/register", json={
            "email": test_user.email,
            "password": "SecurePass123!",
            "full_name": "Another User",
            "tenant_id": 1
        })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login"""
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "Test123!"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient, test_user):
        """Test login with invalid credentials"""
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "WrongPassword"
        })

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """Test getting current user info"""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "full_name" in data

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test accessing protected endpoint without auth"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
EOF

cat > "$PROJECT_NAME/backend/tests/integration/test_api_fields.py" << 'EOF'
"""
Fields API Integration Tests
اختبارات تكامل API الحقول
"""
import pytest
from httpx import AsyncClient


class TestFieldsAPI:
    """Tests for fields endpoints"""

    @pytest.fixture
    def sample_field_data(self):
        """Sample field data for tests"""
        return {
            "name": "Test Field",
            "description": "A test field for integration tests",
            "crop_type": "wheat",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[35.0, 31.0], [35.1, 31.0], [35.1, 31.1], [35.0, 31.1], [35.0, 31.0]]]
            }
        }

    @pytest.mark.asyncio
    async def test_create_field(self, client: AsyncClient, auth_headers, sample_field_data):
        """Test creating a field"""
        response = await client.post(
            "/api/v1/fields",
            json=sample_field_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_field_data["name"]
        assert "id" in data
        assert "uuid" in data

    @pytest.mark.asyncio
    async def test_list_fields(self, client: AsyncClient, auth_headers):
        """Test listing fields"""
        response = await client.get(
            "/api/v1/fields",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    @pytest.mark.asyncio
    async def test_list_fields_pagination(self, client: AsyncClient, auth_headers):
        """Test field list pagination"""
        response = await client.get(
            "/api/v1/fields?page=1&page_size=5",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    @pytest.mark.asyncio
    async def test_get_nonexistent_field(self, client: AsyncClient, auth_headers):
        """Test getting a field that doesn't exist"""
        response = await client.get(
            "/api/v1/fields/99999",
            headers=auth_headers
        )

        assert response.status_code == 404
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Tests Init
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/backend/tests/__init__.py" << 'EOF'
"""Test package"""
EOF

cat > "$PROJECT_NAME/backend/tests/unit/__init__.py" << 'EOF'
"""Unit tests"""
EOF

cat > "$PROJECT_NAME/backend/tests/integration/__init__.py" << 'EOF'
"""Integration tests"""
EOF

log_success "تم إنشاء الاختبارات"
