#!/bin/bash
# ============================================
# SAHOOL Mobile Complete Setup Script v4.2.1
# One script to rule them all - Production Ready
# Fixed and Enhanced Version
# ============================================

set -e  # Exit on any error

# ==================== CONFIGURATION ====================
VERSION="4.2.1"
SCRIPT_NAME="sahool-mobile-setup"
PROJECT_NAME_DEFAULT="sahool-mobile"
MIN_NODE_VERSION="18"
MIN_NPM_VERSION="9"

# ==================== COLORS & STYLING ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

BOLD='\033[1m'
UNDERLINE='\033[4m'

# ==================== LOGGING FUNCTIONS ====================
log() {
    echo -e "${GREEN}[${SCRIPT_NAME}]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

debug() {
    if [ "$DEBUG" = "true" ]; then
        echo -e "${MAGENTA}[DEBUG]${NC} $1"
    fi
}

print_header() {
    echo -e ""
    echo -e "${CYAN}${BOLD}========================================${NC}"
    echo -e "${CYAN}${BOLD}  SAHOOL MOBILE v${VERSION} Setup${NC}"
    echo -e "${CYAN}${BOLD}  AI-Powered Agricultural Platform${NC}"
    echo -e "${CYAN}${BOLD}========================================${NC}"
    echo -e ""
}

print_step() {
    echo -e ""
    log "${BOLD}${UNDERLINE}Step $1: $2${NC}"
}

# ==================== FILE CREATION UTILITY ====================
create_file() {
    local file_path="$1"
    local content="$2"
    local description="$3"

    # Create directory if it doesn't exist
    mkdir -p "$(dirname "$file_path")"

    # Write content to file
    if printf '%s' "$content" > "$file_path"; then
        success "Created: $description ($file_path)"
    else
        error "Failed to create: $file_path"
    fi
}

check_file_exists() {
    if [ -f "$1" ]; then
        warn "File exists: $1. Skipping..."
        return 0
    fi
    return 1
}

# ==================== REQUIREMENTS CHECK ====================
check_requirements() {
    print_step "0" "Checking System Requirements"

    # Check Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed. Please install Node.js ${MIN_NODE_VERSION}+ first."
    fi

    NODE_VERSION=$(node --version | cut -d'v' -f2)
    NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d'.' -f1)

    if [ "$NODE_MAJOR" -lt "$MIN_NODE_VERSION" ]; then
        error "Node.js ${MIN_NODE_VERSION}+ required. Current: $NODE_VERSION"
    fi
    info "Node.js ${NODE_VERSION} OK"

    # Check npm
    if ! command -v npm &> /dev/null; then
        error "npm is not installed."
    fi

    NPM_VERSION=$(npm --version)
    info "npm ${NPM_VERSION} OK"

    # Check git (optional)
    if ! command -v git &> /dev/null; then
        warn "git is not installed. Repository initialization will be skipped."
        HAS_GIT=false
    else
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        info "git ${GIT_VERSION} OK"
        HAS_GIT=true
    fi

    # Check Python (for node-gyp)
    if ! command -v python3 &> /dev/null; then
        warn "Python3 is not installed. Some packages may fail to build."
    else
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        info "python3 ${PYTHON_VERSION} OK"
    fi

    success "All requirements satisfied!"
}

