"""
Pytest configuration for Weather Core tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_field_id():
    """Sample field ID for testing"""
    return 1


@pytest.fixture
def sample_date():
    """Sample date for testing"""
    return "2024-06-15"
