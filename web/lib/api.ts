import axios from 'axios';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:9000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

export interface FieldSummary {
  id: number;
  name: string;
  tenant_id: number;
  area_ha?: number;
  centroid_lat?: number;
  centroid_lon?: number;
  bbox?: number[];
  centroid_geojson?: { type: string; coordinates: [number, number] };
}

export interface FieldHealthInsight {
  score: number;
  label: string;
  ndvi?: number;
  eto?: number;
  ph?: number;
  ec?: number;
}

export interface FieldAlert {
  id: number;
  title: string;
  message: string;
  severity: string;
  created_at: string;
}

export interface FieldTimelinePoint {
  timestamp: string;
  ndvi?: number | null;
  eto?: number | null;
  rain_mm?: number | null;
}

export async function fetchFields(tenantId: number): Promise<FieldSummary[]> {
  const res = await api.get(`/api/geo/fields`, {
    params: { tenant_id: tenantId },
  });
  return res.data.items ?? res.data ?? [];
}

export async function fetchFieldHealth(
  tenantId: number,
  fieldId: number,
): Promise<FieldHealthInsight> {
  const res = await api.get(
    `/api/analytics/field/${fieldId}/health`,
    { params: { tenant_id: tenantId } },
  );
  return res.data;
}

export async function fetchFieldAlerts(
  tenantId: number,
  fieldId: number,
): Promise<FieldAlert[]> {
  const res = await api.get(`/api/alerts/field/${fieldId}`, {
    params: { tenant_id: tenantId },
  });
  return res.data.items ?? res.data ?? [];
}

export async function fetchFieldTimeline(
  tenantId: number,
  fieldId: number,
): Promise<FieldTimelinePoint[]> {
  try {
    const res = await api.get(`/api/timeline/api/v1/timeline/field/${fieldId}`, {
      params: { tenant_id: tenantId },
    });
    return res.data.timeline ?? res.data ?? [];
  } catch {
    return [];
  }
}


export interface AgentReply {
  reply: string;
  priority?: string;
  context?: any;
}

export async function askAgentFieldAdvice(params: {
  tenantId: number;
  fieldId: number;
  message: string;
}): Promise<AgentReply> {
  const res = await api.post('/api/agent/api/v1/agent/field-advice', {
    tenant_id: params.tenantId,
    field_id: params.fieldId,
    message: params.message,
  });
  return res.data;
}
