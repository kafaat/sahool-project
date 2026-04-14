#!/bin/bash
# ==============================================================================
# Part 05: Frontend
# React + TypeScript + Tailwind with proper syntax
# ==============================================================================

generate_frontend() {
    log_info "Creating Frontend..."

    mkdir -p frontend/{src/{components,pages,hooks,stores,api,types,i18n},public}

    # ------------------------------------------------------------------------------
    # Package.json (FIXED - proper quotes)
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/package.json" << 'JSONEOF'
{
  "name": "field-suite-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext .ts,.tsx",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.0",
    "zustand": "^4.4.0",
    "leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1",
    "recharts": "^2.10.0",
    "i18next": "^23.7.0",
    "react-i18next": "^14.0.0",
    "date-fns": "^3.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@types/leaflet": "^1.9.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vite-plugin-pwa": "^0.17.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.56.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0"
  }
}
JSONEOF

    # ------------------------------------------------------------------------------
    # Vite Config
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/vite.config.ts" << 'TSEOF'
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.ico", "robots.txt"],
      manifest: {
        name: "Field Suite Platform",
        short_name: "FieldSuite",
        theme_color: "#16a34a",
        background_color: "#ffffff",
        display: "standalone",
        icons: [
          {
            src: "/icon-192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "/icon-512.png",
            sizes: "512x512",
            type: "image/png",
          },
        ],
      },
    }),
  ],
  server: {
    port: 3000,
    host: true,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
TSEOF

    # ------------------------------------------------------------------------------
    # TypeScript Config
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/tsconfig.json" << 'JSONEOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
JSONEOF

    # ------------------------------------------------------------------------------
    # Tailwind Config
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/tailwind.config.js" << 'JSEOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ndvi: {
          critical: "#dc2626",
          poor: "#f97316",
          moderate: "#eab308",
          good: "#22c55e",
          excellent: "#15803d",
        },
        primary: {
          50: "#f0fdf4",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
        },
      },
    },
  },
  plugins: [],
};
JSEOF

    # ------------------------------------------------------------------------------
    # API Client (FIXED - proper template literals)
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/src/api/client.ts" << 'TSEOF'
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

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

  private setupInterceptors(): void {
    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem("access_token");
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: AxiosError) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Try refresh token
          const refreshed = await this.refreshToken();
          if (refreshed && error.config) {
            return this.client.request(error.config);
          }
          // Logout on refresh failure
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    );
  }

  private async refreshToken(): Promise<boolean> {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) return false;

    try {
      const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      });
      localStorage.setItem("access_token", response.data.access_token);
      return true;
    } catch {
      return false;
    }
  }

  // Fields API
  async getFields(page = 1, size = 20) {
    const { data } = await this.client.get(`/fields?page=${page}&size=${size}`);
    return data;
  }

  async getField(fieldId: number) {
    const { data } = await this.client.get(`/fields/${fieldId}`);
    return data;
  }

  async createField(fieldData: Record<string, unknown>) {
    const { data } = await this.client.post("/fields", fieldData);
    return data;
  }

  // NDVI API
  async getNdviLatest(fieldId: number) {
    const { data } = await this.client.get(`/ndvi/field/${fieldId}/latest`);
    return data;
  }

  async getNdviTimeline(fieldId: number, limit = 30) {
    const { data } = await this.client.get(`/ndvi/field/${fieldId}/timeline?limit=${limit}`);
    return data;
  }

  async triggerNdviComputation(fieldIds: number[]) {
    const { data } = await this.client.post("/ndvi/compute", { field_ids: fieldIds });
    return data;
  }

  // Advisor API
  async getFieldAnalysis(fieldId: number) {
    const { data } = await this.client.get(`/advisor/field/${fieldId}`);
    return data;
  }

  // Auth API
  async login(email: string, password: string) {
    const { data } = await this.client.post("/auth/login", { email, password });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    return data;
  }

  async logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }
}