# ==================== USER INPUT ====================
get_user_input() {
    print_step "1" "Project Configuration"

    # Interactive or non-interactive mode
    if [ "$NON_INTERACTIVE" = "true" ]; then
        info "Running in non-interactive mode using defaults or environment variables."
    else
        # Project name
        read -p "$(echo -e "${GREEN}Project name [${PROJECT_NAME_DEFAULT}]:${NC} ")" PROJECT_NAME
        PROJECT_NAME="${PROJECT_NAME:-$PROJECT_NAME_DEFAULT}"

        # Tenant ID
        read -p "$(echo -e "${GREEN}Default tenant ID [demo-tenant]:${NC} ")" TENANT_ID
        TENANT_ID="${TENANT_ID:-demo-tenant}"

        # API URL
        read -p "$(echo -e "${GREEN}API Gateway URL [http://localhost:9000/api]:${NC} ")" API_URL
        API_URL="${API_URL:-http://localhost:9000/api}"

        # Initialize git
        read -p "$(echo -e "${GREEN}Initialize git repository? (y/n) [y]:${NC} ")" INIT_GIT
        INIT_GIT="${INIT_GIT:-y}"

        # Install dependencies
        read -p "$(echo -e "${GREEN}Install dependencies now? (y/n) [y]:${NC} ")" INSTALL_DEPS
        INSTALL_DEPS="${INSTALL_DEPS:-y}"
    fi

    # Set variables
    export PROJECT_NAME="${PROJECT_NAME:-$PROJECT_NAME_DEFAULT}"
    export TENANT_ID="${TENANT_ID:-demo-tenant}"
    export API_URL="${API_URL:-http://localhost:9000/api}"
    export INIT_GIT="${INIT_GIT:-y}"
    export INSTALL_DEPS="${INSTALL_DEPS:-y}"

    # Create .env file
    cat > .setup.env << EOF
PROJECT_NAME=$PROJECT_NAME
TENANT_ID=$TENANT_ID
API_URL=$API_URL
INIT_GIT=$INIT_GIT
INSTALL_DEPS=$INSTALL_DEPS
EOF

    info "Configuration saved to .setup.env"
}

# ==================== PART 1: PROJECT INIT ====================
part1_project_init() {
    print_step "1" "Creating Expo Project"

    if [ -d "$PROJECT_NAME" ]; then
        warn "Directory $PROJECT_NAME exists. Entering existing project."
        cd "$PROJECT_NAME"
    else
        log "Creating new Expo project: $PROJECT_NAME"
        npx create-expo-app "$PROJECT_NAME" -t tabs@50

        if [ $? -ne 0 ]; then
            error "Failed to create Expo project"
        fi

        cd "$PROJECT_NAME"
        success "Project created successfully"
    fi

    # Initialize git if requested
    if [ "$INIT_GIT" = "y" ] && [ "$HAS_GIT" = true ]; then
        if [ ! -d ".git" ]; then
            log "Initializing git repository..."
            git init
            git branch -M main
            success "Git repository initialized"
        else
            warn "Git repository already exists"
        fi
    fi

    # Create directory structure - FIXED: Proper mkdir syntax
    log "Creating directory structure..."
    mkdir -p app/tabs
    mkdir -p app/field
    mkdir -p hooks
    mkdir -p store
    mkdir -p types
    mkdir -p lib/api
    mkdir -p lib/utils
    mkdir -p components/ui
    mkdir -p components/cards
    mkdir -p components/modals
    mkdir -p assets/images
    mkdir -p assets/icons
    mkdir -p assets/fonts
    mkdir -p assets/animations
    mkdir -p scripts
    mkdir -p .github/workflows

    success "Directory structure created"
}

# ==================== PART 2: CONFIGURATION ====================
part2_configuration() {
    print_step "2" "Configuring TypeScript & Tailwind"

    # Install dependencies
    if [ "$INSTALL_DEPS" = "y" ]; then
        log "Installing dependencies..."

        # Core dependencies
        npm install nativewind@^4.0.1
        npm install -D tailwindcss@^3.4.3

        # State management & API
        npm install @tanstack/react-query@^5.25.0 zustand@^4.5.2 axios@^1.6.8

        # Async storage & security
        npm install @react-native-async-storage/async-storage@^1.21.0
        npm install expo-secure-store@~13.0.1

        # UI & animations
        npm install react-native-maps@1.10.0 expo-linear-gradient@~12.7.2
        npm install react-native-reanimated@~3.6.2 react-native-gesture-handler@~2.14.0
        npm install lucide-react-native@^0.363.0 react-native-svg@^15.0.0

        # Native features
        npm install expo-location@~17.0.1 expo-notifications@~0.28.0
        npm install expo-image-picker@~15.0.4

        # Performance
        npm install @shopify/flash-list@^1.6.3

        # Dev dependencies
        npm install --save-dev typescript @types/react @types/react-native

        if [ $? -ne 0 ]; then
            error "Failed to install dependencies"
        fi
        success "Dependencies installed"
    fi

    # Tailwind configuration
    cat > tailwind.config.js << 'TAILWINDEOF'
/**
 * @type {import("tailwindcss").Config}
 */
module.exports = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./screens/**/*.{ts,tsx}",
  ],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        sahool: {
          bg: '#0D1F17',
          primary: '#1B4D3E',
          light: '#2D6A4F',
          dark: '#14352B',
          accent: '#F4D03F',
          accentLight: '#F7DC6F',
          cream: '#F5F5DC',
          white: '#FFFFFF',
          success: '#27AE60',
          warning: '#E67E22',
          danger: '#E74C3C',
          info: '#3498DB',
        }
      },
      fontFamily: {
        'tajawal': ['Tajawal', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 4px 20px rgba(27, 77, 62, 0.15)',
        medium: '0 8px 30px rgba(27, 77, 62, 0.25)',
        hard: '0 12px 40px rgba(27, 77, 62, 0.35)',
        glow: '0 0 20px rgba(244, 208, 63, 0.5)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
        'full': '9999px',
      }
    },
  },
  plugins: [],
};
TAILWINDEOF
    success "Created: Tailwind config"

    # Global CSS
    cat > global.css << 'GLOBALCSSEOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
GLOBALCSSEOF
    success "Created: Global CSS"

    # Babel config
    cat > babel.config.js << 'BABELEOF'
