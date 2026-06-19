"""
Pytest configuration and fixtures
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use SQLite for testing
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.models import Base, engine


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database after each test"""
    yield
    # Clean up logic here if needed
