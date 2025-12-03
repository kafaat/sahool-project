"""
Pytest configuration for Field Suite Backend tests
سهول اليمن - إعدادات الاختبارات
"""
import pytest
import os
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# Set test environment variables
os.environ.setdefault("IMAGERY_CORE_BASE_URL", "http://imagery-core:8000")
os.environ.setdefault("ANALYTICS_CORE_BASE_URL", "http://analytics-core:8000")
os.environ.setdefault("GEO_CORE_BASE_URL", "http://geo-core:8000")
os.environ.setdefault("WEATHER_CORE_BASE_URL", "http://weather-core:8000")
os.environ.setdefault("ADVISOR_CORE_BASE_URL", "http://advisor-core:8000")
os.environ.setdefault("QUERY_CORE_BASE_URL", "http://query-core:8000")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("API_KEY_SECRET", "test-api-key")


@pytest.fixture
def client():
    """Create test client"""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_http_client():
    """Mock httpx client for external service calls"""
    with patch("app.main.http_client") as mock:
        mock.get = AsyncMock()
        mock.post = AsyncMock()
        yield mock


@pytest.fixture
def sample_field_id():
    """Sample field ID"""
    return 1


@pytest.fixture
def sample_region_id():
    """Sample region ID"""
    return 1


@pytest.fixture
def yemen_governorates():
    """List of Yemen governorates"""
    return [
        "صنعاء", "عدن", "تعز", "حضرموت", "الحديدة",
        "إب", "ذمار", "شبوة", "لحج", "أبين",
        "مأرب", "الجوف", "عمران", "حجة", "المحويت",
        "ريمة", "المهرة", "سقطرى", "البيضاء", "صعدة"
    ]


@pytest.fixture
def yemen_crops():
    """List of Yemen crops"""
    return [
        "قمح", "ذرة", "شعير", "بن", "طماطم",
        "بصل", "بطاطس", "خضروات", "فواكه", "أعلاف"
    ]
