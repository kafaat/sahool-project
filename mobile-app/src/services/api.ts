import axios, { AxiosInstance, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { APP_CONFIG } from '../config';
import type {
  AuthResponse,
  LoginCredentials,
  RegisterData,
  DashboardData,
  Field,
  NDVIData,
  NDVIHistory,
  Weather,
  Alert,
  SoilData,
  AdvisorResponse,
  User,
  PaginatedResponse,
} from '../types';

const API_BASE_URL = APP_CONFIG.api.baseUrl;

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: APP_CONFIG.api.timeout,
  headers: {
    'Content-Type': 'application/json',
    'Accept-Language': 'ar',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem(APP_CONFIG.storageKeys.authToken);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, clear storage
      await AsyncStorage.multiRemove([
        APP_CONFIG.storageKeys.authToken,
        APP_CONFIG.storageKeys.refreshToken,
        APP_CONFIG.storageKeys.user,
      ]);
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // ==================== Auth ====================
  login: (credentials: LoginCredentials): Promise<AxiosResponse<AuthResponse>> =>
    apiClient.post('/api/v1/auth/login', credentials),

  register: (data: RegisterData): Promise<AxiosResponse<AuthResponse>> =>
    apiClient.post('/api/v1/auth/register', data),

  refreshToken: (refreshToken: string): Promise<AxiosResponse<AuthResponse>> =>
    apiClient.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),

  logout: (): Promise<AxiosResponse<void>> =>
    apiClient.post('/api/v1/auth/logout'),

  forgotPassword: (email: string): Promise<AxiosResponse<{ message: string }>> =>
    apiClient.post('/api/v1/auth/forgot-password', { email }),

  resetPassword: (token: string, password: string): Promise<AxiosResponse<{ message: string }>> =>
    apiClient.post('/api/v1/auth/reset-password', { token, password }),

  // ==================== User ====================
  getCurrentUser: (): Promise<AxiosResponse<User>> =>
    apiClient.get('/api/v1/users/me'),

  updateProfile: (data: Partial<User>): Promise<AxiosResponse<User>> =>
    apiClient.patch('/api/v1/users/me', data),

  changePassword: (currentPassword: string, newPassword: string): Promise<AxiosResponse<void>> =>
    apiClient.post('/api/v1/users/me/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  // ==================== Dashboard ====================
  getDashboard: (): Promise<AxiosResponse<DashboardData>> =>
    apiClient.get('/api/v1/dashboard'),

  // ==================== Fields ====================
  getFields: (params?: { page?: number; limit?: number; region?: string }): Promise<AxiosResponse<PaginatedResponse<Field>>> =>
    apiClient.get('/api/v1/fields', { params }),

  getFieldDetail: (fieldId: number): Promise<AxiosResponse<Field>> =>
    apiClient.get(`/api/v1/fields/${fieldId}`),

  createField: (data: Partial<Field>): Promise<AxiosResponse<Field>> =>
    apiClient.post('/api/v1/fields', data),

  updateField: (fieldId: number, data: Partial<Field>): Promise<AxiosResponse<Field>> =>
    apiClient.patch(`/api/v1/fields/${fieldId}`, data),

  deleteField: (fieldId: number): Promise<AxiosResponse<void>> =>
    apiClient.delete(`/api/v1/fields/${fieldId}`),

  // ==================== NDVI / Imagery ====================
  getFieldNDVI: (fieldId: number): Promise<AxiosResponse<NDVIData>> =>
    apiClient.get(`/api/v1/imagery/fields/${fieldId}/ndvi-latest`),

  getNDVIHistory: (fieldId: number, params?: { days?: number }): Promise<AxiosResponse<NDVIHistory[]>> =>
    apiClient.get(`/api/v1/imagery/fields/${fieldId}/ndvi-history`, { params }),

  requestNDVIAnalysis: (fieldId: number): Promise<AxiosResponse<{ job_id: string }>> =>
    apiClient.post(`/api/v1/imagery/fields/${fieldId}/analyze`),

  getNDVIImage: (fieldId: number, date?: string): Promise<AxiosResponse<{ url: string }>> =>
    apiClient.get(`/api/v1/imagery/fields/${fieldId}/ndvi-image`, { params: { date } }),

  // ==================== Alerts ====================
  getAlerts: (params?: { unread_only?: boolean; type?: string }): Promise<AxiosResponse<Alert[]>> =>
    apiClient.get('/api/v1/alerts', { params }),

  markAlertAsRead: (alertId: number): Promise<AxiosResponse<Alert>> =>
    apiClient.patch(`/api/v1/alerts/${alertId}/read`),

  markAllAlertsAsRead: (): Promise<AxiosResponse<{ count: number }>> =>
    apiClient.post('/api/v1/alerts/mark-all-read'),

  deleteAlert: (alertId: number): Promise<AxiosResponse<void>> =>
    apiClient.delete(`/api/v1/alerts/${alertId}`),

  // ==================== Weather ====================
  getWeather: (fieldId: number): Promise<AxiosResponse<Weather>> =>
    apiClient.get(`/api/v1/weather/field/${fieldId}`),

  getWeatherForecast: (fieldId: number, days?: number): Promise<AxiosResponse<Weather>> =>
    apiClient.get(`/api/v1/weather/field/${fieldId}/forecast`, { params: { days } }),

  getWeatherByLocation: (lat: number, lon: number): Promise<AxiosResponse<Weather>> =>
    apiClient.get('/api/v1/weather/location', { params: { lat, lon } }),

  // ==================== Soil ====================
  getSoilData: (fieldId: number): Promise<AxiosResponse<SoilData>> =>
    apiClient.get(`/api/v1/soil/field/${fieldId}`),

  getSoilHistory: (fieldId: number): Promise<AxiosResponse<SoilData[]>> =>
    apiClient.get(`/api/v1/soil/field/${fieldId}/history`),

  // ==================== AI Advisor ====================
  getFieldAdvice: (fieldId: number): Promise<AxiosResponse<AdvisorResponse>> =>
    apiClient.get(`/api/v1/advisor/field/${fieldId}/advice`),

  getNDVIAnalysis: (fieldId: number): Promise<AxiosResponse<AdvisorResponse>> =>
    apiClient.get(`/api/v1/advisor/field/${fieldId}/ndvi-analysis`),

  getIrrigationRecommendation: (fieldId: number): Promise<AxiosResponse<AdvisorResponse>> =>
    apiClient.get(`/api/v1/advisor/field/${fieldId}/irrigation`),

  askQuestion: (fieldId: number, question: string): Promise<AxiosResponse<{ answer: string }>> =>
    apiClient.post(`/api/v1/advisor/field/${fieldId}/ask`, { question }),

  // ==================== Analytics ====================
  getFieldAnalytics: (fieldId: number, period?: string): Promise<AxiosResponse<any>> =>
    apiClient.get(`/api/v1/analytics/field/${fieldId}`, { params: { period } }),

  getRegionAnalytics: (regionId: string): Promise<AxiosResponse<any>> =>
    apiClient.get(`/api/v1/analytics/region/${regionId}`),

  // ==================== Regions ====================
  getRegions: (): Promise<AxiosResponse<any[]>> =>
    apiClient.get('/api/v1/regions'),

  getRegionDetail: (regionId: string): Promise<AxiosResponse<any>> =>
    apiClient.get(`/api/v1/regions/${regionId}`),
};

export default apiClient;
