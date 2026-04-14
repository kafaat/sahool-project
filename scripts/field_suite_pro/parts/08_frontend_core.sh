#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Part 8: Frontend Core - React + TypeScript + Tailwind
# ═══════════════════════════════════════════════════════════════════════════════

log_info "إنشاء ملفات الواجهة الأمامية الأساسية..."

# ─────────────────────────────────────────────────────────────────────────────
# Package.json
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/package.json" << 'EOF'
{
  "name": "field-suite-pro",
  "version": "2.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:coverage": "vitest run --coverage",
    "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "format": "prettier --write src"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.0.0",
    "@tanstack/react-query-devtools": "^5.0.0",
    "axios": "^1.6.0",
    "clsx": "^2.0.0",
    "date-fns": "^2.30.0",
    "framer-motion": "^10.16.0",
    "i18next": "^23.7.0",
    "i18next-browser-languagedetector": "^7.2.0",
    "leaflet": "^1.9.4",
    "lucide-react": "^0.292.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-helmet-async": "^2.0.0",
    "react-hook-form": "^7.48.0",
    "react-i18next": "^13.5.0",
    "react-leaflet": "^4.2.1",
    "react-router-dom": "^6.20.0",
    "recharts": "^2.10.0",
    "tailwind-merge": "^2.0.0",
    "zod": "^3.22.0",
    "zustand": "^4.4.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/react": "^14.1.0",
    "@types/leaflet": "^1.9.8",
    "@types/node": "^20.10.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^6.13.0",
    "@typescript-eslint/parser": "^6.13.0",
    "@vitejs/plugin-react": "^4.2.0",
    "@vitest/coverage-v8": "^1.0.0",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "jsdom": "^23.0.0",
    "postcss": "^8.4.32",
    "prettier": "^3.1.0",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vite-plugin-pwa": "^0.17.0",
    "vitest": "^1.0.0"
  }
}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Vite Config
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/vite.config.ts" << 'EOF'
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt', 'apple-touch-icon.png'],
      manifest: {
        name: 'Field Suite Pro',
        short_name: 'FieldSuite',
        description: 'نظام إدارة الحقول الزراعية المتقدم',
        theme_color: '#16a34a',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        icons: [
          {
            src: '/icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
EOF

# ─────────────────────────────────────────────────────────────────────────────
# TypeScript Config
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/tsconfig.json" << 'EOF'
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
EOF

cat > "$PROJECT_NAME/web/tsconfig.node.json" << 'EOF'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Tailwind Config
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/tailwind.config.js" << 'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        ndvi: {
          critical: '#ef4444',
          low: '#f97316',
          medium: '#eab308',
          high: '#22c55e',
          'very-high': '#15803d',
        }
      },
      fontFamily: {
        cairo: ['Cairo', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
EOF

cat > "$PROJECT_NAME/web/postcss.config.js" << 'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Index HTML
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="ar" dir="rtl">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="نظام إدارة الحقول الزراعية المتقدم" />
    <meta name="theme-color" content="#16a34a" />
    <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
    <link rel="manifest" href="/manifest.json" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
    <title>Field Suite Pro - نظام إدارة الحقول</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Main Entry
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/src/main.tsx" << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { HelmetProvider } from 'react-helmet-async';
import App from './App';
import './i18n';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HelmetProvider>
      <QueryClientProvider client={queryClient}>
        <App />
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </HelmetProvider>
  </React.StrictMode>
);
EOF

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/src/index.css" << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    font-family: 'Cairo', sans-serif;
  }

  body {
    @apply bg-gray-50 text-gray-900 antialiased;
    direction: rtl;
  }
}

@layer components {
  .btn {
    @apply inline-flex items-center justify-center px-4 py-2 rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed;
  }

  .btn-primary {
    @apply btn bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500;
  }

  .btn-secondary {
    @apply btn bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-500;
  }

  .btn-danger {
    @apply btn bg-red-600 text-white hover:bg-red-700 focus:ring-red-500;
  }

  .card {
    @apply bg-white rounded-xl shadow-sm border border-gray-100;
  }

  .input {
    @apply w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all;
  }

  .label {
    @apply block text-sm font-medium text-gray-700 mb-1;
  }
}

/* Leaflet customization */
.leaflet-container {
  @apply rounded-lg;
  font-family: 'Cairo', sans-serif;
}

/* NDVI color scale */
.ndvi-scale {
  background: linear-gradient(to right,
    #ef4444 0%,
    #f97316 25%,
    #eab308 50%,
    #22c55e 75%,
    #15803d 100%
  );
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  @apply bg-gray-100 rounded;
}

::-webkit-scrollbar-thumb {
  @apply bg-gray-300 rounded hover:bg-gray-400;
}

/* Loading spinner */
.spinner {
  @apply animate-spin rounded-full border-2 border-gray-300 border-t-primary-600;
}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# i18n Configuration
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/src/i18n/index.ts" << 'EOF'
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import ar from './locales/ar.json';
import en from './locales/en.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      ar: { translation: ar },
      en: { translation: en },
    },
    fallbackLng: 'ar',
    debug: false,
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
EOF

