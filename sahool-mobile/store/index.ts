import { create } from "zustand";
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
}));