import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('authToken');
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
      // Token expired, logout user
      await AsyncStorage.removeItem('authToken');
      // Navigate to login screen
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // Auth
  login: (email: string, password: string) =>
    apiClient.post('/api/v1/auth/login', { email, password }),

  register: (data: any) =>
    apiClient.post('/api/v1/auth/register', data),

  // Dashboard
  getDashboard: () =>
    apiClient.get('/api/v1/dashboard'),

  // Fields
  getFields: () =>
    apiClient.get('/api/v1/fields'),

  getFieldDetail: (fieldId: number) =>
    apiClient.get(`/api/v1/fields/${fieldId}`),

  // NDVI
  getFieldNDVI: (fieldId: number) =>
    apiClient.get(`/api/v1/imagery/fields/${fieldId}/ndvi-latest`),

  getNDVIHistory: (fieldId: number) =>
    apiClient.get(`/api/v1/imagery/fields/${fieldId}/ndvi-history`),

  // Alerts
  getAlerts: () =>
    apiClient.get('/api/v1/alerts'),

  markAlertAsRead: (alertId: number) =>
    apiClient.patch(`/api/v1/alerts/${alertId}/read`),

  // Weather
  getWeather: (fieldId: number) =>
    apiClient.get(`/api/v1/weather/field/${fieldId}`),

  // Soil
  getSoilData: (fieldId: number) =>
    apiClient.get(`/api/v1/soil/field/${fieldId}`),

  // AI Agent
  getFieldAdvice: (fieldId: number) =>
    apiClient.get(`/api/v1/agent/field/${fieldId}/advice`),

  getNDVIAnalysis: (fieldId: number) =>
    apiClient.get(`/api/v1/agent/field/${fieldId}/ndvi-analysis`),
};

export default apiClient;
