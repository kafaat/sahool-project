"""
Base Repository Pattern
نمط المستودع الأساسي
"""

from typing import Any, Generic, Optional, Type, TypeVar
import uuid

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from sahool_shared.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository for CRUD operations.
    مستودع عام لعمليات CRUD
    """

    def __init__(self, model: Type[ModelType], session: Session | AsyncSession):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            session: Database session (sync or async)
        """
        self.model = model
        self.session = session

    # ============ Sync Methods ============

    def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        """Get record by ID."""
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[uuid.UUID] = None
    ) -> list[ModelType]:
        """Get all records with pagination."""
        query = self.session.query(self.model)
        if tenant_id and hasattr(self.model, 'tenant_id'):
            query = query.filter(self.model.tenant_id == tenant_id)
        return query.offset(skip).limit(limit).all()

    def get_by_tenant(
        self,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[ModelType]:
        """Get records by tenant ID."""
        return (
            self.session.query(self.model)
            .filter(self.model.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.flush()
        self.session.refresh(instance)
        return instance

    def update(self, id: uuid.UUID, **kwargs) -> Optional[ModelType]:
        """Update a record by ID."""
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            self.session.flush()
            self.session.refresh(instance)
        return instance

    def delete(self, id: uuid.UUID) -> bool:
        """Delete a record by ID."""
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.flush()
            return True
        return False

    def count(self, tenant_id: Optional[uuid.UUID] = None) -> int:
        """Count records."""
        query = self.session.query(func.count(self.model.id))
        if tenant_id and hasattr(self.model, 'tenant_id'):
            query = query.filter(self.model.tenant_id == tenant_id)
        return query.scalar() or 0

    def exists(self, id: uuid.UUID) -> bool:
        """Check if record exists."""
        return (
            self.session.query(self.model.id)
            .filter(self.model.id == id)
            .first() is not None
        )

    # ============ Async Methods ============

    async def get_by_id_async(self, id: uuid.UUID) -> Optional[ModelType]:
        """Get record by ID (async)."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all_async(
        self,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[uuid.UUID] = None
    ) -> list[ModelType]:
        """Get all records with pagination (async)."""
        query = select(self.model)
        if tenant_id and hasattr(self.model, 'tenant_id'):
            query = query.where(self.model.tenant_id == tenant_id)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_tenant_async(
        self,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[ModelType]:
        """Get records by tenant ID (async)."""
        result = await self.session.execute(
            select(self.model)
            .where(self.model.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_async(self, **kwargs) -> ModelType:
        """Create a new record (async)."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update_async(self, id: uuid.UUID, **kwargs) -> Optional[ModelType]:
        """Update a record by ID (async)."""
        instance = await self.get_by_id_async(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await self.session.flush()
            await self.session.refresh(instance)
        return instance

    async def delete_async(self, id: uuid.UUID) -> bool:
        """Delete a record by ID (async)."""
        instance = await self.get_by_id_async(id)
        if instance:
            await self.session.delete(instance)
            await self.session.flush()
            return True
        return False

    async def count_async(self, tenant_id: Optional[uuid.UUID] = None) -> int:
        """Count records (async)."""
        query = select(func.count(self.model.id))
        if tenant_id and hasattr(self.model, 'tenant_id'):
            query = query.where(self.model.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def exists_async(self, id: uuid.UUID) -> bool:
        """Check if record exists (async)."""
        result = await self.session.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None


# ============ Specialized Repositories ============

class FieldRepository(BaseRepository):
    """Repository for Field model with specialized methods."""

    async def get_by_farmer_async(
        self,
        farmer_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> list:
        """Get fields by farmer ID."""
        result = await self.session.execute(
            select(self.model)
            .where(
                self.model.farmer_id == farmer_id,
                self.model.tenant_id == tenant_id
            )
        )
        return list(result.scalars().all())

    async def get_by_region_async(
        self,
        region_id: int,
        tenant_id: uuid.UUID
    ) -> list:
        """Get fields by region ID."""
        result = await self.session.execute(
            select(self.model)
            .where(
                self.model.region_id == region_id,
                self.model.tenant_id == tenant_id
            )
        )
        return list(result.scalars().all())

    async def get_with_latest_ndvi_async(
        self,
        field_id: uuid.UUID,
        tenant_id: uuid.UUID
    ):
        """Get field with its latest NDVI result."""
        from sahool_shared.models import Field
        from sqlalchemy.orm import selectinload

        result = await self.session.execute(
            select(Field)
            .options(selectinload(Field.ndvi_results))
            .where(
                Field.id == field_id,
                Field.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()


class NDVIRepository(BaseRepository):
    """Repository for NDVI results with specialized methods."""

    async def get_by_field_async(
        self,
        field_id: uuid.UUID,
        limit: int = 10
    ) -> list:
        """Get NDVI results for a field."""
        from sahool_shared.models import NDVIResult

        result = await self.session.execute(
            select(NDVIResult)
            .where(NDVIResult.field_id == field_id)
            .order_by(NDVIResult.acquisition_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_for_field_async(
        self,
        field_id: uuid.UUID
    ):
        """Get latest NDVI result for a field."""
        from sahool_shared.models import NDVIResult

        result = await self.session.execute(
            select(NDVIResult)
            .where(NDVIResult.field_id == field_id)
            .order_by(NDVIResult.acquisition_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class WeatherRepository(BaseRepository):
    """Repository for weather data with specialized methods."""

    async def get_by_region_async(
        self,
        region_id: int,
        limit: int = 7
    ) -> list:
        """Get weather data for a region."""
        from sahool_shared.models import WeatherData

        result = await self.session.execute(
            select(WeatherData)
            .where(WeatherData.region_id == region_id)
            .order_by(WeatherData.forecast_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
