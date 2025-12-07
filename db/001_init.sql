-- =============================================================================
-- SAHOOL Platform v6.8.4 - Initial Database Schema
-- منصة سهول - مخطط قاعدة البيانات الأساسي
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schema
CREATE SCHEMA IF NOT EXISTS sahool;
SET search_path TO sahool, public;

-- =============================================================================
-- Tenants Table - جدول المستأجرين (المنظمات)
-- =============================================================================
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    email VARCHAR(255),
    phone VARCHAR(20),
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    plan_expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_is_active ON tenants(is_active);

-- =============================================================================
-- Users Table - جدول المستخدمين
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMPTZ,
    language VARCHAR(10) DEFAULT 'ar',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- =============================================================================
-- Regions Table - جدول المناطق
-- =============================================================================
CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    governorate VARCHAR(100),
    country VARCHAR(50) DEFAULT 'Yemen',
    geometry GEOMETRY(POLYGON, 4326),
    climate_zone VARCHAR(50),
    elevation_avg DECIMAL(10, 2),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_regions_name ON regions(name_ar);
CREATE INDEX idx_regions_geometry ON regions USING GIST(geometry);

-- =============================================================================
-- Farmers Table - جدول المزارعين
-- =============================================================================
CREATE TABLE IF NOT EXISTS farmers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    national_id VARCHAR(50),
    region_id INTEGER REFERENCES regions(id),
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_farmers_tenant ON farmers(tenant_id);
CREATE INDEX idx_farmers_region ON farmers(region_id);

-- =============================================================================
-- Fields Table - جدول الحقول
-- =============================================================================
CREATE TABLE IF NOT EXISTS fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    farmer_id UUID REFERENCES farmers(id) ON DELETE SET NULL,
    region_id INTEGER REFERENCES regions(id),
    name_ar VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    area_hectares DECIMAL(10, 4) NOT NULL,
    geometry GEOMETRY(POLYGON, 4326),
    centroid GEOMETRY(POINT, 4326),
    crop_type VARCHAR(100),
    planting_date DATE,
    expected_harvest_date DATE,
    irrigation_type VARCHAR(50),
    soil_type VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_fields_tenant ON fields(tenant_id);
CREATE INDEX idx_fields_farmer ON fields(farmer_id);
CREATE INDEX idx_fields_region ON fields(region_id);
CREATE INDEX idx_fields_geometry ON fields USING GIST(geometry);
CREATE INDEX idx_fields_crop_type ON fields(crop_type);

-- =============================================================================
-- NDVI Results Table - جدول نتائج NDVI
-- =============================================================================
CREATE TABLE IF NOT EXISTS ndvi_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    ndvi_value DECIMAL(5, 4) NOT NULL CHECK (ndvi_value >= -1 AND ndvi_value <= 1),
    acquisition_date DATE NOT NULL,
    satellite_name VARCHAR(50),
    cloud_coverage DECIMAL(5, 2),
    tile_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    processing_version VARCHAR(20),
    quality_score DECIMAL(5, 2),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ndvi_tenant ON ndvi_results(tenant_id);
CREATE INDEX idx_ndvi_field ON ndvi_results(field_id);
CREATE INDEX idx_ndvi_date ON ndvi_results(acquisition_date DESC);
CREATE INDEX idx_ndvi_field_date ON ndvi_results(field_id, acquisition_date DESC);

-- =============================================================================
-- Weather Data Table - جدول بيانات الطقس
-- =============================================================================
CREATE TABLE IF NOT EXISTS weather_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    region_id INTEGER REFERENCES regions(id),
    forecast_date DATE NOT NULL,
    temperature DECIMAL(5, 2),
    temperature_min DECIMAL(5, 2),
    temperature_max DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    rainfall DECIMAL(8, 2),
    wind_speed DECIMAL(6, 2),
    wind_direction VARCHAR(10),
    pressure DECIMAL(7, 2),
    solar_radiation DECIMAL(8, 2),
    uv_index DECIMAL(4, 2),
    source VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_weather_field ON weather_data(field_id);
CREATE INDEX idx_weather_region ON weather_data(region_id);
CREATE INDEX idx_weather_date ON weather_data(forecast_date DESC);

-- =============================================================================
-- Alerts Table - جدول التنبيهات
-- =============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    title_ar VARCHAR(200) NOT NULL,
    title_en VARCHAR(200),
    description_ar TEXT,
    description_en TEXT,
    status VARCHAR(20) DEFAULT 'active',
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_tenant ON alerts(tenant_id);
CREATE INDEX idx_alerts_field ON alerts(field_id);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_type ON alerts(alert_type);

-- =============================================================================
-- Soil Analysis Table - جدول تحليل التربة
-- =============================================================================
CREATE TABLE IF NOT EXISTS soil_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    analysis_date DATE NOT NULL,
    ph DECIMAL(4, 2),
    nitrogen DECIMAL(8, 2),
    phosphorus DECIMAL(8, 2),
    potassium DECIMAL(8, 2),
    organic_matter DECIMAL(5, 2),
    moisture DECIMAL(5, 2),
    salinity DECIMAL(6, 2),
    texture VARCHAR(50),
    recommendations TEXT,
    lab_name VARCHAR(200),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_soil_field ON soil_analysis(field_id);
CREATE INDEX idx_soil_date ON soil_analysis(analysis_date DESC);

