/**
 * API Type Definitions
 * تعريفات أنواع API
 */

// Base types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ApiError {
  detail: string
  code?: string
  field?: string
}

// Region types
export interface Region {
  id: number
  name_ar: string
  name_en: string
  latitude: number
  longitude: number
  area_km2?: number
  population?: number
  agricultural_area_ha?: number
}

// Field types
export interface Field {
  id: string
  name: string
  region_id: number
  farmer_id: string
  area_hectares: number
  crop_type: string
  planting_date?: string
  expected_harvest_date?: string
  geometry: GeoJSONGeometry
  irrigation_type: string
  soil_type?: string
  health_status: 'healthy' | 'moderate' | 'stressed' | 'critical'
  created_at: string
  updated_at: string
}

export interface GeoJSONGeometry {
  type: 'Point' | 'Polygon' | 'MultiPolygon'
  coordinates: number[] | number[][] | number[][][]
}

// Weather types
export interface WeatherData {
  id?: string
  field_id?: string
  region_id?: number
  date: string
  temperature: number
  tmax?: number
  tmin?: number
  humidity: number
  rainfall: number
  wind_speed?: number
  wind_direction?: string
  pressure?: number
  source: string
}

export interface WeatherForecast {
  date: string
  tmax: number
  tmin: number
  rain_probability: number
  humidity: number
  description_ar: string
}

export interface WeatherAlert {
  id: string
  type: string
  severity: 'low' | 'moderate' | 'high' | 'critical'
  title_ar: string
  description_ar: string
  affected_regions: string[]
  valid_from: string
  valid_until: string
}

// NDVI types
export interface NDVIResult {
  field_id: string
  analysis_date: string
  mean_ndvi: number
  min_ndvi: number
  max_ndvi: number
  health_status: 'healthy' | 'moderate' | 'stressed' | 'critical'
  health_description_ar: string
  stress_areas_percent: number
  recommendation_ar?: string
}

export interface NDVIHistory {
  field_id: string
  data_points: NDVIDataPoint[]
}

export interface NDVIDataPoint {
  date: string
  mean_ndvi: number
  health_status: string
}

// Soil types
export interface SoilAnalysis {
  field_id: string
  sample_date: string
  ph_value: number
  nitrogen_ppm: number
  phosphorus_ppm: number
  potassium_ppm: number
  organic_matter_percent: number
  salinity_ms_cm: number
  fertility_status: string
  recommendations_ar: string[]
}

// Irrigation types
export interface IrrigationSchedule {
  id: string
  field_id: string
  scheduled_date: string
  start_time: string
  duration_minutes: number
  water_amount_liters: number
  method: string
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
  reason_ar: string
}

// Dashboard types
export interface DashboardSummary {
  total_farmers: number
  total_fields: number
  total_area_ha: number
  active_regions: number
}

export interface NDVIStatus {
  excellent: number
  good: number
  moderate: number
  poor: number
}

export interface DashboardWeather {
  avg_temp_celsius: number
  rain_probability: number
}

export interface DashboardData {
  summary: DashboardSummary
  ndvi_status: NDVIStatus
  weather: DashboardWeather
  alerts: WeatherAlert[]
}

// Analytics types
export interface YieldPrediction {
  field_id: string
  crop_type: string
  predicted_yield_ton_per_ha: number
  confidence_percent: number
  factors: YieldFactor[]
}

export interface YieldFactor {
  name: string
  impact: 'positive' | 'negative' | 'neutral'
  description_ar: string
}

export interface YieldSummary {
  farmer_id: string
  year: number
  total_yield_tons: number
  total_revenue_yer: number
  total_expenses_yer: number
  profit_yer: number
  profit_margin_percent: number
  crop_breakdown: CropYield[]
}

export interface CropYield {
  crop: string
  yield_tons: number
  revenue_yer: number
}

// Advisor types
export interface AdvisorResponse {
  analysis: string
  recommendations: Recommendation[]
  alerts: string[]
}

export interface Recommendation {
  type: 'irrigation' | 'fertilizer' | 'pest' | 'harvest' | 'general'
  priority: 'low' | 'medium' | 'high'
  title_ar: string
  description_ar: string
  action_ar: string
}

// Geo types
export interface AreaResult {
  area_ha: number
  area_m2: number
  perimeter_m: number
  centroid?: { lat: number; lon: number }
}

export interface ElevationResult {
  elevation_m: number
  slope_percent: number
  aspect_degrees?: number
  terrain_type: string
  suitability?: Record<string, string>
}

export interface ZoneInfo {
  zone_name: string
  zone_type: string
  governorate: string
  altitude_range: string
  annual_rainfall: string
  recommended_crops: string[]
  irrigation_type: string
}

// Auth types
export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'farmer' | 'agronomist' | 'viewer'
  tenant_id: string
  region_id?: number
  phone?: string
  total_fields?: number
  total_area_hectares?: number
  joined_at?: string
  subscription_tier?: string
}

export interface RegisterRequest {
  email: string
  password: string
  name: string
  phone?: string
  region_id?: number
  preferred_language?: 'ar' | 'en'
}
