/**
 * سهول اليمن - Weather Store
 * إدارة بيانات الطقس والتنبؤات
 */
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export interface WeatherData {
  regionId: number
  regionName: string
  current: {
    temperature: number
    humidity: number
    windSpeed: number
    windDirection: string
    pressure: number
    uvIndex: number
    visibility: number
    description: string
    icon: string
  }
  forecast: DayForecast[]
  alerts: WeatherAlert[]
  lastUpdated: string
}

export interface DayForecast {
  date: string
  tempMin: number
  tempMax: number
  humidity: number
  precipitation: number
  precipProbability: number
  windSpeed: number
  description: string
  icon: string
}

export interface WeatherAlert {
  id: string
  type: 'heat' | 'cold' | 'rain' | 'wind' | 'dust' | 'flood'
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  titleAr: string
  description: string
  descriptionAr: string
  startTime: string
  endTime: string
  affectedRegions: number[]
}

export interface AgriculturalConditions {
  regionId: number
  plantingConditions: 'excellent' | 'good' | 'fair' | 'poor'
  irrigationNeeded: boolean
  irrigationAmount: number // mm
  sprayingWindow: boolean
  harvestConditions: 'excellent' | 'good' | 'fair' | 'poor'
  frostRisk: boolean
  heatStressRisk: boolean
  recommendations: string[]
  recommendationsAr: string[]
}

interface WeatherState {
  weatherData: Record<number, WeatherData>
  selectedRegion: number | null
  alerts: WeatherAlert[]
  agriculturalConditions: Record<number, AgriculturalConditions>
  isLoading: boolean
  error: string | null

  // Actions
  setWeatherData: (regionId: number, data: WeatherData) => void
  setMultipleWeatherData: (data: Record<number, WeatherData>) => void
  selectRegion: (regionId: number | null) => void
  setAlerts: (alerts: WeatherAlert[]) => void
  addAlert: (alert: WeatherAlert) => void
  dismissAlert: (alertId: string) => void
  setAgriculturalConditions: (regionId: number, conditions: AgriculturalConditions) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearWeatherData: () => void
}

export const useWeatherStore = create<WeatherState>()(
  devtools(
    (set) => ({
      weatherData: {},
      selectedRegion: null,
      alerts: [],
      agriculturalConditions: {},
      isLoading: false,
      error: null,

      setWeatherData: (regionId, data) => set((state) => ({
        weatherData: { ...state.weatherData, [regionId]: data },
      })),

      setMultipleWeatherData: (data) => set((state) => ({
        weatherData: { ...state.weatherData, ...data },
      })),

      selectRegion: (regionId) => set({ selectedRegion: regionId }),

      setAlerts: (alerts) => set({ alerts }),

      addAlert: (alert) => set((state) => ({
        alerts: [...state.alerts, alert],
      })),

      dismissAlert: (alertId) => set((state) => ({
        alerts: state.alerts.filter((a) => a.id !== alertId),
      })),

      setAgriculturalConditions: (regionId, conditions) => set((state) => ({
        agriculturalConditions: {
          ...state.agriculturalConditions,
          [regionId]: conditions
        },
      })),

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      clearWeatherData: () => set({
        weatherData: {},
        alerts: [],
        agriculturalConditions: {}
      }),
    }),
    { name: 'WeatherStore' }
  )
)

// Selectors
export const selectCurrentWeather = (state: WeatherState): WeatherData | null => {
  if (state.selectedRegion === null) return null
  return state.weatherData[state.selectedRegion] || null
}

export const selectActiveAlerts = (state: WeatherState): WeatherAlert[] => {
  const now = new Date()
  return state.alerts.filter((alert) => {
    const endTime = new Date(alert.endTime)
    return endTime > now
  })
}

export const selectCriticalAlerts = (state: WeatherState): WeatherAlert[] => {
  return state.alerts.filter((a) => a.severity === 'critical' || a.severity === 'high')
}

export const selectRegionConditions = (
  state: WeatherState,
  regionId: number
): AgriculturalConditions | null => {
  return state.agriculturalConditions[regionId] || null
}

// Helper functions
export const getAlertColor = (severity: WeatherAlert['severity']): string => {
  switch (severity) {
    case 'critical': return 'red'
    case 'high': return 'orange'
    case 'medium': return 'yellow'
    case 'low': return 'blue'
    default: return 'gray'
  }
}

export const getConditionColor = (
  condition: AgriculturalConditions['plantingConditions']
): string => {
  switch (condition) {
    case 'excellent': return 'green'
    case 'good': return 'blue'
    case 'fair': return 'yellow'
    case 'poor': return 'red'
    default: return 'gray'
  }
}
