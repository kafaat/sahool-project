// Field Types
export interface Field {
  id: number;
  name: string;
  area_hectares: number;
  crop_type: string;
  status: 'healthy' | 'warning' | 'critical';
  ndvi_current: number;
  geometry: GeoJSONPolygon;
  region: string;
  soil_type?: string;
  irrigation_type?: string;
  planting_date?: string;
  farmer_id: number;
  created_at: string;
  updated_at: string;
}

export interface GeoJSONPolygon {
  type: 'Polygon';
  coordinates: number[][][];
}

export interface GeoJSONPoint {
  type: 'Point';
  coordinates: [number, number];
}

// NDVI Types
export interface NDVIData {
  id: number;
  field_id: number;
  value: number;
  acquisition_date: string;
  satellite: string;
  cloud_coverage: number;
  analysis?: NDVIAnalysis;
}

export interface NDVIAnalysis {
  health_status: string;
  vegetation_density: string;
  recommendations: string[];
  trend: 'up' | 'down' | 'stable';
}

export interface NDVIHistory {
  date: string;
  value: number;
}

// Weather Types
export interface Weather {
  field_id: number;
  temperature: number;
  humidity: number;
  wind_speed: number;
  precipitation: number;
  condition: string;
  forecast: WeatherForecast[];
}

export interface WeatherForecast {
  date: string;
  temp_min: number;
  temp_max: number;
  condition: string;
  precipitation_chance: number;
}

// Alert Types
export interface Alert {
  id: number;
  type: 'warning' | 'critical' | 'info' | 'success';
  title: string;
  message: string;
  field_name: string;
  field_id: number;
  created_at: string;
  is_read: boolean;
  category: 'weather' | 'ndvi' | 'irrigation' | 'pest' | 'soil' | 'general';
}

// User Types
export interface User {
  id: number;
  name: string;
  email: string;
  phone?: string;
  role: 'admin' | 'farmer' | 'agronomist' | 'viewer';
  region?: string;
  total_fields?: number;
  total_area?: number;
  created_at?: string;
}

// Auth Types
export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
  phone?: string;
  region?: string;
}

// Dashboard Types
export interface DashboardData {
  totalFields: number;
  totalArea: number;
  avgNDVI: number;
  activeAlerts: number;
  weatherToday: {
    temp: number;
    condition: string;
  };
  recentAlerts: Alert[];
  fieldsSummary: FieldSummary[];
}

export interface FieldSummary {
  id: number;
  name: string;
  ndvi: number;
  status: string;
}

// Soil Types
export interface SoilData {
  field_id: number;
  ph: number;
  nitrogen: number;
  phosphorus: number;
  potassium: number;
  organic_matter: number;
  moisture: number;
  texture: string;
  analysis_date: string;
}

// AI Advisor Types
export interface AdvisorResponse {
  field_id: number;
  recommendations: Recommendation[];
  analysis_summary: string;
  confidence: number;
}

export interface Recommendation {
  type: 'irrigation' | 'fertilizer' | 'pest_control' | 'harvest' | 'general';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  action_items: string[];
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Settings Types
export interface AppSettings {
  notifications_enabled: boolean;
  alert_critical: boolean;
  alert_warning: boolean;
  alert_info: boolean;
  language: 'ar' | 'en';
  dark_mode: boolean;
  units: 'metric' | 'imperial';
}

// Navigation Types
export type RootStackParamList = {
  Login: undefined;
  Main: undefined;
  FieldDetail: { fieldId: number };
};

export type MainTabParamList = {
  Home: undefined;
  Fields: undefined;
  NDVI: { fieldId?: number } | undefined;
  Alerts: undefined;
  Profile: undefined;
};
