-- سهول اليمن - Database Tables
-- المناطق (المحافظات)
CREATE TABLE regions (
    id SERIAL PRIMARY KEY,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    coordinates GEOGRAPHY(POINT, 4326),
    area_km2 DECIMAL(10,2),
    agricultural_potential TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- المزارعون
CREATE TABLE farmers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100),
    region_id INTEGER REFERENCES regions(id),
    tenant_id UUID NOT NULL,
    registration_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- الحقول
CREATE TABLE fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farmer_id UUID REFERENCES farmers(id),
    region_id INTEGER REFERENCES regions(id),
    tenant_id UUID NOT NULL,
    name_ar VARCHAR(200),
    area_hectares DECIMAL(10,2) NOT NULL,
    crop_type VARCHAR(100),
    coordinates GEOGRAPHY(POINT, 4326),
    elevation_meters INTEGER,
    soil_type VARCHAR(50),
    irrigation_type VARCHAR(50),
    field_geometry GEOGRAPHY(POLYGON, 4326),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- نتائج NDVI
CREATE TABLE ndvi_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id),
    tenant_id UUID NOT NULL,
    ndvi_value DECIMAL(5,3) CHECK (ndvi_value BETWEEN -1 AND 1),
    acquisition_date DATE NOT NULL,
    tile_url TEXT,
    tile_metadata JSONB DEFAULT '{}',
    cloud_coverage DECIMAL(5,2) CHECK (cloud_coverage BETWEEN 0 AND 100),
    satellite_name VARCHAR(50) DEFAULT 'Sentinel-2',
    processing_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- بيانات الطقس
CREATE TABLE weather_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    region_id INTEGER REFERENCES regions(id),
    tenant_id UUID NOT NULL,
    temperature DECIMAL(6,2),
    humidity DECIMAL(5,2),
    rainfall DECIMAL(8,2),
    wind_speed DECIMAL(6,2),
    wind_direction VARCHAR(10),
    pressure DECIMAL(7,2),
    forecast_date DATE,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- سجل الإنتاج
CREATE TABLE yield_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id),
    tenant_id UUID NOT NULL,
    crop_type VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    yield_ton_per_hectare DECIMAL(10,2),
    revenue_yer DECIMAL(15,2),
    expenses_yer DECIMAL(15,2),
    profit_yer DECIMAL(15,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- تحليل التربة
CREATE TABLE soil_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id),
    tenant_id UUID NOT NULL,
    ph_value DECIMAL(4,2),
    nitrogen_ppm DECIMAL(8,2),
    phosphorus_ppm DECIMAL(8,2),
    potassium_ppm DECIMAL(8,2),
    organic_matter_percent DECIMAL(5,2),
    salinity_ms_cm DECIMAL(6,2),
    analysis_date DATE,
    lab_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- جداول الري
CREATE TABLE irrigation_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id),
    tenant_id UUID NOT NULL,
    schedule_date DATE NOT NULL,
    water_amount_mm DECIMAL(8,2),
    irrigation_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    executed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- صحة النبات
CREATE TABLE plant_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id UUID REFERENCES fields(id),
    tenant_id UUID NOT NULL,
    disease_name VARCHAR(100),
    confidence_score DECIMAL(5,2) CHECK (confidence_score BETWEEN 0 AND 100),
    severity_level VARCHAR(20) CHECK (severity_level IN ('low', 'medium', 'high', 'critical')),
    recommendation TEXT,
    image_url TEXT,
    metadata JSONB DEFAULT '{}',
    detected_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- سجل التدقيق
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100),
    tenant_id UUID NOT NULL,
    action VARCHAR(100),
    table_name VARCHAR(100),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- إدراج بيانات المحافظات (20 محافظة يمنية)
