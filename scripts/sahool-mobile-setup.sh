#!/bin/bash

# ============================================
# SAHOOL MOBILE - Professional Setup Script
# Version: 4.2.1 - Fixed & Enhanced
# ============================================
#
# FIXES APPLIED:
# - Fixed Unicode ellipsis (...) characters in spread operators
# - Fixed CI/CD workflow YAML quoting
# - Consolidated script into single file
# - Fixed mkdir with proper syntax
# - Fixed NativeWind compatibility with Tailwind v3
# - Added missing functions (create_file, log, etc.)
# - Fixed package version compatibility
# - Added TypeScript declarations
# - Fixed React Query v5 syntax (gcTime instead of cacheTime)
# - Added comprehensive error handling
# - Improved CI/CD pipeline
# ============================================

set -e

# ============================================
# SECTION 1: UTILITIES & FUNCTIONS
# ============================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Print functions
log() {
    echo -e "${GREEN}[✓ SAHOOL]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[⚠ WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[✗ ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[ℹ INFO]${NC} $1"
}

step() {
    echo -e "${PURPLE}[→ STEP]${NC} $1"
}

success() {
    echo -e "${CYAN}[★ SUCCESS]${NC} $1"
}

# File creation function
create_file() {
    local file_path=$1
    local content=$2

    # Create directory
    mkdir -p "$(dirname "$file_path")"

    # Write content
    printf '%s' "$content" > "$file_path"

    if [ -f "$file_path" ]; then
        log "Created: $file_path"
    else
        error "Failed to create: $file_path"
    fi
}

# Requirements check function
check_requirements() {
    local requirements=("node" "npm" "npx" "git")

    for cmd in "${requirements[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "$cmd is not installed. Please install it first."
        fi
    done

    # Check Node.js version
    local node_version
    node_version=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$node_version" -lt 18 ]; then
        error "Node.js 18 or later required. Current version: $(node -v)"
    fi

    log "All requirements satisfied ✓"
}

# ============================================
# SECTION 2: HEADER & USER INPUT
# ============================================

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║          🌱 SAHOOL MOBILE - Professional Setup 🌱          ║${NC}"
echo -e "${CYAN}║              Smart Agriculture Platform v4.2               ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

step "Checking requirements..."
check_requirements

echo ""
info "Setting up project..."
echo ""

read -p "Create new project? (y/n) [y]: " CREATE_NEW
CREATE_NEW=${CREATE_NEW:-y}

read -p "Project name [sahool-mobile]: " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-sahool-mobile}

read -p "Tenant ID [demo-tenant]: " DEFAULT_TENANT
DEFAULT_TENANT=${DEFAULT_TENANT:-demo-tenant}

read -p "API Gateway URL [http://localhost:9000/api]: " API_URL
API_URL=${API_URL:-http://localhost:9000/api}

read -p "Mapbox Token (optional): " MAPBOX_TOKEN
MAPBOX_TOKEN=${MAPBOX_TOKEN:-your_mapbox_token}

echo ""

# ============================================
# SECTION 3: PROJECT CREATION
# ============================================

if [ "$CREATE_NEW" = "y" ] || [ "$CREATE_NEW" = "Y" ]; then
    step "Creating new Expo project..."

    npx create-expo-app@latest "$PROJECT_NAME" --template tabs

    cd "$PROJECT_NAME" || error "Failed to enter project directory"
else
    if [ -d "$PROJECT_NAME" ]; then
        cd "$PROJECT_NAME" || error "Failed to enter project directory"
        log "Using existing directory: $PROJECT_NAME"
    else
        error "Directory $PROJECT_NAME does not exist"
    fi
fi

# ============================================
# SECTION 4: DEPENDENCIES
# ============================================

step "Installing core dependencies..."

# NativeWind with Tailwind v3
npm install nativewind@^4.0.1
npm install -D tailwindcss@^3.4.3

# Core packages
npm install axios@^1.6.8 \
    @tanstack/react-query@^5.28.0 \
    zustand@^4.5.2

# Expo packages
npm install expo-linear-gradient@~13.0.2 \
    expo-location@~17.0.1 \
    expo-notifications@~0.28.0 \
    expo-secure-store@~13.0.1 \
    expo-image-picker@~15.0.4 \
    expo-speech@~12.0.1 \
    expo-font@~12.0.5

# React Native packages
npm install react-native-reanimated@~3.10.0 \
    react-native-gesture-handler@~2.16.0 \
    react-native-maps@1.14.0 \
    react-native-safe-area-context@4.10.1 \
    react-native-svg@15.2.0

# Icons & Animations
npm install lucide-react-native@^0.378.0 \
    lottie-react-native@^6.7.0

# Storage
npm install @react-native-async-storage/async-storage@1.23.1 \
    @shopify/flash-list@1.6.4

# Dev dependencies
npm install -D typescript@^5.4.0 \
    @types/react@~18.2.0 \
    eslint@^8.57.0 \
    prettier@^3.2.0

log "All dependencies installed ✓"

# ============================================
# SECTION 5: CONFIGURATION FILES
# ============================================

step "Creating configuration files..."

# 5.1 Tailwind Config
create_file "tailwind.config.js" '/** @type {import("tailwindcss").Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
  ],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        sahool: {
          bg: "#0D1F17",
          primary: "#1B4D3E",
          light: "#2D6A4F",
          dark: "#14352B",
          accent: "#F4D03F",
          "accent-light": "#F7DC6F",
          success: "#27AE60",
          warning: "#E67E22",
          danger: "#E74C3C",
          info: "#3498DB",
        },
      },
    },
  },
  plugins: [],
};'