module.exports = function(api) {
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
};
BABELEOF
    success "Created: Babel config"

    # TypeScript config
    cat > tsconfig.json << 'TSCONFIGEOF'
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitAny": true,
    "noImplicitReturns": true,
    "noImplicitThis": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "noUncheckedIndexedAccess": true,
    "paths": {
      "@/*": ["./*"]
    },
    "types": ["nativewind/types"]
  },
  "include": ["**/*.ts", "**/*.tsx", "global.css"]
}
TSCONFIGEOF
    success "Created: TypeScript config"

    # NativeWind types
    echo '/// <reference types="nativewind/types" />' > nativewind-env.d.ts
    success "Created: NativeWind types"

    # Metro config
    cat > metro.config.js << 'METROEOF'
const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

const config = getDefaultConfig(__dirname);

module.exports = withNativeWind(config, {
  input: "./global.css",
  inlineRem: 16,
});
METROEOF
    success "Created: Metro config"

    # Environment variables
    cat > .env << ENVEOF
EXPO_PUBLIC_API_URL=$API_URL
EXPO_PUBLIC_TENANT_ID=$TENANT_ID
EXPO_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
EXPO_PUBLIC_MIXPANEL_TOKEN=your_mixpanel_token
EXPO_PUBLIC_SENTRY_DSN=your_sentry_dsn
ENVEOF
    success "Created: Environment variables"

    # .gitignore
    cat > .gitignore << 'GITIGNOREEOF'
# Dependencies
node_modules/
.pnp/
.pnp.js

# Expo
.expo/
dist/
web-build/

# Native
*.orig.*
*.jks
*.p8
*.p12
*.key
*.mobileprovision

# Metro
.metro-health-check*

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage
coverage/
*.lcov

# OS
.DS_Store

# Environment
.env
.env.local
.env.development
.env.test
.env.production
.env*.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# Temporary
*.tmp
*.temp

# Build outputs
android/
ios/
build/
*.apk
*.aab
*.ipa

# EAS
.eas/

# TypeScript
*.tsbuildinfo

# Keep setup env
!.setup.env
GITIGNOREEOF
    success "Created: Git ignore"

    success "Configuration completed"
}

# ==================== PART 3: TYPES & STORE ====================
part3_types_store() {
    print_step "3" "Setting Up Types & State Management"

    # Types
    cat > types/index.ts << 'TYPESEOF'
export interface Field {
  id: string;
  name: string;
  tenantId: string;
  cropType: string;
  acreage: number;
  healthScore: number;
  boundaryPolygon: { latitude: number; longitude: number }[];
  center: { latitude: number; longitude: number };
  equipment?: Equipment[];
  ndviHistory?: NDVIEntry[];
  createdAt: string;
  updatedAt: string;
}

export interface Equipment {
  id: string;
  name: string;
  type: string;
  status: "active" | "idle" | "maintenance";
  fuel: number;
  location: { latitude: number; longitude: number };
  lastUpdate: string;
}

export interface NDVIEntry {
  date: string;
  value: number;
  satellite: string;
  cloudCoverage: number;
}

export interface WeatherData {
  current: {
    temperature: number;
    humidity: number;
    windSpeed: number;
    condition: string;
  };
  forecast: { date: string; temperature: { min: number; max: number }; precipitation: number; condition: string }[];
  alerts: WeatherAlert[];
}

export interface WeatherAlert {
  id: string;
  type: string;
  severity: "low" | "medium" | "high" | "extreme";
  title: string;
  description: string;
  startTime: string;
  endTime: string;
}

export interface Alert {
  id: string;
  type: "pest" | "disease" | "weather" | "equipment";
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  message: string;
  fieldId?: string;
  equipmentId?: string;
  isRead: boolean;
  createdAt: string;
}

export interface AIChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  image?: string;
  timestamp: Date;
  context?: any;
}

export interface User {
  id: string;
  email: string;
  name: string;
  tenantId: string;
  role: "farmer" | "manager" | "admin";
  avatar?: string;
  preferences: {
    language: "ar" | "en";
    units: "metric" | "imperial";
    notifications: boolean;
  };
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  meta?: { total: number; page: number; limit: number };
}

export interface ApiError {
  success: false;
  message: string;
  code: string;
  details?: any;
}

export interface AstralData {
  moonPhase: string;
  moonIllumination: number;
  zodiacSign: string;
  starPosition: string;
  recommendations: AstralRecommendation[];
  date: string;
}

export interface AstralRecommendation {
  activity: string;
  time: string;
  reason: string;
  zodiac: string;
  star: string;
  fieldId?: string;
}
TYPESEOF
    success "Created: Type definitions"

    # Store
    cat > store/appStore.ts << 'STOREEOF'
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Field, User, Equipment, Alert } from "@/types";

export interface AppState {
  tenantId: string;
  setTenantId: (id: string) => void;
  user: User | null;
  setUser: (user: User | null) => void;
  selectedField: Field | null;
  setSelectedField: (field: Field | null) => void;
  fields: Field[];
  setFields: (fields: Field[]) => void;
  selectedEquipment: Equipment | null;
  setSelectedEquipment: (equipment: Equipment | null) => void;
  alerts: Alert[];
  setAlerts: (alerts: Alert[]) => void;
  markAlertAsRead: (alertId: string) => void;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  notificationsOpen: boolean;
  toggleNotifications: () => void;
  reset: () => void;
}

