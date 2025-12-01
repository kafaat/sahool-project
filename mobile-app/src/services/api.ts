import axios, { AxiosInstance } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// API Configuration
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:9000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('userToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      await AsyncStorage.removeItem('userToken');
      await AsyncStorage.removeItem('userData');
      // Navigation will be handled by the component
    }
    return Promise.reject(error);
  }
);

// Authentication APIs
export const login = async (email: string, password: string) => {
  const response = await apiClient.post('/api/v1/auth/login', { email, password });
  return response.data;
};

export const register = async (userData: { name: string; email: string; password: string }) => {
  const response = await apiClient.post('/api/v1/auth/register', userData);
  return response.data;
};

// Dashboard APIs
export const getDashboard = async () => {
  const response = await apiClient.get('/api/v1/dashboard');
  return response.data;
};

// Fields APIs
export const getFields = async () => {
  const response = await apiClient.get('/api/geo/fields');
  return response.data;
};

export const getFieldDetails = async (fieldId: number) => {
  const response = await apiClient.get(`/api/geo/fields/${fieldId}`);
  return response.data;
};

export const createField = async (fieldData: any) => {
  const response = await apiClient.post('/api/geo/fields', fieldData);
  return response.data;
};

// NDVI APIs
export const getNDVIData = async (fieldId: number) => {
  const response = await apiClient.get(`/api/imagery/fields/${fieldId}/ndvi-latest`);
  return response.data;
};

export const getNDVIHistory = async (fieldId: number, days: number = 30) => {
  const response = await apiClient.get(`/api/imagery/fields/${fieldId}/ndvi-history`, {
    params: { days },
  });
  return response.data;
};

// Weather APIs
export const getFieldWeather = async (fieldId: number) => {
  const response = await apiClient.get(`/api/weather/field/${fieldId}`);
  return response.data;
};

// Alerts APIs
export const getAlerts = async (params?: any) => {
  const response = await apiClient.get('/api/alerts/alerts', { params });
  return response.data;
};

export const markAlertAsRead = async (alertId: number) => {
  const response = await apiClient.put(`/api/alerts/alerts/${alertId}/read`);
  return response.data;
};

// AI Agent APIs
export const getFieldAdvice = async (fieldId: number) => {
  const response = await apiClient.get(`/api/agent/field/${fieldId}/advice`);
  return response.data;
};

export const getNDVIAnalysis = async (fieldId: number) => {
  const response = await apiClient.get(`/api/agent/field/${fieldId}/ndvi-analysis`);
  return response.data;
};

// Soil APIs
export const getSoilData = async (fieldId: number) => {
  const response = await apiClient.get(`/api/soil/field/${fieldId}`);
  return response.data;
};

// User Profile APIs
export const getUserProfile = async () => {
  const response = await apiClient.get('/api/v1/users/me');
  return response.data;
};

export const updateUserProfile = async (userData: any) => {
  const response = await apiClient.put('/api/v1/users/me', userData);
  return response.data;
};

// Export configured axios instance
export default apiClient;
