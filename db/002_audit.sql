-- =============================================================================
-- SAHOOL Platform v6.8.4 - Audit System
-- منصة سهول - نظام التدقيق
-- SOC2/GDPR Compliant Audit Trail
-- =============================================================================

SET search_path TO sahool, public;

-- =============================================================================
-- Audit Log Table - جدول سجل التدقيق
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Who
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    user_role VARCHAR(50),

    -- What
    action VARCHAR(50) NOT NULL,  -- CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT, etc.
    resource_type VARCHAR(100) NOT NULL,  -- Table/entity name
    resource_id VARCHAR(100),  -- Primary key of affected record

    -- Details
    old_values JSONB,  -- Previous state (for UPDATE/DELETE)
    new_values JSONB,  -- New state (for CREATE/UPDATE)
    changes JSONB,     -- Diff of changes

    -- Context
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    session_id VARCHAR(100),

    -- Metadata
    severity VARCHAR(20) DEFAULT 'info',  -- info, warning, error, critical
    status VARCHAR(20) DEFAULT 'success',  -- success, failure
    error_message TEXT,
    metadata JSONB DEFAULT '{}',

    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_severity ON audit_logs(severity);
CREATE INDEX idx_audit_ip ON audit_logs(ip_address);

-- Composite index for common queries
CREATE INDEX idx_audit_tenant_action_date ON audit_logs(tenant_id, action, created_at DESC);

-- =============================================================================
-- GDPR Data Subject Requests Table - طلبات أصحاب البيانات
-- =============================================================================
CREATE TABLE IF NOT EXISTS gdpr_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Request Details
    request_type VARCHAR(50) NOT NULL,  -- access, rectification, erasure, portability, restriction
    requester_email VARCHAR(255) NOT NULL,
    requester_name VARCHAR(200),

    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, in_progress, completed, rejected
    assigned_to UUID REFERENCES users(id),

    -- Processing
    received_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    deadline_at TIMESTAMPTZ,  -- Usually 30 days from received_at

    -- Details
    description TEXT,
    response TEXT,
    data_exported JSONB,  -- For portability requests

    -- Audit
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_gdpr_tenant ON gdpr_requests(tenant_id);
CREATE INDEX idx_gdpr_status ON gdpr_requests(status);
CREATE INDEX idx_gdpr_type ON gdpr_requests(request_type);

-- =============================================================================
-- Data Retention Policies Table - سياسات الاحتفاظ بالبيانات
-- =============================================================================
CREATE TABLE IF NOT EXISTS retention_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,

    resource_type VARCHAR(100) NOT NULL,
    retention_days INTEGER NOT NULL DEFAULT 365,
    archive_after_days INTEGER,
    delete_after_days INTEGER,

    is_active BOOLEAN DEFAULT TRUE,
    last_cleanup_at TIMESTAMPTZ,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_retention_tenant ON retention_policies(tenant_id);
CREATE INDEX idx_retention_resource ON retention_policies(resource_type);

-- =============================================================================
-- Security Events Table - أحداث الأمان
-- =============================================================================
CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,

    event_type VARCHAR(100) NOT NULL,  -- login_failed, password_changed, role_changed, etc.
    severity VARCHAR(20) NOT NULL DEFAULT 'info',

    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),

    ip_address INET,
    user_agent TEXT,
    location_country VARCHAR(100),
    location_city VARCHAR(100),

    description TEXT,
    blocked BOOLEAN DEFAULT FALSE,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_security_tenant ON security_events(tenant_id);
CREATE INDEX idx_security_type ON security_events(event_type);
CREATE INDEX idx_security_severity ON security_events(severity);
CREATE INDEX idx_security_user ON security_events(user_id);
CREATE INDEX idx_security_ip ON security_events(ip_address);
CREATE INDEX idx_security_created ON security_events(created_at DESC);

-- =============================================================================
-- Audit Trigger Function
-- =============================================================================
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    audit_user_id UUID;
    audit_tenant_id UUID;
    audit_changes JSONB;
    old_data JSONB;
    new_data JSONB;