const initialState = {
  tenantId: process.env.EXPO_PUBLIC_TENANT_ID || "demo-tenant",
  user: null,
  selectedField: null,
  fields: [],
  selectedEquipment: null,
  alerts: [],
  sidebarOpen: true,
  notificationsOpen: false,
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      ...initialState,
      setTenantId: (id) => set({ tenantId: id }),
      setUser: (user) => set({ user }),
      setSelectedField: (field) => set({ selectedField: field }),
      setFields: (fields) => set({ fields }),
      setSelectedEquipment: (equipment) => set({ selectedEquipment: equipment }),
      setAlerts: (alerts) => set({ alerts }),
      markAlertAsRead: (alertId) => set((state) => ({
        alerts: state.alerts.map((alert) =>
          alert.id === alertId ? { ...alert, isRead: true } : alert
        ),
      })),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      toggleNotifications: () => set((state) => ({ notificationsOpen: !state.notificationsOpen })),
      reset: () => {
        set(initialState);
        AsyncStorage.removeItem("app-storage");
      },
    }),
    {
      name: "app-storage",
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        tenantId: state.tenantId,
        user: state.user,
        selectedField: state.selectedField,
        fields: state.fields,
        alerts: state.alerts,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);
STOREEOF
    success "Created: App Store"

    success "Types & Store configured"
}

# ==================== PART 4: API CLIENT ====================
part4_api_client() {
    print_step "4" "Setting Up API Client"

    # FIXED: Added proper imports for Platform and types
    cat > lib/api/client.ts << 'APIEOF'
import axios, { AxiosInstance, AxiosError, AxiosResponse } from "axios";
import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";
import { ApiResponse, ApiError, Field, WeatherData, NDVIEntry, Alert, Equipment } from "@/types";

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
        config.headers["X-Client-Version"] = "4.2.1";
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
          // Here you would typically redirect to login
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
APIEOF
    success "Created: API Client"

    success "API Client configured"
}

# ==================== PART 5: HOOKS ====================
part5_hooks() {
    print_step "5" "Creating Custom Hooks"

    # FIXED: Added proper type imports
    cat > hooks/useSahoolData.ts << 'HOOKSDATAEOF'
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAppStore } from "@/store/appStore";
import { Field, WeatherData, NDVIEntry, Alert } from "@/types";

export function useSahoolQuery<T>(
  key: string[],
  fetchFn: () => Promise<{ data: { data: T } }>,
  options?: Partial<UseQueryOptions<T>>
) {
  return useQuery({
    queryKey: key,
    queryFn: async () => {
      const response = await fetchFn();
      return response.data.data;
    },
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 60,
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
    retry: 3,
    ...options,
  });
}

export function useFields() {
  const { tenantId } = useAppStore();
  return useSahoolQuery<Field[]>(
    ["fields", tenantId],
    () => api.getFields(tenantId),
    { enabled: !!tenantId, staleTime: 1000 * 60 * 10 }
  );
}

export function useWeather(lat: number, lon: number) {
  return useSahoolQuery<WeatherData>(
    ["weather", String(lat), String(lon)],
    () => api.getWeatherData(lat, lon),
    { refetchInterval: 1000 * 60 * 15 }
  );
}

export function useNDVI(fieldId: string) {
  return useSahoolQuery<NDVIEntry[]>(
    ["ndvi", fieldId],
    () => api.getNDVITimeline(fieldId),
    { enabled: !!fieldId, refetchInterval: 1000 * 60 * 60 * 6 }
  );
}

export function useAIChat() {
  return useMutation({
    mutationFn: async ({ message, context }: { message: string; context: any }) => {
      const response = await api.chatWithAI(message, context);
      return response.data.data;
    },
  });
}

export function useAlerts() {
  const { tenantId } = useAppStore();
  return useSahoolQuery<Alert[]>(
    ["alerts", tenantId],
    () => api.getActiveAlerts(tenantId),
    { enabled: !!tenantId, refetchInterval: 1000 * 60 * 5 }
  );
}
HOOKSDATAEOF
    success "Created: Sahool Data Hooks"

    cat > hooks/useMicroInteraction.ts << 'HOOKSMICROEOF'
