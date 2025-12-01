from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey,
    DateTime, CheckConstraint, Index, DECIMAL, text
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geometry
from datetime import datetime

from app.db.base import Base


class Field(Base):
    """
    Field model with enhanced security, indexing, and audit trails
    Version: 3.2.0 - Optimized for multi-tenant spatial queries
    """
    __tablename__ = "fields"

    # Primary Key (UUID for better security and distribution)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True
    )

    # Tenant Isolation (CRITICAL for multi-tenancy)
    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="Tenant identifier for data isolation"
    )

    # Field Information
    name = Column(
        String(255),
        nullable=False,
        doc="Field name"
    )

    crop = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Crop type (tomato, wheat, etc.)"
    )

    # Area in hectares (with precision)
    area_ha = Column(
        DECIMAL(12, 4),
        nullable=True,
        index=True,
        doc="Field area in hectares"
    )

    # Centroid cache (for quick access without geometry processing)
    centroid_lat = Column(
        DECIMAL(10, 7),
        nullable=True,
        doc="Centroid latitude (WGS84)"
    )

    centroid_lon = Column(
        DECIMAL(11, 7),
        nullable=True,
        doc="Centroid longitude (WGS84)"
    )

    # PostGIS geometry column (MultiPolygon) in EPSG:4326
    geometry = Column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=False,
        doc="Field boundary geometry (MultiPolygon, EPSG:4326)"
    )

    # Timestamps (for audit and sync)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        index=True,
        doc="Creation timestamp"
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
        index=True,
        doc="Last update timestamp"
    )

    # Soft delete support
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Soft delete timestamp (NULL = active)"
    )

    # Metadata (flexible JSONB for custom fields)
    metadata = Column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        doc="Custom metadata in JSON format"
    )

    # Constraints
    __table_args__ = (
        # Geometry validation
        CheckConstraint(
            "ST_IsValid(geometry)",
            name="geometry_valid"
        ),
        CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="geometry_srid"
        ),

        # Area validation
        CheckConstraint(
            "area_ha IS NULL OR area_ha > 0",
            name="area_positive"
        ),

        # Centroid range validation
        CheckConstraint(
            "centroid_lat IS NULL OR (centroid_lat >= -90 AND centroid_lat <= 90)",
            name="centroid_lat_range"
        ),
        CheckConstraint(
            "centroid_lon IS NULL OR (centroid_lon >= -180 AND centroid_lon <= 180)",
            name="centroid_lon_range"
        ),

        # Composite indexes for optimized queries
        Index(
            'idx_fields_tenant_geometry',
            'tenant_id', 'geometry',
            postgresql_using='gist'
        ),
        Index(
            'idx_fields_tenant_created',
            'tenant_id', 'created_at',
            postgresql_where=text("deleted_at IS NULL")
        ),
        Index(
            'idx_fields_tenant_crop',
            'tenant_id', 'crop',
            postgresql_where=text("deleted_at IS NULL AND crop IS NOT NULL")
        ),
        Index(
            'idx_fields_metadata',
            'metadata',
            postgresql_using='gin'
        ),

        # Table comment
        {'comment': 'Agricultural fields with spatial data (v3.2.0)'}
    )

    def __repr__(self):
        return f"<Field(id={self.id}, name='{self.name}', tenant_id={self.tenant_id}, area_ha={self.area_ha})>"

    @property
    def is_active(self) -> bool:
        """Check if field is active (not soft-deleted)"""
        return self.deleted_at is None

    def soft_delete(self):
        """Soft delete the field"""
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore soft-deleted field"""
        self.deleted_at = None
