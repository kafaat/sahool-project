import { useQuery, useMutation, UseQueryOptions } from "@tanstack/react-query";
import { api } from "../lib/api/client";
import { useAppStore } from "../store/appStore";
import { Field, WeatherData, NDVIEntry, Alert, Zone } from "../types";

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

export function useZones(fieldId: string) {
  return useSahoolQuery<Zone[]>(
    ["zones", fieldId],
    () => api.getManagementZones(fieldId),
    { enabled: !!fieldId }
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