BEGIN
    -- Get user context (set by application)
    audit_user_id := NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID;
    audit_tenant_id := NULLIF(current_setting('app.current_tenant_id', TRUE), '')::UUID;

    -- Prepare data
    IF TG_OP = 'DELETE' THEN
        old_data := to_jsonb(OLD);
        new_data := NULL;
        audit_changes := NULL;
    ELSIF TG_OP = 'INSERT' THEN
        old_data := NULL;
        new_data := to_jsonb(NEW);
        audit_changes := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        old_data := to_jsonb(OLD);
        new_data := to_jsonb(NEW);
        -- Calculate changes (fields that differ)
        SELECT jsonb_object_agg(key, value)
        INTO audit_changes
        FROM (
            SELECT key, jsonb_build_object('old', old_data->key, 'new', new_data->key) as value
            FROM jsonb_object_keys(new_data) AS key
            WHERE old_data->key IS DISTINCT FROM new_data->key
              AND key NOT IN ('updated_at', 'created_at')  -- Exclude timestamp changes
        ) AS changes;
    END IF;

    -- Skip if no actual changes
    IF TG_OP = 'UPDATE' AND audit_changes IS NULL THEN
        RETURN NEW;
    END IF;

    -- Insert audit record
    INSERT INTO sahool.audit_logs (
        tenant_id,
        user_id,
        action,
        resource_type,
        resource_id,
        old_values,
        new_values,
        changes
    ) VALUES (
        COALESCE(audit_tenant_id,
            CASE WHEN TG_OP = 'DELETE' THEN (OLD).tenant_id
                 ELSE (NEW).tenant_id END),
        audit_user_id,
        TG_OP,
        TG_TABLE_NAME,
        CASE WHEN TG_OP = 'DELETE' THEN (OLD).id::TEXT
             ELSE (NEW).id::TEXT END,
        old_data,
        new_data,
        audit_changes
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Apply Audit Triggers to Important Tables
-- =============================================================================
DO $$
DECLARE
    tables_to_audit TEXT[] := ARRAY[
        'users', 'fields', 'farmers', 'alerts',
        'ndvi_results', 'weather_data', 'irrigation_schedules',
        'yield_records', 'soil_analysis', 'plant_health'
    ];
    t TEXT;
BEGIN
    FOREACH t IN ARRAY tables_to_audit
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS audit_trigger ON sahool.%I;
            CREATE TRIGGER audit_trigger
                AFTER INSERT OR UPDATE OR DELETE ON sahool.%I
                FOR EACH ROW
                EXECUTE FUNCTION audit_trigger_function();
        ', t, t);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Helper Functions
-- =============================================================================

-- Function to log security events
CREATE OR REPLACE FUNCTION log_security_event(
    p_tenant_id UUID,
    p_event_type VARCHAR(100),
    p_severity VARCHAR(20),
    p_user_id UUID DEFAULT NULL,
    p_user_email VARCHAR(255) DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_description TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    event_id UUID;
BEGIN
    INSERT INTO sahool.security_events (
        tenant_id, event_type, severity, user_id, user_email,
        ip_address, description, metadata
    ) VALUES (
        p_tenant_id, p_event_type, p_severity, p_user_id, p_user_email,
        p_ip_address, p_description, p_metadata
    ) RETURNING id INTO event_id;

    RETURN event_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get audit trail for a resource
CREATE OR REPLACE FUNCTION get_audit_trail(
    p_resource_type VARCHAR(100),
    p_resource_id VARCHAR(100),
    p_limit INTEGER DEFAULT 100
) RETURNS TABLE (
    id UUID,
    action VARCHAR(50),
    user_email VARCHAR(255),
    changes JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.action,
        COALESCE(a.user_email, u.email) as user_email,
        a.changes,
        a.created_at
    FROM sahool.audit_logs a
    LEFT JOIN sahool.users u ON a.user_id = u.id
    WHERE a.resource_type = p_resource_type
      AND a.resource_id = p_resource_id
    ORDER BY a.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function for GDPR data export
CREATE OR REPLACE FUNCTION export_user_data(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'user', (SELECT to_jsonb(u.*) - 'password_hash' FROM sahool.users u WHERE u.id = p_user_id),
        'fields', (SELECT COALESCE(jsonb_agg(to_jsonb(f.*)), '[]'::jsonb) FROM sahool.fields f WHERE f.tenant_id = (SELECT tenant_id FROM sahool.users WHERE id = p_user_id)),
        'audit_logs', (SELECT COALESCE(jsonb_agg(to_jsonb(a.*)), '[]'::jsonb) FROM sahool.audit_logs a WHERE a.user_id = p_user_id),
        'exported_at', NOW()
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to anonymize user data (Right to Erasure)
CREATE OR REPLACE FUNCTION anonymize_user(p_user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Anonymize user record
    UPDATE sahool.users
    SET
        email = 'deleted_' || id::TEXT || '@anonymized.local',
        full_name = 'Deleted User',
        phone = NULL,
        avatar_url = NULL,
        password_hash = 'DELETED',
        is_active = FALSE,
        settings = '{}'
    WHERE id = p_user_id;

    -- Log the action
    INSERT INTO sahool.audit_logs (
        user_id, action, resource_type, resource_id,
        metadata, severity
    ) VALUES (
        p_user_id, 'GDPR_ERASURE', 'users', p_user_id::TEXT,
        '{"reason": "Right to Erasure request"}', 'warning'
    );

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Data Cleanup Job (should be run periodically)
-- =============================================================================
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(retention_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sahool.audit_logs
    WHERE created_at < NOW() - (retention_days || ' days')::INTERVAL
      AND severity NOT IN ('error', 'critical');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Log the cleanup
    INSERT INTO sahool.audit_logs (
        action, resource_type, metadata
    ) VALUES (
        'CLEANUP', 'audit_logs',
        jsonb_build_object('deleted_count', deleted_count, 'retention_days', retention_days)
    );

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Default Retention Policies
-- =============================================================================
INSERT INTO retention_policies (resource_type, retention_days, archive_after_days)
VALUES
    ('audit_logs', 365, 90),
    ('security_events', 730, 180),
    ('weather_data', 1095, 365),
    ('ndvi_results', 1825, 730)
ON CONFLICT DO NOTHING;

-- =============================================================================
-- Grants
-- =============================================================================
GRANT SELECT, INSERT ON sahool.audit_logs TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON sahool.gdpr_requests TO PUBLIC;
GRANT SELECT ON sahool.retention_policies TO PUBLIC;
GRANT SELECT, INSERT ON sahool.security_events TO PUBLIC;