cat > "$PROJECT_NAME/web/src/i18n/locales/ar.json" << 'EOF'
{
  "common": {
    "loading": "جاري التحميل...",
    "error": "حدث خطأ",
    "save": "حفظ",
    "cancel": "إلغاء",
    "delete": "حذف",
    "edit": "تعديل",
    "add": "إضافة",
    "search": "بحث",
    "filter": "تصفية",
    "refresh": "تحديث",
    "back": "رجوع",
    "next": "التالي",
    "previous": "السابق"
  },
  "auth": {
    "login": "تسجيل الدخول",
    "logout": "تسجيل الخروج",
    "register": "إنشاء حساب",
    "email": "البريد الإلكتروني",
    "password": "كلمة المرور",
    "confirmPassword": "تأكيد كلمة المرور",
    "fullName": "الاسم الكامل",
    "forgotPassword": "نسيت كلمة المرور؟"
  },
  "nav": {
    "dashboard": "لوحة التحكم",
    "fields": "الحقول",
    "ndvi": "تحليل NDVI",
    "advisor": "المستشار",
    "reports": "التقارير",
    "settings": "الإعدادات"
  },
  "fields": {
    "title": "الحقول",
    "addField": "إضافة حقل",
    "fieldName": "اسم الحقل",
    "cropType": "نوع المحصول",
    "area": "المساحة",
    "status": "الحالة",
    "plantingDate": "تاريخ الزراعة",
    "harvestDate": "تاريخ الحصاد المتوقع"
  },
  "ndvi": {
    "title": "تحليل NDVI",
    "mean": "المتوسط",
    "min": "الأدنى",
    "max": "الأعلى",
    "std": "الانحراف المعياري",
    "zones": "المناطق",
    "timeline": "التسلسل الزمني",
    "critical": "حرج",
    "low": "منخفض",
    "medium": "متوسط",
    "high": "مرتفع",
    "veryHigh": "مرتفع جداً"
  },
  "advisor": {
    "title": "المستشار الزراعي",
    "analyze": "تحليل الحقل",
    "recommendations": "التوصيات",
    "alerts": "التنبيهات",
    "priority": {
      "critical": "حرج",
      "high": "عالي",
      "medium": "متوسط",
      "low": "منخفض"
    },
    "urgency": {
      "immediate": "فوري",
      "within_24h": "خلال 24 ساعة",
      "within_48h": "خلال 48 ساعة",
      "routine": "روتيني"
    }
  }
}
EOF

cat > "$PROJECT_NAME/web/src/i18n/locales/en.json" << 'EOF'
{
  "common": {
    "loading": "Loading...",
    "error": "An error occurred",
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "edit": "Edit",
    "add": "Add",
    "search": "Search",
    "filter": "Filter",
    "refresh": "Refresh",
    "back": "Back",
    "next": "Next",
    "previous": "Previous"
  },
  "auth": {
    "login": "Login",
    "logout": "Logout",
    "register": "Register",
    "email": "Email",
    "password": "Password",
    "confirmPassword": "Confirm Password",
    "fullName": "Full Name",
    "forgotPassword": "Forgot Password?"
  },
  "nav": {
    "dashboard": "Dashboard",
    "fields": "Fields",
    "ndvi": "NDVI Analysis",
    "advisor": "Advisor",
    "reports": "Reports",
    "settings": "Settings"
  },
  "fields": {
    "title": "Fields",
    "addField": "Add Field",
    "fieldName": "Field Name",
    "cropType": "Crop Type",
    "area": "Area",
    "status": "Status",
    "plantingDate": "Planting Date",
    "harvestDate": "Expected Harvest Date"
  },
  "ndvi": {
    "title": "NDVI Analysis",
    "mean": "Mean",
    "min": "Min",
    "max": "Max",
    "std": "Std Dev",
    "zones": "Zones",
    "timeline": "Timeline",
    "critical": "Critical",
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "veryHigh": "Very High"
  },
  "advisor": {
    "title": "Agricultural Advisor",
    "analyze": "Analyze Field",
    "recommendations": "Recommendations",
    "alerts": "Alerts",
    "priority": {
      "critical": "Critical",
      "high": "High",
      "medium": "Medium",
      "low": "Low"
    },
    "urgency": {
      "immediate": "Immediate",
      "within_24h": "Within 24h",
      "within_48h": "Within 48h",
      "routine": "Routine"
    }
  }
}
EOF

# ─────────────────────────────────────────────────────────────────────────────
# API Client
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/src/api/client.ts" << 'EOF'
import axios, { AxiosInstance, AxiosError } from 'axios';
import { useAuthStore } from '@/stores/authStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && originalRequest) {
      // Try to refresh token
      const refreshToken = useAuthStore.getState().refreshToken;
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;
          useAuthStore.getState().setTokens(access_token, refresh_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        } catch {
          useAuthStore.getState().logout();
          window.location.href = '/login';
        }
      } else {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
EOF

# ─────────────────────────────────────────────────────────────────────────────
# Auth Store (Zustand)
# ─────────────────────────────────────────────────────────────────────────────
cat > "$PROJECT_NAME/web/src/stores/authStore.ts" << 'EOF'
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  uuid: string;
  email: string;
  fullName: string;
  tenantId: number;
  role: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setUser: (user) => set({ user, isAuthenticated: true }),

      setTokens: (accessToken, refreshToken) =>
        set({ accessToken, refreshToken, isAuthenticated: true }),

      logout: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);
EOF

log_success "تم إنشاء ملفات الواجهة الأمامية الأساسية"