import { useCallback } from "react";
import {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from "react-native-reanimated";

export function usePressAnimation() {
  const scale = useSharedValue(1);

  const pressIn = useCallback(() => {
    scale.value = withSpring(0.95, { stiffness: 500, damping: 10 });
  }, []);

  const pressOut = useCallback(() => {
    scale.value = withSpring(1, { stiffness: 500, damping: 10 });
  }, []);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return { pressIn, pressOut, animatedStyle, scale };
}
HOOKSMICROEOF
    success "Created: Micro Interaction Hook"

    cat > hooks/useAstralData.ts << 'HOOKSASTRALEOF'
import { useQuery } from "@tanstack/react-query";
import { AstralData, AstralRecommendation } from "@/types";

interface AstralQueryParams {
  date: Date;
  location: { latitude: number; longitude: number };
  fieldId?: string;
}

function calculateMoonPhase(date: Date): string {
  const knownNewMoon = new Date("2024-01-11");
  const daysSince = (date.getTime() - knownNewMoon.getTime()) / (1000 * 60 * 60 * 24);
  const lunarCycle = 29.53;
  const phase = (daysSince % lunarCycle) / lunarCycle;

  if (phase < 0.03 || phase > 0.97) return "new";
  if (phase < 0.22) return "waxing_crescent";
  if (phase < 0.28) return "first_quarter";
  if (phase < 0.47) return "waxing_gibbous";
  if (phase < 0.53) return "full";
  if (phase < 0.72) return "waning_gibbous";
  if (phase < 0.78) return "last_quarter";
  return "waning_crescent";
}

function getZodiacSign(date: Date): string {
  const signs = ["Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"];
  const month = date.getMonth() + 1;
  const day = date.getDate();

  const boundaries = [20, 19, 21, 20, 21, 21, 23, 23, 23, 23, 22, 22];
  const index = day < boundaries[month - 1] ? (month + 10) % 12 : (month + 11) % 12;

  return signs[index];
}

function generateRecommendations(moonPhase: string, zodiac: string): AstralRecommendation[] {
  return [
    {
      activity: "Deep watering",
      time: "Before sunrise",
      reason: "Moon phase enhances water absorption",
      zodiac: zodiac,
      star: "Sirius",
    },
    {
      activity: "Foliar feeding",
      time: "Afternoon",
      reason: "Current zodiac favors foliar nutrition",
      zodiac: zodiac,
      star: "Betelgeuse",
    },
  ];
}

async function fetchAstralData(params: AstralQueryParams): Promise<AstralData> {
  const moonPhase = calculateMoonPhase(params.date);
  const zodiacSign = getZodiacSign(params.date);

  return {
    moonPhase,
    moonIllumination: Math.random(),
    zodiacSign,
    starPosition: "Sirius",
    date: params.date.toISOString(),
    recommendations: generateRecommendations(moonPhase, zodiacSign),
  };
}

export function useAstralData(params: AstralQueryParams) {
  return useQuery({
    queryKey: ["astral", params.date.toDateString(), params.fieldId],
    queryFn: () => fetchAstralData(params),
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}
HOOKSASTRALEOF
    success "Created: Astral Data Hook"

    # Export hooks
    cat > hooks/index.ts << 'HOOKSINDEXEOF'
export * from "./useSahoolData";
export * from "./useMicroInteraction";
export * from "./useAstralData";
HOOKSINDEXEOF
    success "Created: Hooks index"

    success "Hooks created"
}

# ==================== PART 6: COMPONENTS ====================
part6_components() {
    print_step "6" "Creating Core Components"

    # Loading Component
    cat > components/ui/Loading.tsx << 'LOADINGEOF'
import React from "react";
import { View, Text, ActivityIndicator, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

interface LoadingProps {
  message?: string;
  size?: "small" | "large";
  style?: "default" | "overlay";
}

export function Loading({ message = "Loading...", size = "large", style = "default" }: LoadingProps) {
  if (style === "overlay") {
    return (
      <View style={styles.overlay}>
        <LinearGradient colors={["#1B4D3E", "#14352B"]} style={styles.overlayBox}>
          <ActivityIndicator size={size} color="#F4D03F" />
          <Text style={styles.message}>{message}</Text>
        </LinearGradient>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <LinearGradient colors={["#1B4D3E", "#14352B"]} style={styles.box}>
        <ActivityIndicator size={size} color="#F4D03F" />
        <Text style={styles.message}>{message}</Text>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0D1F17",
    alignItems: "center",
    justifyContent: "center",
  },
  overlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(13, 31, 23, 0.8)",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 50,
  },
  box: {
    padding: 32,
    borderRadius: 24,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "rgba(244, 208, 63, 0.2)",
  },
  overlayBox: {
    padding: 24,
    borderRadius: 16,
    alignItems: "center",
  },
  message: {
    color: "#F4D03F",
    marginTop: 24,
    fontSize: 18,
  },
});
LOADINGEOF
    success "Created: Loading Component"

    # FIXED: Button Component with proper Animated import
    cat > components/ui/Button.tsx << 'BUTTONEOF'
import React from "react";
import { Text, TouchableOpacity, ActivityIndicator, StyleSheet, ViewStyle } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated from "react-native-reanimated";
import { usePressAnimation } from "@/hooks/useMicroInteraction";
import { LucideIcon } from "lucide-react-native";

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  icon?: LucideIcon;
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
}

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export function Button({
  title,
  onPress,
  variant = "primary",
  size = "md",
  icon: Icon,
  loading = false,
  disabled = false,
  style,
}: ButtonProps) {
  const { pressIn, pressOut, animatedStyle } = usePressAnimation();

  const gradients: Record<string, [string, string]> = {
    primary: ["#F4D03F", "#F7DC6F"],
    secondary: ["#1B4D3E", "#2D6A4F"],
    danger: ["#E74C3C", "#C0392B"],
    ghost: ["transparent", "transparent"],
  };

  const sizes: Record<string, ViewStyle> = {
    sm: { paddingHorizontal: 16, paddingVertical: 8 },
    md: { paddingHorizontal: 24, paddingVertical: 12 },
    lg: { paddingHorizontal: 32, paddingVertical: 16 },
  };

  const textColor = variant === "primary" ? "#1B4D3E" : "#FFFFFF";

  return (
    <AnimatedTouchable
      onPressIn={pressIn}
      onPressOut={pressOut}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
      style={[animatedStyle, style]}
    >
      <LinearGradient
        colors={gradients[variant]}
        style={[styles.button, sizes[size]]}
      >
        {loading ? (
          <ActivityIndicator color={textColor} />
        ) : (
          <>
            {Icon && <Icon size={20} color={textColor} style={styles.icon} />}
            <Text style={[styles.text, { color: textColor }]}>
              {title}
            </Text>
          </>
        )}
      </LinearGradient>
    </AnimatedTouchable>
  );
}

const styles = StyleSheet.create({
  button: {
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
  },
  text: {
    fontWeight: "600",
    fontSize: 16,
  },
  icon: {
    marginRight: 8,
  },
});
BUTTONEOF
    success "Created: Button Component"

    # FIXED: SahoolCard Component with proper Animated import
    cat > components/cards/SahoolCard.tsx << 'CARDEOF'
import React from "react";
import { View, Text, TouchableOpacity, Image, StyleSheet, ViewStyle } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated from "react-native-reanimated";
import { usePressAnimation } from "@/hooks/useMicroInteraction";
import { LucideIcon } from "lucide-react-native";

interface SahoolCardProps {
  icon?: LucideIcon;
  image?: string;
  title: string;
  subtitle?: string;
  value?: string;
  badge?: string;
  gradient?: [string, string];
  onPress?: () => void;
  variant?: "default" | "compact" | "featured";
  style?: ViewStyle;
}

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export function SahoolCard({
  icon: Icon,
  image,
  title,
  subtitle,
  value,
  badge,
  gradient = ["#1B4D3E", "#14352B"],
  onPress,
  variant = "default",
  style,
}: SahoolCardProps) {
  const { pressIn, pressOut, animatedStyle } = usePressAnimation();

  const variantStyles: Record<string, ViewStyle> = {
    default: { padding: 20 },
    compact: { padding: 12 },
    featured: { padding: 24 },
  };

  return (
    <AnimatedTouchable
      onPressIn={pressIn}
      onPressOut={pressOut}
      onPress={onPress}
      activeOpacity={0.7}
      style={[animatedStyle, style]}
    >
      <LinearGradient
        colors={gradient}
        style={[styles.card, variantStyles[variant]]}
      >
        {image && (
          <Image
            source={{ uri: image }}
            style={styles.image}
            resizeMode="cover"
          />
        )}

        <View style={styles.content}>
          <View style={styles.header}>
            {Icon && (
              <View style={styles.iconContainer}>
                <Icon size={20} color="#F4D03F" />
              </View>
            )}
            <View style={styles.titleContainer}>
              <Text style={styles.title}>{title}</Text>
              {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
            </View>
          </View>

          {badge && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{badge}</Text>
            </View>
          )}
        </View>

        {value && (
          <Text style={styles.value}>{value}</Text>
        )}
      </LinearGradient>
    </AnimatedTouchable>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.1)",
  },
  image: {
    width: "100%",
    height: 128,
    borderRadius: 12,
    marginBottom: 12,
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    marginBottom: 8,
  },
  iconContainer: {
    width: 40,
    height: 40,
    backgroundColor: "rgba(244, 208, 63, 0.2)",
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  titleContainer: {
    flex: 1,
  },
  title: {
    color: "#FFFFFF",
    fontWeight: "700",
    fontSize: 18,
  },
  subtitle: {
    color: "rgba(255, 255, 255, 0.6)",
    fontSize: 14,
  },
  badge: {
    backgroundColor: "rgba(244, 208, 63, 0.2)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 9999,
    alignSelf: "flex-start",
    marginTop: 8,
  },
  badgeText: {
    color: "#F4D03F",
    fontSize: 12,
    fontWeight: "500",
  },
  value: {
    color: "#F4D03F",
    fontSize: 24,
    fontWeight: "900",
    marginLeft: 16,
  },
});
CARDEOF
    success "Created: Sahool Card Component"

    # Component exports
    cat > components/index.ts << 'COMPONENTSINDEXEOF'
export * from "./ui/Loading";
export * from "./ui/Button";
export * from "./cards/SahoolCard";
COMPONENTSINDEXEOF
    success "Created: Components index"

    success "Components created"
}