INSERT INTO regions (name_ar, name_en, coordinates, area_km2, agricultural_potential) VALUES
('صنعاء', 'Sanaa', ST_SetSRID(ST_MakePoint(44.2067, 15.3547), 4326)::GEOGRAPHY, 12630, 'عالية - قمح, خضروات'),
('عدن', 'Aden', ST_SetSRID(ST_MakePoint(45.0339, 12.8254), 4326)::GEOGRAPHY, 1114, 'متوسطة - خضروات استوائية'),
('تعز', 'Taiz', ST_SetSRID(ST_MakePoint(44.0107, 13.5782), 4326)::GEOGRAPHY, 12213, 'عالية - قهوة, حبوب'),
('حضرموت', 'Hadramaut', ST_SetSRID(ST_MakePoint(48.8318, 15.4768), 4326)::GEOGRAPHY, 98044, 'متوسطة - نخيل, أعلاف'),
('الحديدة', 'Hudaydah', ST_SetSRID(ST_MakePoint(42.9531, 14.7974), 4326)::GEOGRAPHY, 17090, 'عالية - خضروات, حبوب'),
('إب', 'Ibb', ST_SetSRID(ST_MakePoint(43.9440, 14.1446), 4326)::GEOGRAPHY, 11770, 'عالية - قهوة, حبوب'),
('ذمار', 'Dhamar', ST_SetSRID(ST_MakePoint(44.4137, 15.5570), 4326)::GEOGRAPHY, 10100, 'عالية - قمح, حبوب'),
('شبوة', 'Shabwah', ST_SetSRID(ST_MakePoint(45.7186, 14.3801), 4326)::GEOGRAPHY, 49230, 'متوسطة - أعلاف, نخيل'),
('لحج', 'Lahij', ST_SetSRID(ST_MakePoint(44.8812, 13.0565), 4326)::GEOGRAPHY, 15730, 'متوسطة - خضروات, أعلاف'),
('أبين', 'Abyan', ST_SetSRID(ST_MakePoint(45.8824, 13.6950), 4326)::GEOGRAPHY, 21789, 'متوسطة - نخيل, حبوب'),
('مأرب', 'Marib', ST_SetSRID(ST_MakePoint(45.3406, 15.4620), 4326)::GEOGRAPHY, 20423, 'متوسطة - نخيل, أعلاف'),
('الجوف', 'Al Jawf', ST_SetSRID(ST_MakePoint(44.8154, 16.7206), 4326)::GEOGRAPHY, 44773, 'متوسطة - حبوب, خضروات'),
('عمران', 'Amran', ST_SetSRID(ST_MakePoint(43.9430, 16.2564), 4326)::GEOGRAPHY, 9250, 'عالية - قمح, خضروات'),
('حجة', 'Hajjah', ST_SetSRID(ST_MakePoint(43.3250, 16.1235), 4326)::GEOGRAPHY, 10000, 'متوسطة - حبوب, أعلاف'),
('المحويت', 'Mahwit', ST_SetSRID(ST_MakePoint(43.5400, 15.2589), 4326)::GEOGRAPHY, 2858, 'متوسطة - قهوة, حبوب'),
('ريمة', 'Raymah', ST_SetSRID(ST_MakePoint(44.5000, 14.4000), 4326)::GEOGRAPHY, 3940, 'متوسطة - حبوب, خضروات'),
('المهرة', 'Al Mahrah', ST_SetSRID(ST_MakePoint(51.8000, 16.5000), 4326)::GEOGRAPHY, 123500, 'منخفضة - أعلاف, نحل'),
('سقطرى', 'Soqatra', ST_SetSRID(ST_MakePoint(53.8000, 12.5000), 4326)::GEOGRAPHY, 3650, 'منخفضة - نباتات نادرة'),
('البيضاء', 'Al Bayda', ST_SetSRID(ST_MakePoint(45.3000, 14.2000), 4326)::GEOGRAPHY, 11170, 'متوسطة - حبوب, أعلاف'),
('صعدة', 'Saadah', ST_SetSRID(ST_MakePoint(43.7000, 16.9000), 4326)::GEOGRAPHY, 14564, 'متوسطة - حبوب, أعلاف');
