"""
Database Utilities
أدوات قاعدة البيانات
"""

import os
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import text

from sahool_shared.models.base import Base


class DatabaseManager:
    """
    Database manager for async SQLAlchemy operations.
    مدير قاعدة البيانات لعمليات SQLAlchemy غير المتزامنة
    """

    def __init__(
        self,
        url: Optional[str] = None,
        pool_size: int = 20,
        max_overflow: int = 50,
        pool_recycle: int = 3600,
        echo: bool = False,
    ):
        self.url = url or os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://sahool:sahool@localhost:5432/sahool_db"
        )

        # Ensure we use asyncpg driver
        if self.url.startswith("postgresql://"):
            self.url = self.url.replace("postgresql://", "postgresql+asyncpg://")

        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.echo = echo

    async def connect(self) -> None:
        """Create database engine and session factory."""
        if self._engine is not None:
            return

        self._engine = create_async_engine(
            self.url,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,
            echo=self.echo,
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def disconnect(self) -> None:
        """Close database engine."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @property
    def engine(self) -> AsyncEngine:
        """Get database engine."""
        if self._engine is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get session factory."""
        if self._session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def create_tables(self) -> None:
        """Create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def health_check(self) -> dict:
        """Check database health."""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


# Global database manager
_db_manager: Optional[DatabaseManager] = None


async def get_db_manager() -> DatabaseManager:
    """Get or create global database manager."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.connect()
    return _db_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database session.
    تبعية FastAPI لجلسة قاعدة البيانات

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    manager = await get_db_manager()
    async with manager.session() as session:
        yield session
