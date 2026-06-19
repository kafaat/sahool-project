import axios from 'axios';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:9000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

// =============================================================================
// Types - متوافقة مع الخلفية
// =============================================================================

export interface FieldSummary {
  id: string;  // UUID from backend
  name_ar: string;
  name_en?: string;
  tenant_id: string;
  area_hectares: number;
  crop_type?: string;
  status: string;
  centroid?: { lat: number; lng: number };
  // Legacy compatibility
  name?: string;
  area_ha?: number;
  centroid_lat?: number;
  centroid_lon?: number;
}

export interface FieldHealthInsight {
  field_id: string;
  name_ar: string;
  latest_ndvi?: number;
  health_status: string;
  alert_count: number;
  // Computed for UI
  score?: number;
  label?: string;
}

export interface FieldAlert {
  id: string;
  title_ar: string;
  title_en?: string;
  message_ar: string;
  message_en?: string;
  severity: string;
  status: string;
  created_at: string;
  // Legacy compatibility
  title?: string;
  message?: string;
}

export interface FieldTimelinePoint {
  timestamp: string;
  ndvi?: number | null;
  eto?: number | null;
  rain_mm?: number | null;
}

export interface NDVITrendPoint {
  date: string;
  value: number;
  field_id?: string;
  field_name?: string;
}

// =============================================================================
// API Functions - متصلة بالخلفية
// =============================================================================

/**
 * Fetch all fields for a tenant
 * يستدعي: GET /api/v1/geo/fields
 */
export async function fetchFields(tenantId: number | string): Promise<FieldSummary[]> {
  try {
    const res = await api.get(`/api/v1/geo/fields`, {
      headers: { 'X-Tenant-ID': String(tenantId) },
    });

    const fields = res.data.fields ?? res.data.items ?? res.data ?? [];

    // Map to legacy format for UI compatibility
    return fields.map((f: any) => ({
      ...f,
      id: f.id || f.field_id,
      name: f.name_ar || f.name,
      area_ha: f.area_hectares || f.area_ha,
      centroid_lat: f.centroid?.lat || f.centroid_lat,
      centroid_lon: f.centroid?.lng || f.centroid_lon,
    }));
  } catch (error) {
    console.error('fetchFields error:', error);
    return [];
  }
}

/**
 * Fetch field health/analytics summary
 * يستدعي: GET /api/v1/analytics/fields/{fieldId}/summary
 */
export async function fetchFieldHealth(
  tenantId: number | string,
  fieldId: number | string,
): Promise<FieldHealthInsight | null> {
  try {
    const res = await api.get(
      `/api/v1/analytics/fields/${fieldId}/summary`,
      { headers: { 'X-Tenant-ID': String(tenantId) } },
    );

    const data = res.data;

    // Calculate score from NDVI for UI
    const ndvi = data.latest_ndvi ?? 0;
    let score = 0;
    let label = 'غير معروف';

    if (ndvi >= 0.6) {
      score = 90;
      label = 'ممتاز';
    } else if (ndvi >= 0.4) {
      score = 70;
      label = 'جيد';
    } else if (ndvi >= 0.2) {
      score = 50;
      label = 'متوسط';
    } else if (ndvi > 0) {
      score = 30;
      label = 'ضعيف';
    }

    return {
      ...data,
      score,
      label,
    };
  } catch (error) {
    console.error('fetchFieldHealth error:', error);
    return null;
  }
}

/**
 * Fetch alerts for a field
 * يستدعي: GET /api/v1/alerts/field/{fieldId}
 */
export async function fetchFieldAlerts(
  tenantId: number | string,
  fieldId: number | string,
): Promise<FieldAlert[]> {
  try {
    const res = await api.get(`/api/v1/alerts/field/${fieldId}`, {
      headers: { 'X-Tenant-ID': String(tenantId) },
    });

    const alerts = res.data.items ?? res.data ?? [];

    // Map to legacy format for UI
    return alerts.map((a: any) => ({
      ...a,
      title: a.title_ar || a.title,
      message: a.message_ar || a.message,
    }));
  } catch (error) {
    console.error('fetchFieldAlerts error:', error);
    return [];
  }
}