export const apiClient = new ApiClient();
TSEOF

    # ------------------------------------------------------------------------------
    # Auth Store (Zustand)
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/src/stores/authStore.ts" << 'TSEOF'
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: number;
  email: string;
  fullName: string;
  tenantId: string;
  roles: string[];
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, isAuthenticated: false });
      },
    }),
    {
      name: "auth-storage",
    }
  )
);
TSEOF

    # ------------------------------------------------------------------------------
    # Types
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/src/types/index.ts" << 'TSEOF'
export interface Field {
  id: number;
  tenantId: string;
  name: string;
  description?: string;
  cropType?: string;
  areaHectares?: number;
  center?: { lat: number; lng: number };
  createdAt: string;
  updatedAt: string;
}

export interface NdviResult {
  id: number;
  fieldId: number;
  captureDate: string;
  meanNdvi: number;
  minNdvi: number;
  maxNdvi: number;
  stdNdvi: number;
  healthScore: number;
  zones: NdviZone[];
}

export interface NdviZone {
  zone: string;
  minValue: number;
  maxValue: number;
  areaPercentage: number;
  healthStatus: string;
}

export interface Recommendation {
  type: string;
  priority: string;
  title: string;
  description: string;
  action: string;
  confidence: number;
}

export interface FieldAnalysis {
  fieldId: number;
  analysisDate: string;
  overallHealthScore: number;
  recommendations: Recommendation[];
  alerts: Array<{ level: string; message: string }>;
  nextActions: string[];
}
TSEOF

    # ------------------------------------------------------------------------------
    # Components
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/src/components/Layout.tsx" << 'TSXEOF'
import { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";
import { useTranslation } from "react-i18next";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const navItems = [
    { path: "/", label: t("nav.dashboard"), icon: "📊" },
    { path: "/fields", label: t("nav.fields"), icon: "🌾" },
    { path: "/advisor", label: t("nav.advisor"), icon: "🤖" },
    { path: "/settings", label: t("nav.settings"), icon: "⚙️" },
  ];

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === "ar" ? "en" : "ar");
  };

  return (
    <div className="min-h-screen bg-gray-50" dir={i18n.language === "ar" ? "rtl" : "ltr"}>
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-64 bg-white shadow-lg">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-primary-600">Field Suite</h1>
        </div>

        <nav className="mt-6">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center px-6 py-3 text-gray-700 hover:bg-gray-100 ${
                location.pathname === item.path ? "bg-primary-50 text-primary-600 border-r-4 border-primary-600" : ""
              }`}
            >
              <span className="mr-3">{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-gray-600">{user?.fullName}</span>
            <button
              onClick={logout}
              className="text-sm text-red-600 hover:underline"
            >
              {t("auth.logout")}
            </button>
          </div>
          <button
            onClick={toggleLanguage}
            className="w-full py-2 text-sm bg-gray-100 rounded hover:bg-gray-200"
          >
            {i18n.language === "ar" ? "English" : "العربية"}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-64 p-8">{children}</main>
    </div>
  );
}
TSXEOF

    write_heredoc "frontend/src/components/HealthIndicator.tsx" << 'TSXEOF'
interface HealthIndicatorProps {
  score: number;
  size?: "sm" | "md" | "lg";
}

export function HealthIndicator({ score, size = "md" }: HealthIndicatorProps) {
  const getColor = (score: number): string => {
    if (score >= 80) return "bg-ndvi-excellent";
    if (score >= 60) return "bg-ndvi-good";
    if (score >= 40) return "bg-ndvi-moderate";
    if (score >= 20) return "bg-ndvi-poor";
    return "bg-ndvi-critical";
  };

  const sizeClasses = {
    sm: "w-8 h-8 text-xs",
    md: "w-12 h-12 text-sm",
    lg: "w-16 h-16 text-lg",
  };

  return (
    <div
      className={`${sizeClasses[size]} ${getColor(score)} rounded-full flex items-center justify-center text-white font-bold`}
    >
      {Math.round(score)}
    </div>
  );
}
TSXEOF

    # ------------------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/src/pages/Dashboard.tsx" << 'TSXEOF'
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { HealthIndicator } from "../components/HealthIndicator";
import { useTranslation } from "react-i18next";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export function Dashboard() {
  const { t } = useTranslation();

  const { data: fields, isLoading } = useQuery({
    queryKey: ["fields"],
    queryFn: () => apiClient.getFields(),
  });

  if (isLoading) {
    return <div className="flex justify-center p-8">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">{t("dashboard.title")}</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          title={t("dashboard.totalFields")}
          value={fields?.total || 0}
          icon="🌾"
        />
        <StatCard
          title={t("dashboard.healthyFields")}
          value={fields?.items?.filter((f: { healthScore?: number }) => (f.healthScore || 0) > 60).length || 0}
          icon="✅"
          color="text-green-600"
        />
        <StatCard
          title={t("dashboard.needsAttention")}
          value={fields?.items?.filter((f: { healthScore?: number }) => (f.healthScore || 0) < 40).length || 0}
          icon="⚠️"
          color="text-yellow-600"
        />
        <StatCard
          title={t("dashboard.avgHealth")}
          value={`${Math.round(fields?.items?.reduce((acc: number, f: { healthScore?: number }) => acc + (f.healthScore || 50), 0) / (fields?.items?.length || 1))}%`}
          icon="📊"
        />
      </div>

      {/* Recent Fields */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">{t("dashboard.recentFields")}</h2>
        <div className="space-y-4">
          {fields?.items?.slice(0, 5).map((field: { id: number; name: string; cropType?: string; healthScore?: number }) => (
            <div key={field.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <h3 className="font-medium">{field.name}</h3>
                <p className="text-sm text-gray-500">{field.cropType || "Unknown crop"}</p>
              </div>
              <HealthIndicator score={field.healthScore || 50} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color = "text-gray-900" }: {
  title: string;
  value: string | number;
  icon: string;
  color?: string;
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <span className="text-2xl">{icon}</span>
      </div>
      <p className="mt-4 text-sm text-gray-500">{title}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
TSXEOF

    # ------------------------------------------------------------------------------
    # i18n
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/src/i18n/index.ts" << 'TSEOF'
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  en: {
    translation: {
      nav: {
        dashboard: "Dashboard",
        fields: "Fields",
        advisor: "Advisor",
        settings: "Settings",
      },
      dashboard: {
        title: "Dashboard",
        totalFields: "Total Fields",
        healthyFields: "Healthy Fields",
        needsAttention: "Needs Attention",
        avgHealth: "Average Health",
        recentFields: "Recent Fields",
      },
      auth: {
        login: "Login",
        logout: "Logout",
        email: "Email",
        password: "Password",
      },
    },
  },
  ar: {
    translation: {
      nav: {
        dashboard: "لوحة التحكم",
        fields: "الحقول",
        advisor: "المستشار",
        settings: "الإعدادات",
      },
      dashboard: {
        title: "لوحة التحكم",
        totalFields: "إجمالي الحقول",
        healthyFields: "حقول صحية",
        needsAttention: "تحتاج اهتمام",
        avgHealth: "متوسط الصحة",
        recentFields: "الحقول الأخيرة",
      },
      auth: {
        login: "تسجيل الدخول",
        logout: "تسجيل الخروج",
        email: "البريد الإلكتروني",
        password: "كلمة المرور",
      },
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: "en",
  fallbackLng: "en",
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
TSEOF

    # ------------------------------------------------------------------------------
    # Main App
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/src/App.tsx" << 'TSXEOF'
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { useAuthStore } from "./stores/authStore";
import "./i18n";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
TSXEOF

    # ------------------------------------------------------------------------------
    # Entry files
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/src/main.tsx" << 'TSXEOF'
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
TSXEOF

    write_heredoc "frontend/src/index.css" << 'CSSEOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: "Inter", system-ui, sans-serif;
}
CSSEOF

    write_heredoc "frontend/index.html" << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#16a34a" />
    <title>Field Suite Platform</title>
    <link rel="icon" href="/favicon.ico" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
HTMLEOF

    # ------------------------------------------------------------------------------
    # Dockerfile
    # ------------------------------------------------------------------------------
    write_heredoc "frontend/Dockerfile" << 'DOCKERFILE'
FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
DOCKERFILE

    write_heredoc "frontend/nginx.conf" << 'NGINXEOF'
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINXEOF

    log_success "Frontend created"
}
