import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Dashboard
export const fetchDashboard = async () => {
  const response = await api.get('/v1/dashboard')
  return response.data
}

// Regions
export const fetchRegions = async () => {
  const response = await api.get('/v1/regions')
  return response.data
}

// Crops
export const fetchCrops = async () => {
  const response = await api.get('/v1/crops')
  return response.data
}

// Fields
export const fetchFields = async (params?: {
  crop_type?: string
  region_id?: number
  page?: number
  page_size?: number
}) => {
  const response = await api.get('/v1/fields/search', { params })
  return response.data
}

export const fetchFieldDetails = async (fieldId: string) => {
  const response = await api.get(`/v1/fields/${fieldId}/details`)
  return response.data
}

export const fetchFieldSummary = async (fieldId: string) => {
  const response = await api.get(`/v1/fields/${fieldId}/summary`)
  return response.data
}

// NDVI
export const fetchNDVI = async (fieldId: number, targetDate?: string) => {
  const params = targetDate ? { target_date: targetDate } : {}
  const response = await api.get(`/v1/ndvi/${fieldId}`, { params })
  return response.data
}

export const fetchNDVIHistory = async (fieldId: number, months?: number) => {
  const params = months ? { months } : {}
  const response = await api.get(`/v1/ndvi/${fieldId}/history`, { params })
  return response.data
}

// Weather
export const fetchWeather = async (fieldId: number, targetDate?: string) => {
  const params = targetDate ? { target_date: targetDate } : {}
  const response = await api.get(`/v1/weather/fields/${fieldId}`, { params })
  return response.data
}

export const fetchWeatherForecast = async (fieldId: number, days?: number) => {
  const params = days ? { days } : {}
  const response = await api.get(`/v1/weather/fields/${fieldId}/forecast`, { params })
  return response.data
}

// Analytics
export const fetchNDVITimeline = async (fieldId: number, months?: number) => {
  const params = months ? { months } : {}
  const response = await api.get(`/v1/analytics/ndvi/${fieldId}/timeline`, { params })
  return response.data
}

export const fetchYieldPrediction = async (fieldId: number, cropType: string) => {
  const response = await api.get('/v1/analytics/yield-prediction', {
    params: { field_id: fieldId, crop_type: cropType }
  })
  return response.data
}

// Advisor
export const analyzeField = async (data: {
  field_id: number
  crop_type?: string
  ndvi_value?: number
}) => {
  const response = await api.post('/v1/advisor/analyze-field', data)
  return response.data
}

export const getIrrigationAdvice = async (fieldId: number, cropType?: string) => {
  const params = cropType ? { crop_type: cropType } : {}
  const response = await api.get(`/v1/advisor/irrigation/${fieldId}`, { params })
  return response.data
}

export const getPestAlerts = async (regionId?: number, cropType?: string) => {
  const params: any = {}
  if (regionId) params.region_id = regionId
  if (cropType) params.crop_type = cropType
  const response = await api.get('/v1/advisor/pest-alerts', { params })
  return response.data
}

export const askAdvisor = async (question: string) => {
  const response = await api.post('/v1/advisor/ask', { question })
  return response.data
}

// Geo
export const computeArea = async (geometry: any) => {
  const response = await api.post('/v1/geo/compute-area', geometry)
  return response.data
}

export const getElevation = async (lat: number, lon: number) => {
  const response = await api.get('/v1/geo/elevation', { params: { lat, lon } })
  return response.data
}

export default api