/**
 * Fetch NDVI timeline/trends for a field
 * يستدعي: GET /api/v1/analytics/ndvi-trends
 */
export async function fetchFieldTimeline(
  tenantId: number | string,
  fieldId: number | string,
): Promise<FieldTimelinePoint[]> {
  try {
    const res = await api.get(`/api/v1/analytics/ndvi-trends`, {
      params: { field_id: fieldId, days: 30 },
      headers: { 'X-Tenant-ID': String(tenantId) },
    });

    const dataPoints = res.data.data_points ?? res.data.timeline ?? [];

    // Map to timeline format
    return dataPoints.map((p: NDVITrendPoint) => ({
      timestamp: p.date,
      ndvi: p.value,
      eto: null,
      rain_mm: null,
    }));
  } catch (error) {
    console.error('fetchFieldTimeline error:', error);
    return [];
  }
}

// =============================================================================
// Agent/AI Functions
// =============================================================================

export interface AgentReply {
  reply: string;
  priority?: string;
  context?: any;
}

/**
 * Ask AI agent for field advice
 * يستدعي: POST /api/v1/analytics/insights (مؤقتاً حتى يتم إنشاء agent service)
 */
export async function askAgentFieldAdvice(params: {
  tenantId: number | string;
  fieldId: number | string;
  message: string;
}): Promise<AgentReply> {
  try {
    // Try agent service first
    const res = await api.post('/api/v1/agent/field-advice', {
      field_id: params.fieldId,
      message: params.message,
    }, {
      headers: { 'X-Tenant-ID': String(params.tenantId) },
    });
    return res.data;
  } catch {
    // Fallback: return insights as advice
    try {
      const insights = await api.get('/api/v1/analytics/insights', {
        params: { field_id: params.fieldId, limit: 3 },
        headers: { 'X-Tenant-ID': String(params.tenantId) },
      });

      const insightsList = insights.data.insights ?? [];
      if (insightsList.length > 0) {
        return {
          reply: insightsList.map((i: any) => `• ${i.title_ar}: ${i.description_ar}`).join('\n'),
          priority: 'medium',
        };
      }
    } catch {
      // Ignore
    }

    return {
      reply: 'عذراً، خدمة المساعد الذكي غير متاحة حالياً. يرجى المحاولة لاحقاً.',
      priority: 'low',
    };
  }
}

// =============================================================================
// Additional API Functions
// =============================================================================

/**
 * Fetch tenant overview analytics
 * يستدعي: GET /api/v1/analytics/overview
 */
export async function fetchTenantOverview(tenantId: number | string) {
  try {
    const res = await api.get('/api/v1/analytics/overview', {
      headers: { 'X-Tenant-ID': String(tenantId) },
    });
    return res.data;
  } catch (error) {
    console.error('fetchTenantOverview error:', error);
    return null;
  }
}

/**
 * Fetch management zones for a field
 * يستدعي: GET /api/v1/zones/field/{fieldId}
 */
export async function fetchFieldZones(
  tenantId: number | string,
  fieldId: number | string,
) {
  try {
    const res = await api.get(`/api/v1/zones/field/${fieldId}`, {
      headers: { 'X-Tenant-ID': String(tenantId) },
    });
    return res.data;
  } catch (error) {
    console.error('fetchFieldZones error:', error);
    return null;
  }
}

/**
 * Fetch weather data for a field
 * يستدعي: GET /api/v1/weather/field/{fieldId}
 */
export async function fetchFieldWeather(
  tenantId: number | string,
  fieldId: number | string,
) {
  try {
    const res = await api.get(`/api/v1/weather/fields/${fieldId}`, {
      headers: { 'X-Tenant-ID': String(tenantId) },
    });
    return res.data;
  } catch (error) {
    console.error('fetchFieldWeather error:', error);
    return null;
  }
}
