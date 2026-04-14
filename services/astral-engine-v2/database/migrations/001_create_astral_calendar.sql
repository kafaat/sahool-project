-- قاعدة بيانات الطوالع الفلكية - Yemen Edition
-- Created for SAHOOL Platform v2.1

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS astral_calendar (
    id SERIAL PRIMARY KEY,
    noue_name_ar VARCHAR(100) NOT NULL,
    noue_name_en VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration_days INTEGER,
    moon_phase JSONB,
    agricultural_impact JSONB NOT NULL,
    crop_specific_effects JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_astral_start_date ON astral_calendar(start_date);
CREATE INDEX IF NOT EXISTS idx_astral_end_date ON astral_calendar(end_date);
CREATE INDEX IF NOT EXISTS idx_astral_noue_name ON astral_calendar(noue_name_ar);