# ==================== PART 7: SCREENS ====================
part7_screens() {
    print_step "7" "Creating Application Screens"

    # Root Layout
    cat > app/_layout.tsx << 'ROOTLAYOUTEOF'
import { useEffect } from "react";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
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
  useEffect(() => {
    SplashScreen.hideAsync();
  }, []);

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
}
ROOTLAYOUTEOF
    success "Created: Root Layout"

    # Tabs Layout
    cat > app/tabs/_layout.tsx << 'TABLAYOUTEOF'
import { Tabs } from "expo-router";
import { View, StyleSheet, Platform } from "react-native";
import { Home, Map, Bell, Brain, User } from "lucide-react-native";
import { useAppStore } from "@/store/appStore";

export default function TabLayout() {
  const { alerts } = useAppStore();
  const unreadCount = alerts.filter(a => !a.isRead).length;

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
              {unreadCount > 0 && <View style={styles.badge} />}
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="assistant"
        options={{
          title: "AI",
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
  tabBarLabel: {
    fontSize: 11,
    fontWeight: "600",
  },
  badge: {
    position: "absolute",
    top: -4,
    right: -8,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#E74C3C",
  },
});
TABLAYOUTEOF
    success "Created: Tab Layout"

    # FIXED: Dashboard Screen with proper Loading import
    cat > app/tabs/index.tsx << 'DASHBOARDEOF'
import React from "react";
import { View, Text, ScrollView, StyleSheet } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { SahoolCard } from "@/components/cards/SahoolCard";
import { Loading } from "@/components/ui/Loading";
import { useFields, useAlerts } from "@/hooks/useSahoolData";
import { useAppStore } from "@/store/appStore";
import { MapPin, Sprout, AlertTriangle, Brain, Calendar } from "lucide-react-native";
import { useRouter } from "expo-router";

export default function DashboardScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAppStore();
  const { data: fields, isLoading: fieldsLoading } = useFields();
  const { data: alerts } = useAlerts();

  if (fieldsLoading) {
    return <Loading message="Initializing your farm..." />;
  }

  const urgentAlerts = alerts?.filter(a => a.severity === "high" || a.severity === "critical") || [];
  const avgHealth = fields?.length
    ? Math.round(fields.reduce((sum, f) => sum + f.healthScore, 0) / fields.length)
    : 0;

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingTop: insets.top, paddingBottom: 100 }}>
      <View style={styles.header}>
        <Text style={styles.greeting}>
          Good morning! {user?.name?.split(" ")[0] || "Farmer"}
        </Text>
        <Text style={styles.subtitle}>
          You have {fields?.length || 0} active fields
        </Text>
      </View>

      <View style={styles.kpiGrid}>
        <SahoolCard
          icon={Sprout}
          title="Field Health"
          value={`${avgHealth}%`}
          subtitle="Average score"
          onPress={() => router.push("/analytics")}
          style={styles.kpiCard}
        />
        <SahoolCard
          icon={AlertTriangle}
          title="Urgent Alerts"
          value={String(urgentAlerts.length)}
          subtitle="Need attention"
          gradient={["#E74C3C", "#C0392B"]}
          onPress={() => router.push("/alerts")}
          style={styles.kpiCard}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Active Fields</Text>
        {fields?.slice(0, 3).map((field) => (
          <SahoolCard
            key={field.id}
            icon={MapPin}
            title={field.name}
            value={`${field.acreage} ha`}
            subtitle={`Health: ${field.healthScore}% | ${field.cropType}`}
            onPress={() => router.push(`/field/${field.id}`)}
            style={styles.fieldCard}
          />
        ))}
      </View>

      <View style={styles.section}>
        <SahoolCard
          icon={Brain}
          title="AI Assistant"
          subtitle="Ask about your farm"
          gradient={["rgba(244, 208, 63, 0.2)", "rgba(244, 208, 63, 0.1)"]}
          onPress={() => router.push("/assistant")}
        />
      </View>

      <View style={styles.section}>
        <SahoolCard
          icon={Calendar}
          title="Astral Calendar"
          subtitle="Farming recommendations"
          gradient={["#2D6A4F", "#1B4D3E"]}
          onPress={() => router.push("/astral-calendar")}
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0D1F17",
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 24,
  },
  greeting: {
    fontSize: 28,
    fontWeight: "900",
    color: "#FFFFFF",
  },
  subtitle: {
    fontSize: 18,
    color: "#F4D03F",
    marginTop: 8,
  },
  kpiGrid: {
    flexDirection: "row",
    paddingHorizontal: 16,
    gap: 12,
  },
  kpiCard: {
    flex: 1,
  },
  section: {
    paddingHorizontal: 16,
    marginTop: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "900",
    color: "#FFFFFF",
    marginBottom: 16,
  },
  fieldCard: {
    marginBottom: 12,
  },
});
DASHBOARDEOF
    success "Created: Dashboard Screen"

    # Placeholder screens
    for screen in fields alerts assistant profile; do
        cat > "app/tabs/${screen}.tsx" << SCREENEOF
