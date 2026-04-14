"""
Database Utilities - Sahool Agricultural Platform
Database connection, session management, and utilities
"""

import os
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/sahool"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    poolclass=pool.QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False,          # Set to True for SQL logging
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    
    Usage in FastAPI:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database session
    
    Usage:
        with get_db_context() as db:
            users = db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def drop_db():
    """Drop all tables - USE WITH CAUTION!"""
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")


def check_db_connection() -> bool:
    """Check if database connection is healthy"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


class DatabaseManager:
    """Database manager for advanced operations"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def execute_raw(self, query: str, params: Optional[dict] = None):
        """Execute raw SQL query"""
        with self.engine.connect() as conn:
            result = conn.execute(query, params or {})
            return result.fetchall()
    
    def backup_table(self, table_name: str, backup_name: str):
        """Create a backup of a table"""
        query = f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name}"
        with self.engine.connect() as conn:
            conn.execute(query)
        logger.info(f"Table {table_name} backed up to {backup_name}")
    
    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table"""
        query = f"SELECT COUNT(*) FROM {table_name}"
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return result.scalar()


# Event listeners for connection pool
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Event listener for new connections"""
    logger.debug("New database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Event listener for connection checkout"""
    logger.debug("Database connection checked out from pool")


# Pagination helper
class Paginator:
    """Helper class for pagination"""
    
    @staticmethod
    def paginate(query, page: int = 1, page_size: int = 20):
        """
        Paginate a SQLAlchemy query
        
        Args:
            query: SQLAlchemy query object
            page: Page number (1-indexed)
            page_size: Number of items per page
        
        Returns:
            dict with items, total, page, page_size, total_pages
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }


# Export commonly used items
__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "get_db_context",
    "init_db",
    "drop_db",
    "check_db_connection",
    "DatabaseManager",
    "Paginator"
]
