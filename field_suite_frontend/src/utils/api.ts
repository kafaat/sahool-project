/**
 * API Utilities for Sahool Yemen
 * سهول اليمن - أدوات واجهة برمجة التطبيقات
 *
 * Enhanced API handling with retry, caching, and error management.
 */

// =============================================================================
// Types
// =============================================================================

interface RetryConfig {
  maxRetries: number
  baseDelay: number
  maxDelay: number
}

interface CacheConfig {
  enabled: boolean
  ttl: number // milliseconds
}

interface ApiOptions {
  retry?: Partial<RetryConfig>
  cache?: Partial<CacheConfig>
  timeout?: number
}

interface ApiError extends Error {
  status?: number
  code?: string
  details?: any
}

// =============================================================================
// Default Configuration
// =============================================================================

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 10000,
}

const DEFAULT_CACHE_CONFIG: CacheConfig = {
  enabled: true,
  ttl: 5 * 60 * 1000, // 5 minutes
}

// =============================================================================
// Cache Implementation
// =============================================================================

interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

class SimpleCache {
  private cache: Map<string, CacheEntry<any>> = new Map()
  private maxSize = 100

  get<T>(key: string): T | null {
    const entry = this.cache.get(key)
    if (!entry) return null

    const isExpired = Date.now() - entry.timestamp > entry.ttl
    if (isExpired) {
      this.cache.delete(key)
      return null
    }

    return entry.data
  }

  set<T>(key: string, data: T, ttl: number): void {
    // Evict old entries if cache is full
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value
      if (oldestKey) this.cache.delete(oldestKey)
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    })
  }

  delete(key: string): void {
    this.cache.delete(key)
  }

  clear(): void {
    this.cache.clear()
  }

  invalidate(pattern: string): void {
    const regex = new RegExp(pattern.replace('*', '.*'))
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key)
      }
    }
  }
}

export const apiCache = new SimpleCache()

// =============================================================================
// Retry Logic
// =============================================================================

async function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function calculateDelay(attempt: number, config: RetryConfig): number {
  const exponentialDelay = config.baseDelay * Math.pow(2, attempt)
  const jitter = Math.random() * 0.3 * exponentialDelay
  return Math.min(exponentialDelay + jitter, config.maxDelay)
}

function shouldRetry(error: any, attempt: number, maxRetries: number): boolean {
  if (attempt >= maxRetries) return false

  // Don't retry client errors (4xx) except for rate limiting (429)
  if (error.status && error.status >= 400 && error.status < 500 && error.status !== 429) {
    return false
  }

  // Retry network errors, server errors, and rate limiting
  return true
}

// =============================================================================
// Error Handling
// =============================================================================

export function createApiError(
  message: string,
  status?: number,
  code?: string,
  details?: any
): ApiError {
  const error = new Error(message) as ApiError
  error.status = status
  error.code = code
  error.details = details
  return error
}

export function getErrorMessage(error: any): string {
  // Arabic error messages
  const errorMessages: Record<number, string> = {
    400: 'طلب غير صالح',
    401: 'غير مصرح',
    403: 'الوصول مرفوض',
    404: 'غير موجود',
    408: 'انتهت مهلة الطلب',
    429: 'طلبات كثيرة جداً، يرجى المحاولة لاحقاً',
    500: 'خطأ في الخادم',
    502: 'خطأ في البوابة',
    503: 'الخدمة غير متاحة',
    504: 'انتهت مهلة البوابة',
  }

  if (error.status && errorMessages[error.status]) {
    return errorMessages[error.status]
  }

  if (error.message === 'Network Error' || !navigator.onLine) {
    return 'لا يوجد اتصال بالإنترنت'
  }

  if (error.message === 'timeout') {
    return 'انتهت مهلة الاتصال'
  }

  return error.message || 'حدث خطأ غير متوقع'
}

// =============================================================================
// API Request Wrapper
// =============================================================================

export async function apiRequest<T>(
  fetchFn: () => Promise<Response>,
  options: ApiOptions = {}
): Promise<T> {
  const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...options.retry }
  // Cache config reserved for future use
  const _cacheConfig = { ...DEFAULT_CACHE_CONFIG, ...options.cache }
  void _cacheConfig // Suppress unused variable warning

  let lastError: any

  for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
    try {
      // Add timeout if specified
      const controller = new AbortController()
      let timeoutId: ReturnType<typeof setTimeout> | undefined

      if (options.timeout) {
        timeoutId = setTimeout(() => controller.abort(), options.timeout)
      }

      try {
        const response = await fetchFn()

        if (timeoutId) clearTimeout(timeoutId)

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw createApiError(
            errorData.message || errorData.error || `HTTP ${response.status}`,
            response.status,
            errorData.code,
            errorData.details
          )
        }

        return await response.json()
      } finally {
        if (timeoutId) clearTimeout(timeoutId)
      }
    } catch (error: any) {
      lastError = error

      if (!shouldRetry(error, attempt, retryConfig.maxRetries)) {
        throw error
      }

      // Wait before retry
      const delayMs = calculateDelay(attempt, retryConfig)
      console.log(`Retry ${attempt + 1}/${retryConfig.maxRetries} after ${delayMs}ms`)
      await delay(delayMs)
    }
  }

  throw lastError
}