import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function ${screen^}Screen() {
  const insets = useSafeAreaInsets();

  return (
    <LinearGradient colors={["#0D1F17", "#1B4D3E"]} style={styles.container}>
      <View style={[styles.content, { paddingTop: insets.top + 20 }]}>
        <Text style={styles.title}>${screen^}</Text>
        <Text style={styles.subtitle}>Coming soon...</Text>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { flex: 1, padding: 16, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 28, fontWeight: "700", color: "#FFFFFF", marginBottom: 8 },
  subtitle: { fontSize: 16, color: "#F4D03F" },
});
SCREENEOF
        success "Created: ${screen^} Screen"
    done

    success "Screens created"
}

# ==================== PART 8: CI/CD & SCRIPTS ====================
part8_cicd_scripts() {
    print_step "8" "Setting Up CI/CD & Utility Scripts"

    # GitHub Actions
    cat > .github/workflows/mobile-ci.yml << 'CICDEOF'
name: SAHOOL Mobile CI/CD

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
    if: github.ref == 'refs/heads/main'
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
      - run: eas build --platform all --profile production --non-interactive
CICDEOF
    success "Created: CI/CD Pipeline"

    # EAS config
    cat > eas.json << 'EASEOF'
{
  "cli": {
    "version": ">= 7.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "autoIncrement": true
    }
  },
  "submit": {
    "production": {}
  }
}
EASEOF
    success "Created: EAS config"

    # Scripts
    cat > scripts/run-dev.sh << 'DEVSCRIPTEOF'
