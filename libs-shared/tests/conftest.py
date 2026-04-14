"""
Pytest Configuration and Fixtures
إعدادات Pytest والـ Fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator
from uuid import uuid4

import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_tenant_id() -> str:
    """Generate sample tenant ID."""
    return str(uuid4())


@pytest.fixture
def sample_user_id() -> str:
    """Generate sample user ID."""
    return str(uuid4())


@pytest.fixture
def sample_field_id() -> str:
    """Generate sample field ID."""
    return str(uuid4())


@pytest.fixture
def jwt_secret() -> str:
    """JWT secret for testing."""
    return "test-jwt-secret-key-for-testing-only"


@pytest.fixture
def sample_coordinates() -> dict:
    """Sample Yemen coordinates (Sanaa)."""
    return {
        "latitude": 15.3694,
        "longitude": 44.1910
    }