-- =============================================================================
-- Irrigation Schedules Table - جدول جداول الري
-- =============================================================================
CREATE TABLE IF NOT EXISTS irrigation_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    duration_minutes INTEGER,
    water_amount_liters DECIMAL(10, 2),
    method VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    completed_at TIMESTAMPTZ,
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_irrigation_field ON irrigation_schedules(field_id);
CREATE INDEX idx_irrigation_date ON irrigation_schedules(scheduled_date);
CREATE INDEX idx_irrigation_status ON irrigation_schedules(status);

-- =============================================================================
-- Yield Records Table - جدول سجلات المحصول
-- =============================================================================
CREATE TABLE IF NOT EXISTS yield_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    harvest_date DATE NOT NULL,
    crop_type VARCHAR(100) NOT NULL,
    yield_kg DECIMAL(12, 2) NOT NULL,
    yield_per_hectare DECIMAL(10, 2),
    quality_grade VARCHAR(20),
    price_per_kg DECIMAL(10, 2),
    total_revenue DECIMAL(14, 2),
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_yield_field ON yield_records(field_id);
CREATE INDEX idx_yield_date ON yield_records(harvest_date DESC);
CREATE INDEX idx_yield_crop ON yield_records(crop_type);

-- =============================================================================
-- Plant Health Records Table - جدول سجلات صحة النبات
-- =============================================================================
CREATE TABLE IF NOT EXISTS plant_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    inspection_date DATE NOT NULL,
    health_score DECIMAL(5, 2),
    disease_detected VARCHAR(200),
    pest_detected VARCHAR(200),
    treatment_applied VARCHAR(200),
    inspector_id UUID REFERENCES users(id),
    photos JSONB DEFAULT '[]',
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_plant_health_field ON plant_health(field_id);
CREATE INDEX idx_plant_health_date ON plant_health(inspection_date DESC);

-- =============================================================================
-- Insert Default Data
-- =============================================================================

-- Default tenant
INSERT INTO tenants (id, name, slug, plan, is_active)
VALUES ('00000000-0000-0000-0000-000000000001', 'Default Organization', 'default', 'free', true)
ON CONFLICT (slug) DO NOTHING;

-- Yemen regions
INSERT INTO regions (name_ar, name_en, governorate, climate_zone) VALUES
    ('صنعاء', 'Sanaa', 'صنعاء', 'highland'),
    ('عدن', 'Aden', 'عدن', 'coastal'),
    ('تعز', 'Taiz', 'تعز', 'highland'),
    ('الحديدة', 'Hodeidah', 'الحديدة', 'coastal'),
    ('إب', 'Ibb', 'إب', 'highland'),
    ('حضرموت', 'Hadramaut', 'حضرموت', 'desert'),
    ('ذمار', 'Dhamar', 'ذمار', 'highland'),
    ('عمران', 'Amran', 'عمران', 'highland'),
    ('صعدة', 'Saada', 'صعدة', 'highland'),
    ('حجة', 'Hajjah', 'حجة', 'highland'),
    ('المحويت', 'Al-Mahwit', 'المحويت', 'highland'),
    ('البيضاء', 'Al-Bayda', 'البيضاء', 'highland'),
    ('شبوة', 'Shabwah', 'شبوة', 'desert'),
    ('لحج', 'Lahij', 'لحج', 'coastal'),
    ('مأرب', 'Marib', 'مأرب', 'desert'),
    ('الجوف', 'Al-Jawf', 'الجوف', 'desert'),
    ('المهرة', 'Al-Mahrah', 'المهرة', 'coastal'),
    ('ريمة', 'Raymah', 'ريمة', 'highland'),
    ('سقطرى', 'Socotra', 'سقطرى', 'coastal')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- Functions
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT table_name
        FROM information_schema.columns
        WHERE column_name = 'updated_at'
        AND table_schema = 'sahool'
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%I_updated_at ON sahool.%I;
            CREATE TRIGGER update_%I_updated_at
                BEFORE UPDATE ON sahool.%I
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        ', t, t, t, t);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Roles and Grants (Least Privilege Principle)
-- =============================================================================

-- Create application roles if they don't exist
DO $$
BEGIN
    -- Application role: for the main application service account
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sahool_app') THEN
        CREATE ROLE sahool_app;
    END IF;

    -- Admin role: for administrative operations
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sahool_admin') THEN
        CREATE ROLE sahool_admin;
    END IF;

    -- Read-only role: for reporting and analytics
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sahool_readonly') THEN
        CREATE ROLE sahool_readonly;
    END IF;
END
$$;

-- Schema access
GRANT USAGE ON SCHEMA sahool TO sahool_app, sahool_admin, sahool_readonly;

-- Application role: full CRUD on all tables (for the application)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA sahool TO sahool_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sahool TO sahool_app;

-- Admin role: full access including DDL operations
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA sahool TO sahool_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA sahool TO sahool_admin;

-- Read-only role: SELECT only (for reporting/analytics)
GRANT SELECT ON ALL TABLES IN SCHEMA sahool TO sahool_readonly;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA sahool GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sahool_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA sahool GRANT USAGE, SELECT ON SEQUENCES TO sahool_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA sahool GRANT ALL PRIVILEGES ON TABLES TO sahool_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA sahool GRANT SELECT ON TABLES TO sahool_readonly;
