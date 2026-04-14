import type { FieldBoundary } from '../shared/models/field_boundary';

const API_BASE = 'http://localhost:8000';

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
}

export interface FieldListResponse {
  fields: FieldBoundary[];
  count: number;
}

export interface AutoDetectResponse {
  fields: FieldBoundary[];
  count: number;
}

export interface ZonesResponse {
  fields: FieldBoundary[];
  count: number;
}

class FieldApiService {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
        },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          data: null,
          error: errorData.detail || `HTTP Error: ${response.status}`,
        };
      }

      if (response.status === 204) {
        return { data: null, error: null };
      }

      const data = await response.json();
      return { data, error: null };
    } catch (err) {
      return {
        data: null,
        error: err instanceof Error ? err.message : 'Network error',
      };
    }
  }

  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.request('/');
  }

  async listFields(): Promise<ApiResponse<FieldListResponse>> {
    return this.request('/fields/');
  }

  async getField(id: string): Promise<ApiResponse<FieldBoundary>> {
    return this.request(`/fields/${id}`);
  }

  async createField(field: Omit<FieldBoundary, 'id'>): Promise<ApiResponse<FieldBoundary>> {
    return this.request('/fields/', {
      method: 'POST',
      body: JSON.stringify(field),
    });
  }

  async updateField(id: string, field: FieldBoundary): Promise<ApiResponse<FieldBoundary>> {
    return this.request(`/fields/${id}`, {
      method: 'PUT',
      body: JSON.stringify(field),
    });
  }

  async deleteField(id: string): Promise<ApiResponse<null>> {
    return this.request(`/fields/${id}`, {
      method: 'DELETE',
    });
  }

  async autoDetect(mock: boolean = true): Promise<ApiResponse<AutoDetectResponse>> {
    return this.request('/fields/auto-detect', {
      method: 'POST',
      body: JSON.stringify({ mock }),
    });
  }

  async splitIntoZones(
    field: FieldBoundary,
    zones: number = 3
  ): Promise<ApiResponse<ZonesResponse>> {
    return this.request('/fields/zones', {
      method: 'POST',
      body: JSON.stringify({ field, zones }),
    });
  }
}

export const fieldApi = new FieldApiService();
