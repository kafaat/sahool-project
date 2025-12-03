"""
Database Connection Manager
مدير اتصال قاعدة البيانات
"""

import os
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from sahool_shared.models.base import Base


class DatabaseManager:
    """
    Database connection manager with support for sync and async sessions.
    مدير اتصال قاعدة البيانات مع دعم الجلسات المتزامنة وغير المتزامنة
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        async_database_url: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
        echo: bool = False,
    ):
        """
        Initialize database manager.

        Args:
            database_url: Sync database URL (postgresql://...)
            async_database_url: Async database URL (postgresql+asyncpg://...)
            pool_size: Connection pool size
            max_overflow: Max overflow connections
            pool_timeout: Pool timeout in seconds
            pool_recycle: Recycle connections after seconds
            echo: Enable SQL echo for debugging
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/sahool"
        )
        self.async_database_url = async_database_url or os.getenv(
            "ASYNC_DATABASE_URL",
            self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        )

        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo

        self._engine: Optional[Engine] = None
        self._async_engine = None
        self._session_factory: Optional[sessionmaker] = None
        self._async_session_factory = None

    @property
    def engine(self) -> Engine:
        """Get or create sync engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.database_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                echo=self.echo,
            )
            # Enable foreign key checks for PostgreSQL
            @event.listens_for(self._engine, "connect")
            def set_search_path(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("SET search_path TO public")
                cursor.close()

        return self._engine

    @property
    def async_engine(self):
        """Get or create async engine."""
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                self.async_database_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                echo=self.echo,
            )
        return self._async_engine

    @property
    def session_factory(self) -> sessionmaker:
        """Get or create sync session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
        return self._session_factory

    @property
    def async_session_factory(self) -> async_sessionmaker:
        """Get or create async session factory."""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
                class_=AsyncSession,
            )
        return self._async_session_factory

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a sync database session.

        Usage:
            with db_manager.get_session() as session:
                session.query(User).all()
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session.

        Usage:
            async with db_manager.get_async_session() as session:
                await session.execute(select(User))
        """
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def create_tables(self) -> None:
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all tables in the database."""
        Base.metadata.drop_all(bind=self.engine)

    async def create_tables_async(self) -> None:
        """Create all tables asynchronously."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables_async(self) -> None:
        """Drop all tables asynchronously."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    def close(self) -> None:
        """Close all connections."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
        if self._async_engine:
            # Async engine needs to be closed asynchronously
            pass

    async def close_async(self) -> None:
        """Close all async connections."""
        if self._async_engine:
            await self._async_engine.dispose()
            self._async_engine = None


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for sync database session.

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db_session)):
            return db.query(User).all()
    """
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        yield session


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async database session.

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_async_db_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    db_manager = get_db_manager()
    async with db_manager.get_async_session() as session:
        yield session


def create_tables() -> None:
    """Create all database tables."""
    get_db_manager().create_tables()


def drop_tables() -> None:
    """Drop all database tables."""
    get_db_manager().drop_tables()