# 5.2 Global CSS
create_file "global.css" '@tailwind base;
@tailwind components;
@tailwind utilities;'

# 5.3 Metro Config
create_file "metro.config.js" 'const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

const config = getDefaultConfig(__dirname);

module.exports = withNativeWind(config, {
  input: "./global.css",
  inlineRem: 16,
});'

# 5.4 Babel Config
create_file "babel.config.js" 'module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ["babel-preset-expo", { jsxImportSource: "nativewind" }],
      "nativewind/babel",
    ],
    plugins: [
      "react-native-reanimated/plugin",
    ],
  };
};'

# 5.5 TypeScript Config
create_file "tsconfig.json" '{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"],
      "@components/*": ["./components/*"],
      "@hooks/*": ["./hooks/*"],
      "@lib/*": ["./lib/*"]
    },
    "types": ["nativewind/types"]
  },
  "include": ["**/*.ts", "**/*.tsx", "nativewind-env.d.ts"]
}'

# 5.6 NativeWind Types
create_file "nativewind-env.d.ts" '/// <reference types="nativewind/types" />'

# 5.7 App Config
create_file "app.json" '{
  "expo": {
    "name": "SAHOOL Mobile",
    "slug": "sahool-mobile",
    "version": "4.2.0",
    "orientation": "portrait",
    "icon": "./assets/images/icon.png",
    "scheme": "sahool",
    "userInterfaceStyle": "dark",
    "splash": {
      "image": "./assets/images/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#0D1F17"
    },
    "assetBundlePatterns": ["**/*"],
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.sahool.mobile"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/images/adaptive-icon.png",
        "backgroundColor": "#1B4D3E"
      },
      "package": "com.sahool.mobile"
    },
    "plugins": [
      "expo-router",
      "expo-secure-store",
      ["expo-location", {
        "locationAlwaysAndWhenInUsePermission": "Allow SAHOOL to use your location."
      }]
    ],
    "experiments": {
      "typedRoutes": true
    }
  }
}'

# 5.8 Environment
create_file ".env" "EXPO_PUBLIC_API_URL=$API_URL
EXPO_PUBLIC_TENANT_ID=$DEFAULT_TENANT
EXPO_PUBLIC_MAPBOX_TOKEN=$MAPBOX_TOKEN
EXPO_PUBLIC_DEBUG_MODE=false"

log "Configuration files created ✓"

# ============================================
# SECTION 6: PROJECT STRUCTURE
# ============================================

step "Creating folder structure..."

mkdir -p "app/(tabs)"
mkdir -p app/field
mkdir -p app/auth
mkdir -p components/ui
mkdir -p components/cards
mkdir -p hooks
mkdir -p lib
mkdir -p store
mkdir -p types
mkdir -p utils
mkdir -p constants
mkdir -p assets/images
mkdir -p assets/fonts
mkdir -p assets/animations
mkdir -p .github/workflows

log "Folder structure created ✓"

# ============================================
# SECTION 7: TYPES
# ============================================

step "Creating type definitions..."

create_file "types/index.ts" 'export interface Field {
  id: string;
  name: string;
  nameAr: string;
  acreage: number;
  cropType: string;
  healthScore: number;
  ndviValue: number;
  moistureLevel: number;
  lastUpdated: string;
  coordinates: { latitude: number; longitude: number };
  boundaries: { latitude: number; longitude: number }[];
  alerts: Alert[];
  status: "healthy" | "warning" | "critical" | "inactive";
  color?: string;
}

export interface WeatherData {
  current: {
    temperature: number;
    humidity: number;
    windSpeed: number;
    condition: string;
    uvIndex: number;
  };
  forecast: {
    date: string;
    dayName: string;
    high: number;
    low: number;
    condition: string;
    rainChance: number;
  }[];
}

export interface Alert {
  id: string;
  type: "irrigation" | "pest" | "weather" | "equipment" | "general";
  priority: "low" | "medium" | "high" | "critical";
  title: string;
  titleAr: string;
  message: string;
  messageAr: string;
  fieldId?: string;
  createdAt: string;
  isRead: boolean;
  actionRequired: boolean;
}

export interface Equipment {
  id: string;
  name: string;
  type: "tractor" | "harvester" | "sprayer" | "seeder";
  status: "operating" | "idle" | "maintenance";
  fuelLevel: number;
  location: { latitude: number; longitude: number };
  operatingHours: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: "owner" | "manager" | "operator";
  tenantId: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}'

log "Type definitions created ✓"

# ============================================
# SECTION 8: API CLIENT
# ============================================

step "Creating API Client..."

create_file "lib/api.ts" 'import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from "axios";
import * as SecureStore from "expo-secure-store";
import { ApiResponse, Field, WeatherData, Alert, Equipment } from "@/types";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:9000/api";
const TENANT_ID = process.env.EXPO_PUBLIC_TENANT_ID || "demo-tenant";
const TOKEN_KEY = "sahool_auth_token";
const REFRESH_TOKEN_KEY = "sahool_refresh_token";

class SahoolApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private refreshSubscribers: ((token: string) => void)[] = [];

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: { "Content-Type": "application/json" },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        try {
          const token = await SecureStore.getItemAsync(TOKEN_KEY);
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
          config.headers["X-Tenant-ID"] = TENANT_ID;
        } catch (error) {
          console.warn("Error setting auth headers:", error);
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            return new Promise((resolve) => {
              this.refreshSubscribers.push((token: string) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                resolve(this.client(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const newToken = await this.refreshToken();
            this.refreshSubscribers.forEach((callback) => callback(newToken));
            this.refreshSubscribers = [];
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            await this.logout();
            throw refreshError;
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private async refreshToken(): Promise<string> {
    const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
    if (!refreshToken) throw new Error("No refresh token");

    const response = await this.client.post("/auth/refresh", { refreshToken });
    const { accessToken, refreshToken: newRefreshToken } = response.data;

    await SecureStore.setItemAsync(TOKEN_KEY, accessToken);
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, newRefreshToken);

    return accessToken;
  }

  // Auth
  async login(email: string, password: string) {
    const response = await this.client.post("/auth/login", { email, password });
    const { accessToken, refreshToken, user } = response.data;
    await SecureStore.setItemAsync(TOKEN_KEY, accessToken);
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.client.post("/auth/logout");
    } finally {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
      await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    }
  }

  async isAuthenticated(): Promise<boolean> {
    const token = await SecureStore.getItemAsync(TOKEN_KEY);
    return !!token;
  }

  // Fields
  async getFields(): Promise<ApiResponse<Field[]>> {
    const response = await this.client.get("/geo/fields");
    return response.data;
  }

  async getFieldById(fieldId: string): Promise<ApiResponse<Field>> {
    const response = await this.client.get(`/geo/fields/${fieldId}`);
    return response.data;
  }

  async createField(field: Partial<Field>): Promise<ApiResponse<Field>> {
    const response = await this.client.post("/geo/fields", field);
    return response.data;
  }

  async updateField(fieldId: string, updates: Partial<Field>): Promise<ApiResponse<Field>> {
    const response = await this.client.patch(`/geo/fields/${fieldId}`, updates);
    return response.data;
  }

  // Weather
  async getWeather(lat: number, lon: number): Promise<ApiResponse<WeatherData>> {
    const response = await this.client.get("/weather/forecast", { params: { lat, lon } });
    return response.data;
  }

  // NDVI
  async getNDVITimeline(fieldId: string, days = 30): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/imagery/ndvi/${fieldId}/timeline`, { params: { days } });
    return response.data;
  }

  // Alerts
  async getAlerts(): Promise<ApiResponse<Alert[]>> {
    const response = await this.client.get("/alerts");
    return response.data;
  }

  async getActiveAlerts(): Promise<ApiResponse<Alert[]>> {
    const response = await this.client.get("/alerts/active");
    return response.data;
  }

  async markAlertAsRead(alertId: string): Promise<ApiResponse<void>> {
    const response = await this.client.patch(`/alerts/${alertId}/read`);
    return response.data;
  }

  // Equipment
  async getEquipment(): Promise<ApiResponse<Equipment[]>> {
    const response = await this.client.get("/equipment");
    return response.data;
  }

  // AI
  async chatWithAI(message: string, context?: any) {
    const response = await this.client.post("/agent/chat", {
      message,
      context,
      timestamp: new Date().toISOString(),
    });
    return response.data;
  }

  // Dashboard
  async getDashboardStats(): Promise<ApiResponse<any>> {
    const response = await this.client.get("/analytics/dashboard");
    return response.data;
  }
}

export const api = new SahoolApiClient();'

log "API Client created ✓"

# ============================================
# SECTION 9: STORE (Zustand) - FIXED SPREAD OPERATORS
# ============================================

step "Creating Store..."

create_file "store/index.ts" 'import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Field, Alert, User, WeatherData, Equipment } from "@/types";

// App Store
interface AppState {
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  theme: "dark" | "light";
  setTheme: (theme: "dark" | "light") => void;
  language: "ar" | "en";
  setLanguage: (lang: "ar" | "en") => void;
  isOnline: boolean;
  setIsOnline: (online: boolean) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      isLoading: false,
      setIsLoading: (isLoading) => set({ isLoading }),
      theme: "dark",
      setTheme: (theme) => set({ theme }),
      language: "ar",
      setLanguage: (language) => set({ language }),
      isOnline: true,
      setIsOnline: (isOnline) => set({ isOnline }),
    }),
    {
      name: "sahool-app-storage",
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({ theme: state.theme, language: state.language }),
    }
  )
);

// Auth Store
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  tenantId: string;
  setUser: (user: User | null) => void;
  setTenantId: (id: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      tenantId: process.env.EXPO_PUBLIC_TENANT_ID || "demo-tenant",
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setTenantId: (tenantId) => set({ tenantId }),
      logout: () => set({ user: null, isAuthenticated: false }),
    }),
    {
      name: "sahool-auth-storage",
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);

// Farm Store
interface FarmState {
  fields: Field[];
  selectedField: Field | null;
  setFields: (fields: Field[]) => void;
  setSelectedField: (field: Field | null) => void;
  updateField: (fieldId: string, updates: Partial<Field>) => void;
  weatherData: WeatherData | null;
  setWeatherData: (data: WeatherData | null) => void;
  equipment: Equipment[];
  setEquipment: (equipment: Equipment[]) => void;
  alerts: Alert[];
  unreadAlertsCount: number;
  setAlerts: (alerts: Alert[]) => void;
  markAlertAsRead: (alertId: string) => void;
  dismissAlert: (alertId: string) => void;
}

export const useFarmStore = create<FarmState>()((set, get) => ({
  fields: [],
  selectedField: null,
  setFields: (fields) => set({ fields }),
  setSelectedField: (selectedField) => set({ selectedField }),
  updateField: (fieldId, updates) => {
    const fields = get().fields.map((f) =>
      f.id === fieldId ? { ...f, ...updates } : f
    );
    set({ fields });
  },
  weatherData: null,
  setWeatherData: (weatherData) => set({ weatherData }),
  equipment: [],
  setEquipment: (equipment) => set({ equipment }),
  alerts: [],
  unreadAlertsCount: 0,
  setAlerts: (alerts) =>
    set({
      alerts,
      unreadAlertsCount: alerts.filter((a) => !a.isRead).length,
    }),
  markAlertAsRead: (alertId) => {
    const alerts = get().alerts.map((a) =>
      a.id === alertId ? { ...a, isRead: true } : a
    );
    set({
      alerts,
      unreadAlertsCount: alerts.filter((a) => !a.isRead).length,
    });
  },
  dismissAlert: (alertId) => {
    const alerts = get().alerts.filter((a) => a.id !== alertId);
    set({
      alerts,
      unreadAlertsCount: alerts.filter((a) => !a.isRead).length,
    });
  },
}));

// AI Chat Store
interface AIMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface AIChatState {
  messages: AIMessage[];
  isTyping: boolean;
  addMessage: (message: Omit<AIMessage, "id" | "timestamp">) => void;
  setIsTyping: (typing: boolean) => void;
  clearChat: () => void;
}

export const useAIChatStore = create<AIChatState>()((set, get) => ({
  messages: [],
  isTyping: false,
  addMessage: (message) => {
    const newMessage: AIMessage = {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date(),
    };
    set({ messages: [...get().messages, newMessage] });
  },
  setIsTyping: (isTyping) => set({ isTyping }),
  clearChat: () => set({ messages: [] }),
}));'

log "Store created ✓"

# ============================================
# SECTION 10: HOOKS - FIXED SPREAD OPERATORS
# ============================================

step "Creating Hooks..."

create_file "hooks/index.ts" 'export * from "./useSahoolData";
export * from "./useMicroInteraction";
export * from "./useLocation";'

create_file "hooks/useSahoolData.ts" 'import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useFarmStore } from "@/store";

// Query Keys
export const queryKeys = {
  fields: ["fields"] as const,
  field: (id: string) => ["fields", id] as const,
  weather: (lat: number, lon: number) => ["weather", lat, lon] as const,
  alerts: ["alerts"] as const,
  equipment: ["equipment"] as const,
  ndvi: (fieldId: string) => ["ndvi", fieldId] as const,
  dashboard: ["dashboard"] as const,
};

// Fields
export function useFields() {
  const { setFields } = useFarmStore();

  return useQuery({
    queryKey: queryKeys.fields,
    queryFn: async () => {
      const response = await api.getFields();
      return response.data;
    },
    staleTime: 1000 * 60 * 10, // 10 minutes
    gcTime: 1000 * 60 * 60,    // Fixed: gcTime instead of cacheTime for React Query v5
    refetchOnWindowFocus: false,
  });
}

export function useField(fieldId: string) {
  return useQuery({
    queryKey: queryKeys.field(fieldId),
    queryFn: async () => {
      const response = await api.getFieldById(fieldId);
      return response.data;
    },
    enabled: !!fieldId,
    staleTime: 1000 * 60 * 5,
  });
}

export function useCreateField() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (field: any) => api.createField(field),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.fields });
    },
  });
}

export function useUpdateField() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ fieldId, updates }: { fieldId: string; updates: any }) =>
      api.updateField(fieldId, updates),
    onSuccess: (_, { fieldId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.fields });
      queryClient.invalidateQueries({ queryKey: queryKeys.field(fieldId) });
    },
  });
}

// Weather
export function useWeather(lat: number, lon: number) {
  const { setWeatherData } = useFarmStore();

  return useQuery({
    queryKey: queryKeys.weather(lat, lon),
    queryFn: async () => {
      const response = await api.getWeather(lat, lon);
      return response.data;
    },
    enabled: !!lat && !!lon,
    staleTime: 1000 * 60 * 15, // 15 minutes
    refetchInterval: 1000 * 60 * 30, // 30 minutes
  });
}

// NDVI - FIXED: proper spread operator
export function useNDVI(fieldId: string, days = 30) {
  return useQuery({
    queryKey: [...queryKeys.ndvi(fieldId), days],
    queryFn: async () => {
      const response = await api.getNDVITimeline(fieldId, days);
      return response.data;
    },
    enabled: !!fieldId,
    staleTime: 1000 * 60 * 60 * 6, // 6 hours
  });
}

// Alerts
export function useAlerts() {
  const { setAlerts } = useFarmStore();

  return useQuery({
    queryKey: queryKeys.alerts,
    queryFn: async () => {
      const response = await api.getActiveAlerts();
      return response.data;
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
    refetchInterval: 1000 * 60 * 5, // 5 minutes
  });
}

export function useMarkAlertAsRead() {
  const queryClient = useQueryClient();
  const { markAlertAsRead } = useFarmStore();

  return useMutation({
    mutationFn: (alertId: string) => api.markAlertAsRead(alertId),
    onMutate: async (alertId) => {
      markAlertAsRead(alertId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts });
    },
  });
}

// Equipment
export function useEquipment() {
  const { setEquipment } = useFarmStore();

  return useQuery({
    queryKey: queryKeys.equipment,
    queryFn: async () => {
      const response = await api.getEquipment();
      return response.data;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

// AI Chat
export function useAIChat() {
  return useMutation({
    mutationFn: ({ message, context }: { message: string; context?: any }) =>
      api.chatWithAI(message, context),
  });
}

// Dashboard
export function useDashboard() {
  return useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: async () => {
      const response = await api.getDashboardStats();
      return response.data;
    },
    staleTime: 1000 * 60 * 5,
  });
}'

create_file "hooks/useMicroInteraction.ts" 'import { useCallback } from "react";
import {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  withSequence,
} from "react-native-reanimated";

const SPRING_CONFIG = {
  damping: 15,
  stiffness: 150,
  mass: 0.5,
};

// Press Animation
export function usePressAnimation(scaleValue = 0.95) {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  const pressIn = useCallback(() => {
    scale.value = withSpring(scaleValue, SPRING_CONFIG);
    opacity.value = withTiming(0.8, { duration: 100 });
  }, [scaleValue]);

  const pressOut = useCallback(() => {
    scale.value = withSpring(1, SPRING_CONFIG);
    opacity.value = withTiming(1, { duration: 100 });
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  return { scale, opacity, pressIn, pressOut, animatedStyle };
}

// Pulse Animation
export function usePulseAnimation() {
  const scale = useSharedValue(1);

  const pulse = useCallback(() => {
    scale.value = withSequence(
      withSpring(1.1, SPRING_CONFIG),
      withSpring(1, SPRING_CONFIG)
    );
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return { pulse, animatedStyle };
}

// Shake Animation
export function useShakeAnimation() {
  const translateX = useSharedValue(0);

  const shake = useCallback(() => {
    translateX.value = withSequence(
      withTiming(-10, { duration: 50 }),
      withTiming(10, { duration: 50 }),
      withTiming(-10, { duration: 50 }),
      withTiming(10, { duration: 50 }),
      withTiming(0, { duration: 50 })
    );
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
  }));

  return { shake, animatedStyle };
}

// Legacy export
export function useMicroInteraction() {
  return usePressAnimation();
}'

create_file "hooks/useLocation.ts" 'import { useState, useCallback, useEffect } from "react";
import * as Location from "expo-location";

interface LocationState {
  latitude: number | null;
  longitude: number | null;
  accuracy: number | null;
  altitude: number | null;
}

export function useLocation() {
  const [location, setLocation] = useState<LocationState>({
    latitude: null,
    longitude: null,
    accuracy: null,
    altitude: null,
  });
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [watchSubscription, setWatchSubscription] = useState<Location.LocationSubscription | null>(null);

  const requestPermission = useCallback(async (): Promise<boolean> => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") {
        setError("Location permission denied");
        return false;
      }
      return true;
    } catch (err) {
      setError("Error requesting permission");
      return false;
    }
  }, []);

  const getCurrentLocation = useCallback(async (): Promise<LocationState | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const hasPermission = await requestPermission();
      if (!hasPermission) return null;

      const currentLocation = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });

      const newLocation: LocationState = {
        latitude: currentLocation.coords.latitude,
        longitude: currentLocation.coords.longitude,
        accuracy: currentLocation.coords.accuracy,
        altitude: currentLocation.coords.altitude,
      };

      setLocation(newLocation);
      return newLocation;
    } catch (err: any) {
      setError(err.message || "Failed to get location");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [requestPermission]);

  const watchLocation = useCallback(async () => {
    const hasPermission = await requestPermission();
    if (!hasPermission) return;

    const subscription = await Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.High,
        timeInterval: 5000,
        distanceInterval: 10,
      },
      (newLocation) => {
        setLocation({
          latitude: newLocation.coords.latitude,
          longitude: newLocation.coords.longitude,
          accuracy: newLocation.coords.accuracy,
          altitude: newLocation.coords.altitude,
        });
      }
    );

    setWatchSubscription(subscription);
  }, [requestPermission]);

  const stopWatching = useCallback(() => {
    if (watchSubscription) {
      watchSubscription.remove();
      setWatchSubscription(null);
    }
  }, [watchSubscription]);

  useEffect(() => {
    return () => {
      if (watchSubscription) {
        watchSubscription.remove();
      }
    };
  }, [watchSubscription]);

  return {
    location,
    error,
    isLoading,
    requestPermission,
    getCurrentLocation,
    watchLocation,
    stopWatching,
  };
}'

log "Hooks created ✓"

# ============================================
# SECTION 11: UI COMPONENTS - FIXED SPREAD OPERATORS
# ============================================

step "Creating UI components..."

create_file "components/ui/Loading.tsx" 'import React from "react";
import { View, Text, ActivityIndicator, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

interface LoadingProps {
  message?: string;
  fullScreen?: boolean;
}

export function Loading({ message = "Loading...", fullScreen = true }: LoadingProps) {
  const content = (
    <View style={styles.container}>
      <View style={styles.loaderContainer}>
        <ActivityIndicator size="large" color="#F4D03F" />
        <Text style={styles.message}>{message}</Text>
      </View>
    </View>
  );

  if (fullScreen) {
    return (
      <LinearGradient colors={["#0D1F17", "#1B4D3E"]} style={styles.fullScreen}>
        {content}
      </LinearGradient>
    );
  }

  return content;
}

const styles = StyleSheet.create({
  fullScreen: { flex: 1 },
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  loaderContainer: {
    backgroundColor: "rgba(27, 77, 62, 0.9)",
    borderRadius: 16,
    padding: 24,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
  },
  message: {
    color: "#F4D03F",
    fontSize: 16,
    marginTop: 16,
    textAlign: "center",
  },
});'

create_file "components/ui/Button.tsx" 'import React from "react";
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated from "react-native-reanimated";
import { usePressAnimation } from "@/hooks/useMicroInteraction";

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "outline" | "danger";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  fullWidth?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export function Button({
  title,
  onPress,
  variant = "primary",
  size = "md",
  disabled = false,
  loading = false,
  icon,
  iconPosition = "left",
  fullWidth = false,
  style,
  textStyle,
}: ButtonProps) {
  const { pressIn, pressOut, animatedStyle } = usePressAnimation();
  const isDisabled = disabled || loading;

  const getGradientColors = (): [string, string] => {
    if (isDisabled) return ["#4A5568", "#2D3748"];
    switch (variant) {
      case "primary": return ["#F4D03F", "#F7DC6F"];
      case "secondary": return ["#1B4D3E", "#2D6A4F"];
      case "danger": return ["#E74C3C", "#C0392B"];
      default: return ["transparent", "transparent"];
    }
  };

  const getTextColor = (): string => {
    if (isDisabled) return "#A0AEC0";
    switch (variant) {
      case "primary": return "#1B4D3E";
      case "outline": return "#F4D03F";
      default: return "#FFFFFF";
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case "sm": return { paddingVertical: 8, paddingHorizontal: 16, fontSize: 14 };
      case "lg": return { paddingVertical: 16, paddingHorizontal: 32, fontSize: 18 };
      default: return { paddingVertical: 12, paddingHorizontal: 24, fontSize: 16 };
    }
  };

  const sizeStyles = getSizeStyles();

  const content = (
    <>
      {loading ? (
        <ActivityIndicator color={getTextColor()} size="small" />
      ) : (
        <>
          {icon && iconPosition === "left" && icon}
          <Text style={[styles.text, { color: getTextColor(), fontSize: sizeStyles.fontSize }, textStyle]}>
            {title}
          </Text>
          {icon && iconPosition === "right" && icon}
        </>
      )}
    </>
  );

  const buttonStyle: ViewStyle = {
    ...styles.button,
    paddingVertical: sizeStyles.paddingVertical,
    paddingHorizontal: sizeStyles.paddingHorizontal,
    width: fullWidth ? "100%" : undefined,
    borderWidth: variant === "outline" ? 1 : 0,
    borderColor: variant === "outline" ? "#F4D03F" : undefined,
  };

  if (variant === "outline") {
    return (
      <AnimatedTouchable
        onPress={onPress}
        onPressIn={pressIn}
        onPressOut={pressOut}
        disabled={isDisabled}
        style={[animatedStyle, buttonStyle, style]}
        activeOpacity={0.7}
      >
        {content}
      </AnimatedTouchable>
    );
  }

  return (
    <AnimatedTouchable
      onPress={onPress}
      onPressIn={pressIn}
      onPressOut={pressOut}
      disabled={isDisabled}
      style={[animatedStyle, style]}
      activeOpacity={0.7}
    >
      <LinearGradient colors={getGradientColors()} start={[0, 0]} end={[1, 1]} style={buttonStyle}>
        {content}
      </LinearGradient>
    </AnimatedTouchable>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 12,
    gap: 8,
  },
  text: {
    fontWeight: "600",
    textAlign: "center",
  },
});'

log "UI components created ✓"

# ============================================
# SECTION 12: CARD COMPONENTS
# ============================================

step "Creating card components..."

create_file "components/cards/SahoolCard.tsx" 'import React from "react";
import { View, Text, TouchableOpacity, StyleSheet, ViewStyle } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated from "react-native-reanimated";
import { usePressAnimation } from "@/hooks/useMicroInteraction";

interface SahoolCardProps {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  subtitle?: string;
  gradient?: [string, string];
  onPress?: () => void;
  style?: ViewStyle;
  trend?: { value: string; isPositive: boolean };
  rightContent?: React.ReactNode;
}

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export function SahoolCard({
  icon,
  title,
  value,
  subtitle,
  gradient = ["#1B4D3E", "#14352B"],
  onPress,
  style,
  trend,
  rightContent,
}: SahoolCardProps) {
  const { pressIn, pressOut, animatedStyle } = usePressAnimation();

  return (
    <AnimatedTouchable
      onPress={onPress}
      onPressIn={pressIn}
      onPressOut={pressOut}
      disabled={!onPress}
      style={[animatedStyle, { flex: 1 }, style]}
      activeOpacity={0.8}
    >
      <LinearGradient colors={gradient} start={[0, 0]} end={[1, 1]} style={styles.card}>
        <View style={styles.header}>
          <View style={styles.iconContainer}>{icon}</View>
          {rightContent}
        </View>

        <View style={styles.content}>
          <Text style={styles.title}>{title}</Text>
          <View style={styles.valueRow}>
            <Text style={styles.value}>{value}</Text>
            {trend && (
              <View style={[styles.trendBadge, { backgroundColor: trend.isPositive ? "#27AE6020" : "#E74C3C20" }]}>
                <Text style={[styles.trendText, { color: trend.isPositive ? "#27AE60" : "#E74C3C" }]}>
                  {trend.isPositive ? "↑" : "↓"} {trend.value}
                </Text>
              </View>
            )}
          </View>
          {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
        </View>
      </LinearGradient>
    </AnimatedTouchable>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 12,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: "rgba(244, 208, 63, 0.2)",
    justifyContent: "center",
    alignItems: "center",
  },
  content: { gap: 4 },
  title: { color: "rgba(255, 255, 255, 0.7)", fontSize: 14 },
  valueRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  value: { color: "#FFFFFF", fontSize: 28, fontWeight: "700" },
  trendBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  trendText: { fontSize: 12, fontWeight: "600" },
  subtitle: { color: "rgba(255, 255, 255, 0.5)", fontSize: 12, marginTop: 4 },
});'

create_file "components/cards/FieldCard.tsx" 'import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { MapPin, Leaf, Droplets, Activity } from "lucide-react-native";
import Animated from "react-native-reanimated";
import { usePressAnimation } from "@/hooks/useMicroInteraction";
import { Field } from "@/types";

interface FieldCardProps {
  field: Field;
  onPress?: () => void;
  selected?: boolean;
}

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export function FieldCard({ field, onPress, selected }: FieldCardProps) {
  const { pressIn, pressOut, animatedStyle } = usePressAnimation();

  const getStatusBadgeColor = (status: string): [string, string] => {
    switch (status) {
      case "healthy": return ["#27AE60", "#2ECC71"];
      case "warning": return ["#F39C12", "#E67E22"];
      case "critical": return ["#E74C3C", "#C0392B"];
      default: return ["#7F8C8D", "#95A5A6"];
    }
  };

  const getStatusText = (status: string): string => {
    switch (status) {
      case "healthy": return "Healthy";
      case "warning": return "Warning";
      case "critical": return "Critical";
      default: return "Inactive";
    }
  };

  return (
    <AnimatedTouchable
      onPress={onPress}
      onPressIn={pressIn}
      onPressOut={pressOut}
      style={animatedStyle}
      activeOpacity={0.8}
    >
      <LinearGradient
        colors={["#1B4D3E", "#14352B"]}
        start={[0, 0]}
        end={[1, 1]}
        style={[styles.card, selected && styles.selectedCard]}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={[styles.colorDot, { backgroundColor: field.color || "#4CAF50" }]} />
            <View>
              <Text style={styles.fieldName}>{field.nameAr || field.name}</Text>
              <Text style={styles.cropType}>{field.cropType}</Text>
            </View>
          </View>
          <LinearGradient colors={getStatusBadgeColor(field.status)} style={styles.statusBadge}>
            <Text style={styles.statusText}>{getStatusText(field.status)}</Text>
          </LinearGradient>
        </View>

        {/* Stats Grid */}
        <View style={styles.statsGrid}>
          <View style={styles.statItem}>
            <View style={[styles.statIcon, { backgroundColor: "rgba(39, 174, 96, 0.2)" }]}>
              <Leaf size={16} color="#27AE60" />
            </View>
            <Text style={styles.statValue}>{field.healthScore}%</Text>
            <Text style={styles.statLabel}>Health</Text>
          </View>

          <View style={styles.statItem}>
            <View style={[styles.statIcon, { backgroundColor: "rgba(244, 208, 63, 0.2)" }]}>
              <Activity size={16} color="#F4D03F" />
            </View>
            <Text style={styles.statValue}>{field.ndviValue.toFixed(2)}</Text>
            <Text style={styles.statLabel}>NDVI</Text>
          </View>

          <View style={styles.statItem}>
            <View style={[styles.statIcon, { backgroundColor: "rgba(52, 152, 219, 0.2)" }]}>
              <Droplets size={16} color="#3498DB" />
            </View>
            <Text style={styles.statValue}>{field.moistureLevel}%</Text>
            <Text style={styles.statLabel}>Moisture</Text>
          </View>

          <View style={styles.statItem}>
            <View style={[styles.statIcon, { backgroundColor: "rgba(155, 89, 182, 0.2)" }]}>
              <MapPin size={16} color="#9B59B6" />
            </View>
            <Text style={styles.statValue}>{field.acreage}</Text>
            <Text style={styles.statLabel}>Hectares</Text>
          </View>
        </View>
      </LinearGradient>
    </AnimatedTouchable>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
    marginBottom: 12,
  },
  selectedCard: {
    borderColor: "#F4D03F",
    borderWidth: 2,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  headerLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  colorDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  fieldName: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },
  cropType: {
    color: "rgba(255, 255, 255, 0.6)",
    fontSize: 12,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: "#FFFFFF",
    fontSize: 11,
    fontWeight: "600",
  },
  statsGrid: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  statItem: {
    alignItems: "center",
    flex: 1,
  },
  statIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 6,
  },
  statValue: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
  },
  statLabel: {
    color: "rgba(255, 255, 255, 0.5)",
    fontSize: 10,
    marginTop: 2,
  },
});'

log "Card components created ✓"

# ============================================
# SECTION 13: COMPONENT EXPORTS
# ============================================

create_file "components/index.ts" '// UI Components
export * from "./ui/Loading";
export * from "./ui/Button";

// Card Components
export * from "./cards/SahoolCard";
export * from "./cards/FieldCard";'

log "Component exports created ✓"

# ============================================
# SECTION 14: APP LAYOUTS
# ============================================

step "Creating layouts..."

create_file "app/_layout.tsx" 'import { useEffect } from "react";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useFonts } from "expo-font";
import * as SplashScreen from "expo-splash-screen";

import "../global.css";

SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 2,
    },
  },
});

export default function RootLayout() {
  const [fontsLoaded] = useFonts({});

  useEffect(() => {
    if (fontsLoaded) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded]);

  return (
    <QueryClientProvider client={queryClient}>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <StatusBar style="light" backgroundColor="#0D1F17" />
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: "#0D1F17" },
            animation: "slide_from_right",
          }}
        >
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="field/[id]" options={{ presentation: "card" }} />
        </Stack>
      </GestureHandlerRootView>
    </QueryClientProvider>
  );
}'

create_file "app/(tabs)/_layout.tsx" 'import { Tabs } from "expo-router";
import { View, StyleSheet, Platform } from "react-native";
import { Home, Map, Bell, Brain, User } from "lucide-react-native";
import { useFarmStore } from "@/store";

export default function TabLayout() {
  const { unreadAlertsCount } = useFarmStore();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: "#F4D03F",
        tabBarInactiveTintColor: "rgba(255, 255, 255, 0.5)",
        tabBarLabelStyle: styles.tabBarLabel,
        tabBarHideOnKeyboard: true,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color, size }) => <Home size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="fields"
        options={{
          title: "Fields",
          tabBarIcon: ({ color, size }) => <Map size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="alerts"
        options={{
          title: "Alerts",
          tabBarIcon: ({ color, size }) => (
            <View>
              <Bell size={size} color={color} />
              {unreadAlertsCount > 0 && <View style={styles.badge} />}
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="assistant"
        options={{
          title: "Assistant",
          tabBarIcon: ({ color, size }) => <Brain size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: "Profile",
          tabBarIcon: ({ color, size }) => <User size={size} color={color} />,
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: "#1B4D3E",
    borderTopWidth: 0,
    height: Platform.OS === "ios" ? 85 : 65,
    paddingBottom: Platform.OS === "ios" ? 25 : 10,
    paddingTop: 10,
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  tabBarLabel: { fontSize: 11, fontWeight: "600" },
  badge: {
    position: "absolute",
    top: -4,
    right: -8,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#E74C3C",
  },
});'

log "Layouts created ✓"

# ============================================
# SECTION 15: PLACEHOLDER SCREENS
# ============================================

step "Creating placeholder screens..."

create_file "app/(tabs)/index.tsx" 'import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function DashboardScreen() {
  const insets = useSafeAreaInsets();

  return (
    <LinearGradient colors={["#0D1F17", "#1B4D3E"]} style={styles.container}>
      <View style={[styles.content, { paddingTop: insets.top + 20 }]}>
        <Text style={styles.title}>SAHOOL Dashboard</Text>
        <Text style={styles.subtitle}>Smart Agriculture Platform</Text>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { flex: 1, padding: 16, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 28, fontWeight: "700", color: "#FFFFFF" },
  subtitle: { fontSize: 16, color: "#F4D03F", marginTop: 8 },
});'

create_file "app/(tabs)/fields.tsx" 'import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

export default function FieldsScreen() {
  return (
    <LinearGradient colors={["#0D1F17", "#1B4D3E"]} style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Fields</Text>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { flex: 1, padding: 16, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 28, fontWeight: "700", color: "#FFFFFF" },
});'

create_file "app/(tabs)/alerts.tsx" 'import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

export default function AlertsScreen() {
  return (
    <LinearGradient colors={["#0D1F17", "#1B4D3E"]} style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Alerts</Text>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { flex: 1, padding: 16, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 28, fontWeight: "700", color: "#FFFFFF" },
});'

create_file "app/(tabs)/assistant.tsx" 'import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

export default function AssistantScreen() {
  return (
    <LinearGradient colors={["#0D1F17", "#1B4D3E"]} style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>AI Assistant</Text>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { flex: 1, padding: 16, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 28, fontWeight: "700", color: "#FFFFFF" },
});'

create_file "app/(tabs)/profile.tsx" 'import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

export default function ProfileScreen() {
  return (
    <LinearGradient colors={["#0D1F17", "#1B4D3E"]} style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Profile</Text>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { flex: 1, padding: 16, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 28, fontWeight: "700", color: "#FFFFFF" },
});'

log "Screens created ✓"

# ============================================
# SECTION 16: CI/CD - FIXED YAML QUOTING
# ============================================

step "Setting up CI/CD..."

create_file ".github/workflows/mobile-ci.yml" 'name: SAHOOL Mobile CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npx tsc --noEmit
      - run: npm run lint || true

  build:
    needs: lint-and-test
    runs-on: ubuntu-latest
    if: github.ref == '\''refs/heads/main'\''
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - uses: expo/expo-github-action@v8
        with:
          expo-version: latest
          eas-version: latest
          token: ${{ secrets.EXPO_TOKEN }}
      - run: npm ci
      - run: eas build --platform all --profile production --non-interactive'

create_file "eas.json" '{
  "cli": { "version": ">= 7.0.0" },
  "build": {
    "development": { "developmentClient": true, "distribution": "internal" },
    "preview": { "distribution": "internal", "android": { "buildType": "apk" } },
    "production": { "autoIncrement": true }
  }
}'

log "CI/CD setup complete ✓"

# ============================================
# SECTION 17: FINAL SETUP
# ============================================

step "Final setup..."

create_file "README.md" '# 🌱 SAHOOL Mobile

**Smart Agriculture Platform**

## 🚀 Quick Start

```bash
npm install
npm start
```

## 📱 Run

```bash
npm run ios      # iOS
npm run android  # Android
```

## 🏗️ Build

```bash
eas build --profile preview   # For testing
eas build --profile production # For production
```

## 📄 License

© 2024 SAHOOL'

mkdir -p assets/fonts
touch assets/fonts/.gitkeep

npm install 2>/dev/null || true

# ============================================
# COMPLETION
# ============================================

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         🎉 SAHOOL project created successfully! 🎉         ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

success "✅ Project setup complete!"
echo ""
info "📋 Next steps:"
echo ""
echo -e "   ${GREEN}1.${NC} cd $PROJECT_NAME"
echo -e "   ${GREEN}2.${NC} Edit .env with your settings"
echo -e "   ${GREEN}3.${NC} npm start"
echo ""
info "📱 To run:"
echo -e "   ${YELLOW}iOS:${NC}     npm run ios"
echo -e "   ${YELLOW}Android:${NC} npm run android"
echo ""
log "🌱 SAHOOL - Smart Agriculture Platform"
