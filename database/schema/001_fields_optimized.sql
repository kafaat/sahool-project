-- ===================================================================
-- Sahool Geo-Core - Optimized Database Schema with Spatial Indexing
-- Version: 3.2.0
-- PostGIS Required: 3.0+
-- ===================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ===================================================================
-- 1. FIELDS TABLE - Optimized with Spatial Indexes
-- ===================================================================

-- Drop existing table if needed (CAREFUL IN PRODUCTION!)
-- DROP TABLE IF EXISTS fields CASCADE;

CREATE TABLE IF NOT EXISTS fields (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Tenant Isolation (CRITICAL for multi-tenancy)
    tenant_id UUID NOT NULL,

    -- Field Information
    name VARCHAR(255) NOT NULL,
    crop VARCHAR(100),
    area_ha DECIMAL(12, 4),

    -- Centroid cache (for quick access without geometry processing)
    centroid_lat DECIMAL(10, 7),
    centroid_lon DECIMAL(11, 7),

    -- Spatial Data - MULTIPOLYGON for complex field shapes
    geometry GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,

    -- Timestamps (for audit and sync)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete support

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT geometry_valid CHECK (ST_IsValid(geometry)),
    CONSTRAINT geometry_srid CHECK (ST_SRID(geometry) = 4326),
    CONSTRAINT area_positive CHECK (area_ha IS NULL OR area_ha > 0),
    CONSTRAINT centroid_lat_range CHECK (
        centroid_lat IS NULL OR (centroid_lat >= -90 AND centroid_lat <= 90)
    ),
    CONSTRAINT centroid_lon_range CHECK (
        centroid_lon IS NULL OR (centroid_lon >= -180 AND centroid_lon <= 180)
    )
);

-- ===================================================================
-- 2. INDEXES - Performance Optimization
-- ===================================================================

-- Primary spatial index (GIST) - CRITICAL for spatial queries
CREATE INDEX IF NOT EXISTS idx_fields_geometry
ON fields USING GIST (geometry);

-- Composite spatial index with tenant isolation
CREATE INDEX IF NOT EXISTS idx_fields_tenant_geometry
ON fields USING GIST (tenant_id, geometry);

-- Tenant isolation index (B-tree) - for fast tenant filtering
CREATE INDEX IF NOT EXISTS idx_fields_tenant_id
ON fields (tenant_id) WHERE deleted_at IS NULL;

-- Temporal queries - list recent fields
CREATE INDEX IF NOT EXISTS idx_fields_created_at
ON fields (tenant_id, created_at DESC) WHERE deleted_at IS NULL;

-- Updated at index for sync operations
CREATE INDEX IF NOT EXISTS idx_fields_updated_at
ON fields (tenant_id, updated_at DESC) WHERE deleted_at IS NULL;

-- Soft delete index
CREATE INDEX IF NOT EXISTS idx_fields_deleted_at
ON fields (tenant_id) WHERE deleted_at IS NOT NULL;

-- Crop type index for filtering
CREATE INDEX IF NOT EXISTS idx_fields_crop
ON fields (tenant_id, crop) WHERE deleted_at IS NULL AND crop IS NOT NULL;

-- Area range queries
CREATE INDEX IF NOT EXISTS idx_fields_area
ON fields (tenant_id, area_ha) WHERE deleted_at IS NULL AND area_ha IS NOT NULL;

-- Metadata JSONB index (GIN) for fast JSON queries
CREATE INDEX IF NOT EXISTS idx_fields_metadata
ON fields USING GIN (metadata);

-- Full-text search on field names
CREATE INDEX IF NOT EXISTS idx_fields_name_trgm
ON fields USING GIN (name gin_trgm_ops) WHERE deleted_at IS NULL;

-- ===================================================================
-- 3. SPATIAL FUNCTIONS - Helper Functions
-- ===================================================================