#!/bin/bash
npm start
DEVSCRIPTEOF
    chmod +x scripts/run-dev.sh
    success "Created: Development script"

    cat > scripts/run-prod.sh << 'PRODSCRIPTEOF'
#!/bin/bash
npm run build && npm start -- --no-dev
PRODSCRIPTEOF
    chmod +x scripts/run-prod.sh
    success "Created: Production script"

    success "CI/CD & scripts configured"
}

# ==================== PART 9: CLEANUP & FINALIZE ====================
part9_finalize() {
    print_step "9" "Finalizing Setup"

    # Create README
    cat > README.md << READMEEOF
# SAHOOL Mobile v${VERSION}

Smart Agricultural Platform - Mobile Application

## Quick Start

\`\`\`bash
# Install dependencies
npm install

# Start development server
npm start

# Build for devices
eas build --platform all --profile development
\`\`\`

## Scripts

- \`npm start\` - Start dev server
- \`npm run lint\` - Lint code
- \`./scripts/run-dev.sh\` - Development mode
- \`./scripts/run-prod.sh\` - Production mode

## Tech Stack

- React Native + Expo SDK 51
- TypeScript
- NativeWind (Tailwind CSS)
- Zustand (State Management)
- TanStack Query v5 (Data Fetching)
- Expo Router

## Features

- Dashboard with real-time KPIs
- AI Assistant
- Interactive maps with NDVI
- Astral calendar
- Push notifications
- IoT Equipment tracking

## Configuration

Edit \`.env\` with your values.

## License

MIT - SAHOOL Team
READMEEOF
    success "Created: README"

    # Clean up
    rm -f .setup.env.tmp 2>/dev/null || true

    success "Setup completed successfully!"
}

# ==================== MAIN EXECUTION ====================
main() {
    print_header

    # Check requirements first
    check_requirements

    # Get user input
    get_user_input

    # Execute all parts
    part1_project_init
    part2_configuration
    part3_types_store
    part4_api_client
    part5_hooks
    part6_components
    part7_screens
    part8_cicd_scripts
    part9_finalize

    # Final messages
    echo -e ""
    echo -e "${GREEN}${BOLD}================================${NC}"
    echo -e "${GREEN}${BOLD}  Setup Complete!${NC}"
    echo -e "${GREEN}${BOLD}================================${NC}"
    echo -e ""
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "  1. ${WHITE}cd ${PROJECT_NAME}${NC}"
    echo -e "  2. ${WHITE}npm start${NC}"
    echo -e "  3. ${WHITE}eas login${NC} (if not already logged in)"
    echo -e "  4. ${WHITE}eas build --platform all --profile development${NC}"
    echo -e ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo -e "  - If 'command not found', run: ${BLUE}npm install -g eas-cli${NC}"
    echo -e "  - If build fails, check: ${BLUE}./setup.log${NC}"
    echo -e "  - For API setup, see: ${BLUE}${API_URL}/docs${NC}"
    echo -e ""
    echo -e "${MAGENTA}Documentation:${NC} ${BLUE}https://docs.sahool.agri${NC}"
    echo -e ""
}

# ==================== ERROR HANDLING ====================
trap 'error "Script failed at line $LINENO"' ERR

# Check for bash version
if [ -z "$BASH_VERSION" ]; then
    error "This script requires bash. Run: bash $0"
fi

# Check for required commands
for cmd in node npm npx; do
    if ! command -v $cmd &> /dev/null; then
        error "$cmd is required but not installed"
    fi
done

# Execute main function
main "$@"