// =============================================================================
// Cached API Request
// =============================================================================

export async function cachedApiRequest<T>(
  cacheKey: string,
  fetchFn: () => Promise<Response>,
  options: ApiOptions = {}
): Promise<T> {
  const cacheConfig = { ...DEFAULT_CACHE_CONFIG, ...options.cache }

  // Check cache first
  if (cacheConfig.enabled) {
    const cached = apiCache.get<T>(cacheKey)
    if (cached !== null) {
      return cached
    }
  }

  // Fetch data
  const data = await apiRequest<T>(fetchFn, options)

  // Cache the result
  if (cacheConfig.enabled) {
    apiCache.set(cacheKey, data, cacheConfig.ttl)
  }

  return data
}

// =============================================================================
// Request Queue (for rate limiting)
// =============================================================================

class RequestQueue {
  private queue: Array<() => Promise<any>> = []
  private processing = false
  private minInterval = 100 // Minimum ms between requests

  async add<T>(request: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await request()
          resolve(result)
        } catch (error) {
          reject(error)
        }
      })

      this.processQueue()
    })
  }

  private async processQueue(): Promise<void> {
    if (this.processing || this.queue.length === 0) return

    this.processing = true

    while (this.queue.length > 0) {
      const request = this.queue.shift()
      if (request) {
        await request()
        await delay(this.minInterval)
      }
    }

    this.processing = false
  }
}

export const requestQueue = new RequestQueue()

// =============================================================================
// Batch Requests
// =============================================================================

export async function batchRequests<T>(
  requests: Array<() => Promise<T>>,
  batchSize = 5
): Promise<Array<T | Error>> {
  const results: Array<T | Error> = []

  for (let i = 0; i < requests.length; i += batchSize) {
    const batch = requests.slice(i, i + batchSize)
    const batchResults = await Promise.allSettled(batch.map((fn) => fn()))

    for (const result of batchResults) {
      if (result.status === 'fulfilled') {
        results.push(result.value)
      } else {
        results.push(result.reason)
      }
    }
  }

  return results
}

// =============================================================================
// Debounced Request
// =============================================================================

export function createDebouncedRequest<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  wait: number
): T {
  let timeoutId: ReturnType<typeof setTimeout> | undefined

  return ((...args: Parameters<T>) => {
    return new Promise((resolve, reject) => {
      if (timeoutId) {
        clearTimeout(timeoutId)
      }

      timeoutId = setTimeout(async () => {
        try {
          const result = await fn(...args)
          resolve(result)
        } catch (error) {
          reject(error)
        }
      }, wait)
    })
  }) as T
}

// =============================================================================
// Data Transformation Helpers
// =============================================================================

/**
 * Transform API response for Yemen regions
 */
export function transformRegionData(region: any) {
  return {
    id: region.id,
    nameAr: region.name_ar,
    nameEn: region.name_en,
    lat: region.lat,
    lon: region.lon,
    center: [region.lat, region.lon] as [number, number],
  }
}

/**
 * Transform weather data
 */
export function transformWeatherData(weather: any) {
  return {
    temperature: weather.temperature,
    humidity: weather.humidity,
    windSpeed: weather.wind_speed,
    conditions: weather.conditions,
    icon: getWeatherIcon(weather.conditions),
  }
}

function getWeatherIcon(conditions: string): string {
  const icons: Record<string, string> = {
    sunny: '☀️',
    cloudy: '☁️',
    rainy: '🌧️',
    partly_cloudy: '⛅',
    hot: '🌡️',
    windy: '💨',
  }
  return icons[conditions] || '🌤️'
}

/**
 * Transform NDVI data
 */
export function transformNDVIData(ndvi: any) {
  const status = getNDVIStatus(ndvi.ndvi_mean || ndvi.value)
  return {
    value: ndvi.ndvi_mean || ndvi.value,
    min: ndvi.ndvi_min,
    max: ndvi.ndvi_max,
    status: status.label,
    statusColor: status.color,
    date: ndvi.date || ndvi.timestamp,
  }
}

function getNDVIStatus(value: number): { label: string; color: string } {
  if (value > 0.6) return { label: 'ممتاز', color: 'green' }
  if (value > 0.4) return { label: 'جيد', color: 'lime' }
  if (value > 0.25) return { label: 'متوسط', color: 'yellow' }
  return { label: 'يحتاج متابعة', color: 'red' }
}

// =============================================================================
// Format Helpers
// =============================================================================

/**
 * Format number in Arabic locale
 */
export function formatNumber(value: number, locale = 'ar-YE'): string {
  return new Intl.NumberFormat(locale).format(value)
}

/**
 * Format date in Arabic locale
 */
export function formatDate(date: string | Date, locale = 'ar-YE'): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(d)
}

/**
 * Format area in hectares
 */
export function formatArea(hectares: number): string {
  return `${formatNumber(hectares)} هكتار`
}

/**
 * Format currency in YER
 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('ar-YE', {
    style: 'currency',
    currency: 'YER',
  }).format(amount)
}