-- Function: Calculate field area in hectares
CREATE OR REPLACE FUNCTION calculate_field_area_ha(geom GEOMETRY)
RETURNS DECIMAL(12, 4) AS $$
BEGIN
    -- Convert to appropriate UTM zone for accurate area calculation
    RETURN ROUND(
        ST_Area(ST_Transform(geom, 32630))::DECIMAL / 10000, -- m² to hectares
        4
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function: Get field centroid
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

-- Function: Validate geometry complexity
CREATE OR REPLACE FUNCTION validate_geometry_complexity(geom GEOMETRY)
RETURNS BOOLEAN AS $$
DECLARE
    num_points INT;
BEGIN
    num_points := ST_NPoints(geom);
    -- Limit to 1000 vertices per field
    RETURN num_points >= 3 AND num_points <= 1000;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Add complexity constraint
ALTER TABLE fields ADD CONSTRAINT geometry_complexity
CHECK (validate_geometry_complexity(geometry));

-- ===================================================================
-- 4. TRIGGERS - Auto-update Timestamps and Derived Fields
-- ===================================================================

-- Trigger function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update timestamp
CREATE TRIGGER trigger_fields_updated_at
    BEFORE UPDATE ON fields
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger function: Auto-calculate area and centroid
CREATE OR REPLACE FUNCTION auto_calculate_field_metrics()
RETURNS TRIGGER AS $$
DECLARE
    centroid_json JSONB;
BEGIN
    -- Calculate area if geometry changed
    IF NEW.geometry IS DISTINCT FROM OLD.geometry OR TG_OP = 'INSERT' THEN
        NEW.area_ha := calculate_field_area_ha(NEW.geometry);

        -- Calculate centroid
        centroid_json := get_field_centroid(NEW.geometry);
        NEW.centroid_lat := (centroid_json->>'lat')::DECIMAL;
        NEW.centroid_lon := (centroid_json->>'lon')::DECIMAL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-calculate metrics
CREATE TRIGGER trigger_auto_calculate_metrics
    BEFORE INSERT OR UPDATE OF geometry ON fields
    FOR EACH ROW
    EXECUTE FUNCTION auto_calculate_field_metrics();

-- ===================================================================
-- 5. VIEWS - Common Queries
-- ===================================================================

-- View: Active fields only (not soft-deleted)
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

-- View: Field statistics per tenant
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

-- ===================================================================
-- 6. SECURITY - Row Level Security (RLS)
-- ===================================================================

-- Enable RLS
ALTER TABLE fields ENABLE ROW LEVEL SECURITY;

-- Policy: Tenants can only see their own fields
CREATE POLICY tenant_isolation_policy ON fields
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Policy: Admin can see all fields
CREATE POLICY admin_all_access_policy ON fields
    FOR ALL
    USING (current_setting('app.user_role', TRUE) = 'admin');

-- ===================================================================
-- 7. PERFORMANCE TUNING - Analyze and Vacuum
-- ===================================================================

-- Analyze table for query optimizer
ANALYZE fields;

-- Vacuum to reclaim space
VACUUM ANALYZE fields;

-- ===================================================================
-- 8. SAMPLE DATA (Optional - for testing)
-- ===================================================================

-- Insert sample field (commented out by default)
/*
INSERT INTO fields (tenant_id, name, crop, geometry) VALUES (
    gen_random_uuid(),
    'Test Field 1',
    'Tomato',
    ST_GeomFromGeoJSON('{
        "type": "MultiPolygon",
        "coordinates": [[[[30.0, 31.0], [30.1, 31.0], [30.1, 31.1], [30.0, 31.1], [30.0, 31.0]]]]
    }')
);
*/

-- ===================================================================
-- 9. MONITORING - Performance Queries
-- ===================================================================

-- Query to check index usage
CREATE OR REPLACE VIEW v_fields_index_usage AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename = 'fields'
ORDER BY idx_scan DESC;

-- Query to check table size
CREATE OR REPLACE VIEW v_fields_table_size AS
SELECT
    pg_size_pretty(pg_total_relation_size('fields')) as total_size,
    pg_size_pretty(pg_table_size('fields')) as table_size,
    pg_size_pretty(pg_indexes_size('fields')) as indexes_size;

-- ===================================================================
-- NOTES
-- ===================================================================
--
-- Performance Considerations:
-- 1. GIST indexes are essential for spatial queries (ST_Intersects, ST_Within, etc.)
-- 2. Composite indexes (tenant_id, geometry) optimize multi-tenant spatial queries
-- 3. Partial indexes (WHERE deleted_at IS NULL) save space and improve performance
-- 4. JSONB GIN indexes enable fast metadata queries
-- 5. Triggers auto-calculate derived fields (area, centroid)
--
-- Security:
-- 1. Row Level Security (RLS) ensures tenant isolation at database level
-- 2. Constraints validate geometry (valid, SRID, complexity)
-- 3. Soft deletes preserve data history
--
-- Maintenance:
-- 1. Run VACUUM ANALYZE regularly (weekly recommended)
-- 2. Monitor index usage with v_fields_index_usage view
-- 3. Check table size with v_fields_table_size view
-- 4. Review slow queries with pg_stat_statements
--
-- ===================================================================
