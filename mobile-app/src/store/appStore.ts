import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Field, User, Equipment, Alert } from "../types";

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
