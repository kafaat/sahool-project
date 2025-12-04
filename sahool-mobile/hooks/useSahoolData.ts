import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
}