/**
 * سهول اليمن - Fields Store
 * إدارة حالة الحقول الزراعية
 */
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

export interface Field {
  id: string
  name: string
  nameAr: string
  area: number
  cropType: string
  regionId: number
  regionName: string
  districtName: string
  coordinates: {
    lat: number
    lng: number
  }
  ndviValue: number
  healthStatus: 'excellent' | 'good' | 'moderate' | 'needs_attention' | 'critical'
  irrigationType: string
  soilType: string
  lastUpdated: string
}

export interface FieldFilters {
  search: string
  regionId: number | null
  cropType: string | null
  healthStatus: string | null
  minArea: number | null
  maxArea: number | null
}

interface FieldsState {
  fields: Field[]
  selectedField: Field | null
  filters: FieldFilters
  isLoading: boolean
  error: string | null
  pagination: {
    page: number
    pageSize: number
    total: number
  }

  // Actions
  setFields: (fields: Field[]) => void
  addField: (field: Field) => void
  updateField: (id: string, updates: Partial<Field>) => void
  removeField: (id: string) => void
  selectField: (field: Field | null) => void
  setFilters: (filters: Partial<FieldFilters>) => void
  resetFilters: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setPagination: (pagination: Partial<FieldsState['pagination']>) => void
}

const initialFilters: FieldFilters = {
  search: '',
  regionId: null,
  cropType: null,
  healthStatus: null,
  minArea: null,
  maxArea: null,
}

export const useFieldsStore = create<FieldsState>()(
  devtools(
    persist(
      (set) => ({
        fields: [],
        selectedField: null,
        filters: initialFilters,
        isLoading: false,
        error: null,
        pagination: {
          page: 1,
          pageSize: 20,
          total: 0,
        },

        setFields: (fields) => set({ fields }),

        addField: (field) => set((state) => ({
          fields: [...state.fields, field]
        })),

        updateField: (id, updates) => set((state) => ({
          fields: state.fields.map((f) =>
            f.id === id ? { ...f, ...updates } : f
          ),
        })),

        removeField: (id) => set((state) => ({
          fields: state.fields.filter((f) => f.id !== id),
        })),

        selectField: (field) => set({ selectedField: field }),

        setFilters: (filters) => set((state) => ({
          filters: { ...state.filters, ...filters },
        })),

        resetFilters: () => set({ filters: initialFilters }),

        setLoading: (isLoading) => set({ isLoading }),

        setError: (error) => set({ error }),

        setPagination: (pagination) => set((state) => ({
          pagination: { ...state.pagination, ...pagination },
        })),
      }),
      {
        name: 'sahool-fields-store',
        partialize: (state) => ({
          filters: state.filters,
          pagination: { pageSize: state.pagination.pageSize },
        }),
      }
    ),
    { name: 'FieldsStore' }
  )
)

// Selectors
export const selectFilteredFields = (state: FieldsState): Field[] => {
  let filtered = state.fields

  if (state.filters.search) {
    const search = state.filters.search.toLowerCase()
    filtered = filtered.filter(
      (f) =>
        f.name.toLowerCase().includes(search) ||
        f.nameAr.includes(state.filters.search) ||
        f.cropType.includes(state.filters.search)
    )
  }

  if (state.filters.regionId) {
    filtered = filtered.filter((f) => f.regionId === state.filters.regionId)
  }

  if (state.filters.cropType) {
    filtered = filtered.filter((f) => f.cropType === state.filters.cropType)
  }

  if (state.filters.healthStatus) {
    filtered = filtered.filter((f) => f.healthStatus === state.filters.healthStatus)
  }

  if (state.filters.minArea !== null) {
    filtered = filtered.filter((f) => f.area >= state.filters.minArea!)
  }

  if (state.filters.maxArea !== null) {
    filtered = filtered.filter((f) => f.area <= state.filters.maxArea!)
  }

  return filtered
}

export const selectFieldsByRegion = (state: FieldsState, regionId: number): Field[] => {
  return state.fields.filter((f) => f.regionId === regionId)
}

export const selectFieldStats = (state: FieldsState) => {
  const fields = state.fields
  return {
    total: fields.length,
    totalArea: fields.reduce((sum, f) => sum + f.area, 0),
    avgNdvi: fields.length > 0
      ? fields.reduce((sum, f) => sum + f.ndviValue, 0) / fields.length
      : 0,
    byHealth: {
      excellent: fields.filter((f) => f.healthStatus === 'excellent').length,
      good: fields.filter((f) => f.healthStatus === 'good').length,
      moderate: fields.filter((f) => f.healthStatus === 'moderate').length,
      needsAttention: fields.filter((f) => f.healthStatus === 'needs_attention').length,
      critical: fields.filter((f) => f.healthStatus === 'critical').length,
    },
  }
}
