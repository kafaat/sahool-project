-- =============================================================================
-- SAHOOL Platform - Performance Indexes Migration
-- Version: 6.8.4
-- Purpose: Add indexes for improved query performance
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Weather Data Indexes
-- -----------------------------------------------------------------------------
-- Composite index for weather queries by field and date
CREATE INDEX IF NOT EXISTS idx_weather_field_date
    ON sahool.weather_data(field_id, forecast_date DESC, created_at DESC);

-- Index for region-based weather queries
CREATE INDEX IF NOT EXISTS idx_weather_region_date
    ON sahool.weather_data(region_id, forecast_date DESC);

-- Index for tenant isolation queries
CREATE INDEX IF NOT EXISTS idx_weather_tenant
    ON sahool.weather_data(tenant_id, created_at DESC);

-- -----------------------------------------------------------------------------
-- NDVI Results Indexes
-- -----------------------------------------------------------------------------
-- Composite index for NDVI queries by field and acquisition date
CREATE INDEX IF NOT EXISTS idx_ndvi_field_date
    ON sahool.ndvi_results(field_id, acquisition_date DESC);

-- Index for tenant NDVI analysis
CREATE INDEX IF NOT EXISTS idx_ndvi_tenant_date
    ON sahool.ndvi_results(tenant_id, acquisition_date DESC);

-- Index for health status filtering
CREATE INDEX IF NOT EXISTS idx_ndvi_health_status
    ON sahool.ndvi_results(health_status, acquisition_date DESC);

-- -----------------------------------------------------------------------------
-- Fields Indexes
-- -----------------------------------------------------------------------------
-- Spatial index for geographic queries (requires PostGIS)
CREATE INDEX IF NOT EXISTS idx_fields_geometry
    ON sahool.fields USING GIST(geometry);

-- Index for field lookups by tenant and region
CREATE INDEX IF NOT EXISTS idx_fields_tenant_region
    ON sahool.fields(tenant_id, region_id);

-- Index for active fields
CREATE INDEX IF NOT EXISTS idx_fields_active
    ON sahool.fields(is_active, tenant_id) WHERE is_active = true;

-- -----------------------------------------------------------------------------
-- Alerts Indexes
-- -----------------------------------------------------------------------------
-- Composite index for unread alerts by tenant
CREATE INDEX IF NOT EXISTS idx_alerts_tenant_unread
    ON sahool.alerts(tenant_id, created_at DESC) WHERE is_read = false;

-- Index for alert severity filtering
CREATE INDEX IF NOT EXISTS idx_alerts_severity
    ON sahool.alerts(severity, created_at DESC);

-- Index for field-specific alerts
CREATE INDEX IF NOT EXISTS idx_alerts_field
    ON sahool.alerts(field_id, created_at DESC);

-- -----------------------------------------------------------------------------
-- Users Indexes
-- -----------------------------------------------------------------------------
-- Unique index for email (case-insensitive)
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower
    ON sahool.users(LOWER(email));

-- Index for tenant user lookups
CREATE INDEX IF NOT EXISTS idx_users_tenant_role
    ON sahool.users(tenant_id, role);

-- Index for active users
CREATE INDEX IF NOT EXISTS idx_users_active
    ON sahool.users(is_active, tenant_id) WHERE is_active = true;

-- -----------------------------------------------------------------------------
-- Farmers Indexes
-- -----------------------------------------------------------------------------
-- Index for farmer search by name (Arabic support)
CREATE INDEX IF NOT EXISTS idx_farmers_name_ar
    ON sahool.farmers USING gin(name_ar gin_trgm_ops);

-- Index for farmer phone lookup
CREATE INDEX IF NOT EXISTS idx_farmers_phone
    ON sahool.farmers(phone);

-- Index for tenant farmers
CREATE INDEX IF NOT EXISTS idx_farmers_tenant
    ON sahool.farmers(tenant_id, created_at DESC);

-- -----------------------------------------------------------------------------
-- Audit Logs Indexes (for compliance queries)
-- -----------------------------------------------------------------------------
-- Composite index for audit trail queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity
    ON sahool.audit_logs(entity_type, entity_id, created_at DESC);

-- Index for user activity tracking
CREATE INDEX IF NOT EXISTS idx_audit_logs_user
    ON sahool.audit_logs(user_id, created_at DESC);

-- Index for action type filtering
CREATE INDEX IF NOT EXISTS idx_audit_logs_action
    ON sahool.audit_logs(action, created_at DESC);

-- -----------------------------------------------------------------------------
-- Soil Analysis Indexes
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_soil_field_date
    ON sahool.soil_analysis(field_id, analysis_date DESC);

-- -----------------------------------------------------------------------------
-- Irrigation Schedules Indexes
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_irrigation_field_date
    ON sahool.irrigation_schedules(field_id, scheduled_date);

CREATE INDEX IF NOT EXISTS idx_irrigation_status
    ON sahool.irrigation_schedules(status, scheduled_date);

-- -----------------------------------------------------------------------------
-- Enable pg_trgm extension for fuzzy search (if not exists)
-- -----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- -----------------------------------------------------------------------------
-- Analyze tables to update statistics
-- -----------------------------------------------------------------------------
ANALYZE sahool.weather_data;
ANALYZE sahool.ndvi_results;
ANALYZE sahool.fields;
ANALYZE sahool.alerts;
ANALYZE sahool.users;
ANALYZE sahool.farmers;

-- =============================================================================
-- End of Performance Indexes Migration
-- =============================================================================
