import axios, { AxiosInstance, AxiosError, AxiosResponse } from "axios";
import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";
import { ApiResponse, ApiError, Field, WeatherData, NDVIEntry, Alert, Equipment, Zone } from "../../types";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:9000/api";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        const token = await SecureStore.getItemAsync("sahool_token");
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        config.headers["X-Tenant-ID"] = process.env.EXPO_PUBLIC_TENANT_ID;
        config.headers["X-Client-Version"] = "5.5.0";
        config.headers["X-Platform"] = Platform.OS;
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          await SecureStore.deleteItemAsync("sahool_token");
        }
        return Promise.reject(error);
      }
    );
  }

  // Geo Service
  async getFields(tenantId: string): Promise<AxiosResponse<ApiResponse<Field[]>>> {
    return this.client.get(`/geo/fields?tenantId=${tenantId}`);
  }

  async getFieldDetails(fieldId: string): Promise<AxiosResponse<ApiResponse<Field>>> {
    return this.client.get(`/geo/fields/${fieldId}`);
  }

  async getEquipmentLocation(equipmentId: string): Promise<AxiosResponse<ApiResponse<Equipment>>> {
    return this.client.get(`/geo/equipment/${equipmentId}/location`);
  }

  // Weather Service
  async getWeatherData(lat: number, lon: number): Promise<AxiosResponse<ApiResponse<WeatherData>>> {
    return this.client.get(`/weather/forecast?lat=${lat}&lon=${lon}`);
  }

  // Imagery Service
  async getNDVITimeline(fieldId: string): Promise<AxiosResponse<ApiResponse<NDVIEntry[]>>> {
    return this.client.get(`/imagery/ndvi/${fieldId}/timeline`);
  }

  // Zones Service
  async getManagementZones(fieldId: string): Promise<AxiosResponse<ApiResponse<Zone[]>>> {
    return this.client.get(`/zones/field/${fieldId}`);
  }

  // AI Assistant
  async chatWithAI(message: string, context: any): Promise<AxiosResponse<ApiResponse<{ reply: string }>>> {
    return this.client.post("/agent/chat", {
      message,
      context,
      timestamp: new Date().toISOString(),
    });
  }

  // Alerts
  async getActiveAlerts(tenantId: string): Promise<AxiosResponse<ApiResponse<Alert[]>>> {
    return this.client.get(`/alerts/active?tenantId=${tenantId}`);
  }
}

export const api = new ApiClient();
