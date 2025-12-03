-- سهول اليمن - Database Indexes
-- فهارس الأداء
CREATE INDEX idx_fields_region ON fields(region_id);
CREATE INDEX idx_fields_farmer ON fields(farmer_id);
CREATE INDEX idx_fields_tenant ON fields(tenant_id);
CREATE INDEX idx_fields_crop ON fields(crop_type);
CREATE INDEX idx_ndvi_field ON ndvi_results(field_id);
CREATE INDEX idx_ndvi_tenant ON ndvi_results(tenant_id);
CREATE INDEX idx_ndvi_date ON ndvi_results(acquisition_date DESC);
CREATE INDEX idx_weather_region ON weather_data(region_id);
CREATE INDEX idx_weather_tenant ON weather_data(tenant_id);
CREATE INDEX idx_weather_date ON weather_data(forecast_date);
CREATE INDEX idx_yield_field ON yield_records(field_id);
CREATE INDEX idx_yield_tenant ON yield_records(tenant_id);
CREATE INDEX idx_yield_year ON yield_records(year DESC);
CREATE INDEX idx_soil_field ON soil_analysis(field_id);
CREATE INDEX idx_soil_tenant ON soil_analysis(tenant_id);
CREATE INDEX idx_irrigation_field ON irrigation_schedules(field_id);
CREATE INDEX idx_irrigation_tenant ON irrigation_schedules(tenant_id);
CREATE INDEX idx_health_field ON plant_health(field_id);
CREATE INDEX idx_health_tenant ON plant_health(tenant_id);
CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_date ON audit_logs(created_at DESC);

-- فهارس المساحات الجغرافية
CREATE INDEX idx_fields_location ON fields USING GIST(coordinates);
CREATE INDEX idx_fields_geometry ON fields USING GIST(field_geometry);
CREATE INDEX idx_regions_location ON regions USING GIST(coordinates);

-- فهارس النصوص الكاملة
CREATE INDEX idx_fields_name_ar ON fields USING gin(to_tsvector('arabic', name_ar));
CREATE INDEX idx_farmers_name ON farmers USING gin(to_tsvector('arabic', name));

-- فهارس JSONB للبيانات الوصفية
CREATE INDEX idx_ndvi_tile_metadata ON ndvi_results USING gin(tile_metadata);
CREATE INDEX idx_health_metadata ON plant_health USING gin(metadata);
CREATE INDEX idx_audit_old_values ON audit_logs USING gin(old_values);
CREATE INDEX idx_audit_new_values ON audit_logs USING gin(new_values);

-- فهارس مركّبة للاستعلامات الشائعة
CREATE INDEX idx_ndvi_field_date ON ndvi_results(field_id, acquisition_date DESC);
CREATE INDEX idx_weather_region_date ON weather_data(region_id, forecast_date DESC);
CREATE INDEX idx_health_field_severity ON plant_health(field_id, severity_level);
