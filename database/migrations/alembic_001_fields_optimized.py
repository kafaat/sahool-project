"""Add optimized fields schema with indexes and constraints

Revision ID: 001_fields_optimized
Revises:
Create Date: 2025-12-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers
revision = '001_fields_optimized'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Apply schema improvements"""

    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS btree_gist;')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')

    # Alter existing fields table (if exists) or create new one
    # Note: In production, you might want to create a new table and migrate data

    # Add new columns
    try:
        op.add_column('fields', sa.Column('created_at', sa.DateTime(timezone=True),
                                          server_default=sa.text('NOW()'), nullable=False))
        op.add_column('fields', sa.Column('updated_at', sa.DateTime(timezone=True),
                                          server_default=sa.text('NOW()'), nullable=False))
        op.add_column('fields', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
        op.add_column('fields', sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()),
                                          server_default=sa.text("'{}'::jsonb"), nullable=False))
    except:
        pass  # Columns might already exist

    # Change ID to UUID (requires data migration in production!)
    # op.execute('ALTER TABLE fields ALTER COLUMN id TYPE UUID USING (uuid_generate_v4());')
    # op.execute('ALTER TABLE fields ALTER COLUMN tenant_id TYPE UUID;')

    # Change numeric types to DECIMAL
    op.alter_column('fields', 'area_ha',
                    type_=sa.DECIMAL(12, 4),
                    existing_type=sa.Float())
    op.alter_column('fields', 'centroid_lat',
                    type_=sa.DECIMAL(10, 7),
                    existing_type=sa.Float())
    op.alter_column('fields', 'centroid_lon',
                    type_=sa.DECIMAL(11, 7),
                    existing_type=sa.Float())

    # Add constraints
    op.create_check_constraint(
        'geometry_valid',
        'fields',
        'ST_IsValid(geometry)'
    )
    op.create_check_constraint(
        'geometry_srid',
        'fields',
        'ST_SRID(geometry) = 4326'
    )
    op.create_check_constraint(
        'area_positive',
        'fields',
        'area_ha IS NULL OR area_ha > 0'
    )
    op.create_check_constraint(
        'centroid_lat_range',
        'fields',
        'centroid_lat IS NULL OR (centroid_lat >= -90 AND centroid_lat <= 90)'
    )
    op.create_check_constraint(
        'centroid_lon_range',
        'fields',
        'centroid_lon IS NULL OR (centroid_lon >= -180 AND centroid_lon <= 180)'
    )

    # Create indexes
    # Spatial indexes
    op.create_index(
        'idx_fields_geometry',
        'fields',
        ['geometry'],
        postgresql_using='gist'
    )
    op.create_index(
        'idx_fields_tenant_geometry',
        'fields',
        ['tenant_id', 'geometry'],
        postgresql_using='gist'
    )

    # B-tree indexes
    op.create_index(
        'idx_fields_tenant_id',
        'fields',
        ['tenant_id'],
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    op.create_index(
        'idx_fields_created_at',
        'fields',
        ['tenant_id', sa.text('created_at DESC')],
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    op.create_index(
        'idx_fields_updated_at',
        'fields',
        ['tenant_id', sa.text('updated_at DESC')],
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    op.create_index(
        'idx_fields_deleted_at',
        'fields',
        ['tenant_id'],
        postgresql_where=sa.text('deleted_at IS NOT NULL')
    )
    op.create_index(
        'idx_fields_crop',
        'fields',
        ['tenant_id', 'crop'],
        postgresql_where=sa.text('deleted_at IS NULL AND crop IS NOT NULL')
    )
    op.create_index(
        'idx_fields_area',
        'fields',
        ['tenant_id', 'area_ha'],
        postgresql_where=sa.text('deleted_at IS NULL AND area_ha IS NOT NULL')
    )

    # JSONB index
    op.create_index(
        'idx_fields_metadata',
        'fields',
        ['metadata'],
        postgresql_using='gin'
    )

    # Full-text search index
    op.create_index(
        'idx_fields_name_trgm',
        'fields',
        ['name'],
        postgresql_using='gin',
        postgresql_ops={'name': 'gin_trgm_ops'},
        postgresql_where=sa.text('deleted_at IS NULL')
    )

    # Create helper functions
    op.execute("""
        CREATE OR REPLACE FUNCTION calculate_field_area_ha(geom GEOMETRY)
        RETURNS DECIMAL(12, 4) AS $$
        BEGIN
            RETURN ROUND(
                ST_Area(ST_Transform(geom, 32630))::DECIMAL / 10000,
                4
            );
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION get_field_centroid(geom GEOMETRY)
        RETURNS JSONB AS $$
        DECLARE
            centroid GEOMETRY;
        BEGIN
            centroid := ST_Centroid(geom);
            RETURN jsonb_build_object(
                'lat', ROUND(ST_Y(centroid)::NUMERIC, 7),
                'lon', ROUND(ST_X(centroid)::NUMERIC, 7)
            );
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION validate_geometry_complexity(geom GEOMETRY)
        RETURNS BOOLEAN AS $$
        DECLARE
            num_points INT;
        BEGIN
            num_points := ST_NPoints(geom);
            RETURN num_points >= 3 AND num_points <= 1000;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """)

    # Create triggers
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_fields_updated_at
            BEFORE UPDATE ON fields
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION auto_calculate_field_metrics()
        RETURNS TRIGGER AS $$
        DECLARE
            centroid_json JSONB;
        BEGIN
            IF NEW.geometry IS DISTINCT FROM OLD.geometry OR TG_OP = 'INSERT' THEN
                NEW.area_ha := calculate_field_area_ha(NEW.geometry);
                centroid_json := get_field_centroid(NEW.geometry);
                NEW.centroid_lat := (centroid_json->>'lat')::DECIMAL;
                NEW.centroid_lon := (centroid_json->>'lon')::DECIMAL;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_auto_calculate_metrics
            BEFORE INSERT OR UPDATE OF geometry ON fields
            FOR EACH ROW
            EXECUTE FUNCTION auto_calculate_field_metrics();
    """)

    # Create views
    op.execute("""
        CREATE OR REPLACE VIEW v_active_fields AS
        SELECT
            id,
            tenant_id,
            name,
            crop,
            area_ha,
            centroid_lat,
            centroid_lon,
            ST_AsGeoJSON(geometry)::JSONB as geometry_geojson,
            created_at,
            updated_at,
            metadata
        FROM fields
        WHERE deleted_at IS NULL;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_tenant_field_stats AS
        SELECT
            tenant_id,
            COUNT(*) as total_fields,
            SUM(area_ha) as total_area_ha,
            AVG(area_ha) as avg_field_size_ha,
            COUNT(DISTINCT crop) as distinct_crops,
            MIN(created_at) as first_field_created,
            MAX(updated_at) as last_updated
        FROM fields
        WHERE deleted_at IS NULL
        GROUP BY tenant_id;
    """)

    # Enable Row Level Security
    op.execute('ALTER TABLE fields ENABLE ROW LEVEL SECURITY;')

    # Create RLS policies
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON fields
            FOR ALL
            USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
    """)

    op.execute("""
        CREATE POLICY admin_all_access_policy ON fields
            FOR ALL
            USING (current_setting('app.user_role', TRUE) = 'admin');
    """)

    # Analyze table
    op.execute('ANALYZE fields;')


def downgrade():
    """Revert schema improvements"""

    # Drop RLS policies
    op.execute('DROP POLICY IF EXISTS tenant_isolation_policy ON fields;')
    op.execute('DROP POLICY IF EXISTS admin_all_access_policy ON fields;')

    # Disable RLS
    op.execute('ALTER TABLE fields DISABLE ROW LEVEL SECURITY;')

    # Drop views
    op.execute('DROP VIEW IF EXISTS v_active_fields;')
    op.execute('DROP VIEW IF EXISTS v_tenant_field_stats;')

    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS trigger_auto_calculate_metrics ON fields;')
    op.execute('DROP TRIGGER IF EXISTS trigger_fields_updated_at ON fields;')

    # Drop functions
    op.execute('DROP FUNCTION IF EXISTS auto_calculate_field_metrics();')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column();')
    op.execute('DROP FUNCTION IF EXISTS validate_geometry_complexity(GEOMETRY);')
    op.execute('DROP FUNCTION IF EXISTS get_field_centroid(GEOMETRY);')
    op.execute('DROP FUNCTION IF EXISTS calculate_field_area_ha(GEOMETRY);')

    # Drop indexes
    op.drop_index('idx_fields_name_trgm', 'fields')
    op.drop_index('idx_fields_metadata', 'fields')
    op.drop_index('idx_fields_area', 'fields')
    op.drop_index('idx_fields_crop', 'fields')
    op.drop_index('idx_fields_deleted_at', 'fields')
    op.drop_index('idx_fields_updated_at', 'fields')
    op.drop_index('idx_fields_created_at', 'fields')
    op.drop_index('idx_fields_tenant_id', 'fields')
    op.drop_index('idx_fields_tenant_geometry', 'fields')
    op.drop_index('idx_fields_geometry', 'fields')

    # Drop constraints
    op.drop_constraint('centroid_lon_range', 'fields')
    op.drop_constraint('centroid_lat_range', 'fields')
    op.drop_constraint('area_positive', 'fields')
    op.drop_constraint('geometry_srid', 'fields')
    op.drop_constraint('geometry_valid', 'fields')

    # Drop columns
    op.drop_column('fields', 'metadata')
    op.drop_column('fields', 'deleted_at')
    op.drop_column('fields', 'updated_at')
    op.drop_column('fields', 'created_at')
