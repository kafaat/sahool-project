#!/bin/bash
# =============================================================================
# Module 02: Database Setup
# وحدة إعداد قاعدة البيانات
# =============================================================================
# This module handles:
# - PostgreSQL deployment with hardening
# - Role-based access (app, readonly, migration, monitoring)
# - Row Level Security (RLS) for multi-tenancy
# - Alembic migrations
# - pgAudit logging
# =============================================================================

set -euo pipefail

DB_INIT_DIR="${PROJECT_ROOT}/database/postgres/init"
DB_MIGRATIONS_DIR="${PROJECT_ROOT}/database/postgres/migrations"

database_module() {
    log "🗄️ Setting up PostgreSQL database..."

    # Create initialization scripts
    create_db_init_scripts

    # Create pg_hba.conf for access control
    create_pg_hba_conf

    # Create postgresql.conf for hardening
    create_postgresql_conf

    # Setup Alembic migrations
    setup_alembic

    success "Database configuration completed"
}

create_db_init_scripts() {
    info "Creating database initialization scripts..."

    mkdir -p "$DB_INIT_DIR"

    # 01 - Extensions
    cat > "${DB_INIT_DIR}/01-extensions.sql" <<'EOF'
-- =============================================================================
-- SAHOOL Yemen - Database Extensions
-- =============================================================================

-- Core extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Geospatial
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "postgis_topology";

-- Full text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Auditing
CREATE EXTENSION IF NOT EXISTS "pgaudit";

-- Performance
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

\echo 'Extensions installed successfully'
EOF

    # 02 - Roles
    cat > "${DB_INIT_DIR}/02-roles.sql" <<'EOF'
-- =============================================================================
-- SAHOOL Yemen - Database Roles (Least Privilege Principle)
-- =============================================================================

-- Application role (CRUD operations)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sahool_app') THEN
        CREATE ROLE sahool_app WITH LOGIN PASSWORD :'DB_PASSWORD';
    END IF;
END
$$;

-- Read-only role (for analytics/reporting)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sahool_readonly') THEN
        CREATE ROLE sahool_readonly WITH LOGIN PASSWORD :'DB_READONLY_PASSWORD';
    END IF;
END
$$;

-- Migration role (DDL operations)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sahool_migration') THEN
        CREATE ROLE sahool_migration WITH LOGIN PASSWORD :'DB_MIGRATION_PASSWORD' CREATEDB;
    END IF;
END
$$;

-- Monitoring role (stats only)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sahool_monitor') THEN
        CREATE ROLE sahool_monitor WITH LOGIN PASSWORD :'DB_MONITOR_PASSWORD';
    END IF;
END
$$;

-- Grant permissions
GRANT CONNECT ON DATABASE sahool_production TO sahool_app, sahool_readonly, sahool_migration, sahool_monitor;

\echo 'Roles created successfully'
EOF

    # 03 - Schema
    cat > "${DB_INIT_DIR}/03-schema.sql" <<'EOF'
-- =============================================================================
-- SAHOOL Yemen - Database Schema
-- =============================================================================

-- Create schema
CREATE SCHEMA IF NOT EXISTS sahool AUTHORIZATION sahool_migration;

-- Set search path
ALTER DATABASE sahool_production SET search_path TO sahool, public;

-- =============================================================================
-- Core Tables
-- =============================================================================

-- Tenants (Organizations)
CREATE TABLE IF NOT EXISTS sahool.tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    email VARCHAR(255),
    phone VARCHAR(20),
    plan VARCHAR(50) DEFAULT 'free',
    plan_expires_at TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users
CREATE TABLE IF NOT EXISTS sahool.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sahool.tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    role VARCHAR(50) DEFAULT 'viewer',
    permissions JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    language VARCHAR(10) DEFAULT 'ar',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

-- Regions (Governorates)
CREATE TABLE IF NOT EXISTS sahool.regions (
    id SERIAL PRIMARY KEY,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    coordinates GEOGRAPHY(POINT, 4326) NOT NULL,
    boundary GEOGRAPHY(POLYGON, 4326),
    area_km2 DECIMAL(10,2),
    agricultural_potential TEXT,
    climate_zone VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Farmers
CREATE TABLE IF NOT EXISTS sahool.farmers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sahool.tenants(id) ON DELETE CASCADE,
    region_id INTEGER REFERENCES sahool.regions(id),
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    phone_encrypted BYTEA,
    email_encrypted BYTEA,
    registration_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fields
CREATE TABLE IF NOT EXISTS sahool.fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sahool.tenants(id) ON DELETE CASCADE,
    farmer_id UUID REFERENCES sahool.farmers(id) ON DELETE SET NULL,
    region_id INTEGER REFERENCES sahool.regions(id),
    name_ar VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    area_hectares DECIMAL(10,2) NOT NULL CHECK (area_hectares > 0),
    crop_type VARCHAR(100),
    crop_variety VARCHAR(100),
    planting_date DATE,
    expected_harvest_date DATE,
    coordinates GEOGRAPHY(POINT, 4326) NOT NULL,
    boundary GEOGRAPHY(POLYGON, 4326),
    elevation_meters INTEGER,
    soil_type VARCHAR(50),
    soil_ph DECIMAL(4,2) CHECK (soil_ph BETWEEN 0 AND 14),
    irrigation_type VARCHAR(50),
    irrigation_system JSONB,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'harvested')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- NDVI Results
CREATE TABLE IF NOT EXISTS sahool.ndvi_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sahool.tenants(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES sahool.fields(id) ON DELETE CASCADE,
    ndvi_value DECIMAL(5,3) NOT NULL CHECK (ndvi_value BETWEEN -1 AND 1),
    acquisition_date DATE NOT NULL,
    satellite_name VARCHAR(50) DEFAULT 'Sentinel-2',
    tile_url TEXT,
    tile_metadata JSONB,
    cloud_coverage DECIMAL(5,2) CHECK (cloud_coverage BETWEEN 0 AND 100),
    processing_version VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Weather Data
CREATE TABLE IF NOT EXISTS sahool.weather_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sahool.tenants(id) ON DELETE CASCADE,
    region_id INTEGER REFERENCES sahool.regions(id),
    field_id UUID REFERENCES sahool.fields(id) ON DELETE CASCADE,
    temperature DECIMAL(6,2),
    temperature_min DECIMAL(6,2),
    temperature_max DECIMAL(6,2),
    humidity DECIMAL(5,2),
    rainfall DECIMAL(8,2),
    wind_speed DECIMAL(6,2),
    wind_direction VARCHAR(10),
    pressure DECIMAL(7,2),
    solar_radiation DECIMAL(8,2),
    forecast_date DATE,
    forecast_accuracy DECIMAL(5,2),
    source VARCHAR(50) DEFAULT 'OpenWeather',
    station_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alerts
CREATE TABLE IF NOT EXISTS sahool.alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES sahool.tenants(id) ON DELETE CASCADE,
    field_id UUID REFERENCES sahool.fields(id) ON DELETE CASCADE,
    region_id INTEGER REFERENCES sahool.regions(id),
    title_ar VARCHAR(200) NOT NULL,
    title_en VARCHAR(200),
    message_ar TEXT NOT NULL,
    message_en TEXT,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'active',
    expires_at TIMESTAMP WITH TIME ZONE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit Log
CREATE TABLE IF NOT EXISTS sahool.audit_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES sahool.tenants(id),
    user_id UUID REFERENCES sahool.users(id),
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(100),
    record_id UUID,
    old_data JSONB,
    new_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

\echo 'Schema created successfully'
EOF

    # 04 - Indexes
    cat > "${DB_INIT_DIR}/04-indexes.sql" <<'EOF'
-- =============================================================================
-- SAHOOL Yemen - Database Indexes
-- =============================================================================

-- Tenant indexes
CREATE INDEX IF NOT EXISTS idx_tenants_slug ON sahool.tenants(slug);
CREATE INDEX IF NOT EXISTS idx_tenants_active ON sahool.tenants(is_active) WHERE is_active = TRUE;

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_tenant ON sahool.users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON sahool.users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON sahool.users(role);

-- Farmer indexes
CREATE INDEX IF NOT EXISTS idx_farmers_tenant ON sahool.farmers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_farmers_region ON sahool.farmers(region_id);

-- Field indexes
CREATE INDEX IF NOT EXISTS idx_fields_tenant ON sahool.fields(tenant_id);
CREATE INDEX IF NOT EXISTS idx_fields_farmer ON sahool.fields(farmer_id);
CREATE INDEX IF NOT EXISTS idx_fields_region ON sahool.fields(region_id);
CREATE INDEX IF NOT EXISTS idx_fields_status ON sahool.fields(status);
CREATE INDEX IF NOT EXISTS idx_fields_crop ON sahool.fields(crop_type);
CREATE INDEX IF NOT EXISTS idx_fields_coordinates ON sahool.fields USING GIST(coordinates);

-- NDVI indexes
CREATE INDEX IF NOT EXISTS idx_ndvi_tenant ON sahool.ndvi_results(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ndvi_field ON sahool.ndvi_results(field_id);
CREATE INDEX IF NOT EXISTS idx_ndvi_date ON sahool.ndvi_results(acquisition_date DESC);
CREATE INDEX IF NOT EXISTS idx_ndvi_field_date ON sahool.ndvi_results(field_id, acquisition_date DESC);

-- Weather indexes
CREATE INDEX IF NOT EXISTS idx_weather_tenant ON sahool.weather_data(tenant_id);
CREATE INDEX IF NOT EXISTS idx_weather_region ON sahool.weather_data(region_id);
CREATE INDEX IF NOT EXISTS idx_weather_field ON sahool.weather_data(field_id);
CREATE INDEX IF NOT EXISTS idx_weather_date ON sahool.weather_data(forecast_date DESC);

-- Alert indexes
CREATE INDEX IF NOT EXISTS idx_alerts_tenant ON sahool.alerts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON sahool.alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON sahool.alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON sahool.alerts(severity);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_tenant ON sahool.audit_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON sahool.audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON sahool.audit_log(created_at DESC);

\echo 'Indexes created successfully'
EOF

    # 05 - Row Level Security
    cat > "${DB_INIT_DIR}/05-rls.sql" <<'EOF'
-- =============================================================================
-- SAHOOL Yemen - Row Level Security (Multi-tenancy)
-- =============================================================================

-- Enable RLS on all tenant tables
ALTER TABLE sahool.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sahool.farmers ENABLE ROW LEVEL SECURITY;
ALTER TABLE sahool.fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE sahool.ndvi_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE sahool.weather_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE sahool.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sahool.audit_log ENABLE ROW LEVEL SECURITY;

-- Create tenant isolation function
CREATE OR REPLACE FUNCTION sahool.current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_tenant_id', TRUE)::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Users policy
CREATE POLICY tenant_isolation_users ON sahool.users
    FOR ALL
    USING (tenant_id = sahool.current_tenant_id())
    WITH CHECK (tenant_id = sahool.current_tenant_id());

-- Farmers policy
CREATE POLICY tenant_isolation_farmers ON sahool.farmers
    FOR ALL
    USING (tenant_id = sahool.current_tenant_id())
    WITH CHECK (tenant_id = sahool.current_tenant_id());

-- Fields policy
CREATE POLICY tenant_isolation_fields ON sahool.fields
    FOR ALL
    USING (tenant_id = sahool.current_tenant_id())
    WITH CHECK (tenant_id = sahool.current_tenant_id());

-- NDVI policy
CREATE POLICY tenant_isolation_ndvi ON sahool.ndvi_results
    FOR ALL
    USING (tenant_id = sahool.current_tenant_id())
    WITH CHECK (tenant_id = sahool.current_tenant_id());

-- Weather policy
CREATE POLICY tenant_isolation_weather ON sahool.weather_data
    FOR ALL
    USING (tenant_id = sahool.current_tenant_id())
    WITH CHECK (tenant_id = sahool.current_tenant_id());

-- Alerts policy
CREATE POLICY tenant_isolation_alerts ON sahool.alerts
    FOR ALL
    USING (tenant_id = sahool.current_tenant_id())
    WITH CHECK (tenant_id = sahool.current_tenant_id());

-- Audit log policy
CREATE POLICY tenant_isolation_audit ON sahool.audit_log
    FOR ALL
    USING (tenant_id = sahool.current_tenant_id() OR tenant_id IS NULL);

\echo 'Row Level Security configured successfully'
EOF

    # 06 - Grants
    cat > "${DB_INIT_DIR}/06-grants.sql" <<'EOF'
-- =============================================================================
-- SAHOOL Yemen - Permission Grants
-- =============================================================================

-- Schema access
GRANT USAGE ON SCHEMA sahool TO sahool_app, sahool_readonly, sahool_migration, sahool_monitor;

-- Application role (CRUD)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA sahool TO sahool_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sahool TO sahool_app;

-- Readonly role (SELECT only)
GRANT SELECT ON ALL TABLES IN SCHEMA sahool TO sahool_readonly;

-- Migration role (DDL)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA sahool TO sahool_migration;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA sahool TO sahool_migration;
ALTER DEFAULT PRIVILEGES IN SCHEMA sahool GRANT ALL ON TABLES TO sahool_migration;

-- Monitor role (stats)
GRANT SELECT ON pg_stat_statements TO sahool_monitor;
GRANT pg_monitor TO sahool_monitor;

-- Future grants
ALTER DEFAULT PRIVILEGES IN SCHEMA sahool GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sahool_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA sahool GRANT SELECT ON TABLES TO sahool_readonly;

\echo 'Permissions granted successfully'
EOF

    # 07 - Seed Data (Yemen Governorates)
    cat > "${DB_INIT_DIR}/07-seed.sql" <<'EOF'
-- =============================================================================
-- SAHOOL Yemen - Seed Data (Governorates)
-- =============================================================================

INSERT INTO sahool.regions (name_ar, name_en, coordinates, climate_zone, agricultural_potential)
VALUES
    ('صنعاء', 'Sanaa', ST_SetSRID(ST_MakePoint(44.2067, 15.3694), 4326), 'highland', 'high'),
    ('عدن', 'Aden', ST_SetSRID(ST_MakePoint(45.0357, 12.7855), 4326), 'coastal', 'medium'),
    ('تعز', 'Taiz', ST_SetSRID(ST_MakePoint(44.0206, 13.5789), 4326), 'highland', 'high'),
    ('الحديدة', 'Hodeidah', ST_SetSRID(ST_MakePoint(42.9532, 14.7979), 4326), 'coastal', 'high'),
    ('إب', 'Ibb', ST_SetSRID(ST_MakePoint(44.1826, 13.9659), 4326), 'highland', 'very_high'),
    ('ذمار', 'Dhamar', ST_SetSRID(ST_MakePoint(44.4050, 14.5425), 4326), 'highland', 'high'),
    ('حجة', 'Hajjah', ST_SetSRID(ST_MakePoint(43.6034, 15.6916), 4326), 'highland', 'medium'),
    ('صعدة', 'Saada', ST_SetSRID(ST_MakePoint(43.7595, 16.9400), 4326), 'highland', 'medium'),
    ('المهرة', 'Al-Mahrah', ST_SetSRID(ST_MakePoint(52.1818, 16.5200), 4326), 'desert', 'low'),
    ('حضرموت', 'Hadramaut', ST_SetSRID(ST_MakePoint(48.7829, 15.9323), 4326), 'desert', 'low'),
    ('شبوة', 'Shabwah', ST_SetSRID(ST_MakePoint(47.0118, 14.5277), 4326), 'desert', 'low'),
    ('أبين', 'Abyan', ST_SetSRID(ST_MakePoint(45.8318, 13.5857), 4326), 'coastal', 'medium'),
    ('لحج', 'Lahij', ST_SetSRID(ST_MakePoint(44.8833, 13.0500), 4326), 'coastal', 'medium'),
    ('الضالع', 'Al-Dhale', ST_SetSRID(ST_MakePoint(44.7333, 13.7000), 4326), 'highland', 'medium'),
    ('البيضاء', 'Al-Bayda', ST_SetSRID(ST_MakePoint(45.5728, 14.1677), 4326), 'highland', 'medium'),
    ('مأرب', 'Marib', ST_SetSRID(ST_MakePoint(45.3262, 15.4642), 4326), 'desert', 'medium'),
    ('الجوف', 'Al-Jawf', ST_SetSRID(ST_MakePoint(45.5000, 16.5000), 4326), 'desert', 'low'),
    ('عمران', 'Amran', ST_SetSRID(ST_MakePoint(43.9436, 15.6592), 4326), 'highland', 'high'),
    ('المحويت', 'Al-Mahwit', ST_SetSRID(ST_MakePoint(43.5447, 15.4697), 4326), 'highland', 'high'),
    ('ريمة', 'Raymah', ST_SetSRID(ST_MakePoint(43.7167, 14.6500), 4326), 'highland', 'high'),
    ('سقطرى', 'Socotra', ST_SetSRID(ST_MakePoint(53.8237, 12.4634), 4326), 'tropical', 'medium')
ON CONFLICT DO NOTHING;

\echo 'Seed data inserted successfully'
EOF

    info "Database initialization scripts created"
}

create_pg_hba_conf() {
    info "Creating pg_hba.conf..."

    cat > "${PROJECT_ROOT}/database/postgres/pg_hba.conf" <<'EOF'
# =============================================================================
# SAHOOL Yemen - PostgreSQL Host-Based Authentication
# =============================================================================

# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Local connections
local   all             postgres                                peer
local   all             all                                     scram-sha-256

# IPv4 local connections (Docker network)
host    all             postgres        127.0.0.1/32            scram-sha-256
host    all             postgres        172.20.0.0/16           scram-sha-256

# Application connections
host    sahool_production   sahool_app      172.20.0.0/16       scram-sha-256
host    sahool_production   sahool_readonly 172.20.0.0/16       scram-sha-256
host    sahool_production   sahool_migration 172.20.0.0/16      scram-sha-256
host    sahool_production   sahool_monitor  172.20.0.0/16       scram-sha-256

# SSL required for external connections
hostssl all             all             0.0.0.0/0               scram-sha-256
hostssl all             all             ::/0                    scram-sha-256

# Deny all other connections
host    all             all             all                     reject
EOF

    info "pg_hba.conf created"
}

create_postgresql_conf() {
    info "Creating postgresql.conf..."

    cat > "${PROJECT_ROOT}/database/postgres/postgresql.conf" <<'EOF'
# =============================================================================
# SAHOOL Yemen - PostgreSQL Configuration (Hardened)
# =============================================================================

# Connection Settings
listen_addresses = '*'
port = 5432
max_connections = 200

# SSL/TLS
ssl = on
ssl_cert_file = '/var/lib/postgresql/certs/server.crt'
ssl_key_file = '/var/lib/postgresql/certs/server.key'
ssl_ca_file = '/var/lib/postgresql/certs/ca.crt'
ssl_min_protocol_version = 'TLSv1.2'
ssl_ciphers = 'HIGH:!aNULL:!MD5'

# Authentication
password_encryption = scram-sha-256

# Memory Settings
shared_buffers = 256MB
effective_cache_size = 768MB
maintenance_work_mem = 64MB
work_mem = 16MB

# Write-Ahead Log
wal_level = replica
max_wal_size = 1GB
min_wal_size = 80MB
checkpoint_completion_target = 0.9

# Query Planning
random_page_cost = 1.1
effective_io_concurrency = 200
default_statistics_target = 100

# Logging
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 0
log_statement = 'ddl'
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# pgAudit
shared_preload_libraries = 'pgaudit,pg_stat_statements'
pgaudit.log = 'ddl,role'
pgaudit.log_catalog = off
pgaudit.log_level = 'log'

# Statistics
track_activities = on
track_counts = on
track_io_timing = on
track_functions = all

# Locale
lc_messages = 'en_US.UTF-8'
lc_monetary = 'en_US.UTF-8'
lc_numeric = 'en_US.UTF-8'
lc_time = 'en_US.UTF-8'
default_text_search_config = 'pg_catalog.english'

# Timezone
timezone = 'UTC'
EOF

    info "postgresql.conf created"
}

setup_alembic() {
    info "Setting up Alembic migrations..."

    mkdir -p "${DB_MIGRATIONS_DIR}/versions"

    # Create alembic.ini
    cat > "${PROJECT_ROOT}/alembic.ini" <<'EOF'
[alembic]
script_location = database/postgres/migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

    # Create migration env.py
    cat > "${DB_MIGRATIONS_DIR}/env.py" <<'EOF'
"""Alembic migration environment."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def get_url():
    return os.getenv("DATABASE_URL", "postgresql://localhost/sahool_production")


def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

    # Create script.py.mako template
    cat > "${DB_MIGRATIONS_DIR}/script.py.mako" <<'EOF'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
EOF

    info "Alembic migrations configured"
}

# Run module
database_module
