/**
 * Loading States and Skeleton Components for Sahool Yemen
 * سهول اليمن - حالات التحميل
 *
 * Provides consistent loading UI across the application.
 */
import React from 'react'
import clsx from 'clsx'

interface SkeletonProps {
  className?: string
  animate?: boolean
  style?: React.CSSProperties
}

/**
 * Base skeleton component
 */
export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  animate = true,
  style,
}) => {
  return (
    <div
      className={clsx(
        'bg-gray-200 rounded',
        animate && 'animate-pulse',
        className
      )}
      style={style}
    />
  )
}

/**
 * Card skeleton for dashboard cards
 */
export const CardSkeleton: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-3">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-8 w-8 rounded-full" />
      </div>
      <Skeleton className="h-8 w-24 mb-2" />
      <Skeleton className="h-3 w-32" />
    </div>
  )
}

/**
 * Stats card skeleton
 */
export const StatsCardSkeleton: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-12 w-12 rounded-lg" />
        <div className="flex-1">
          <Skeleton className="h-4 w-24 mb-2" />
          <Skeleton className="h-6 w-16" />
        </div>
      </div>
    </div>
  )
}

/**
 * Table skeleton
 */
export const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 4,
}) => {
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Header */}
      <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
        <div className="flex gap-4">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
        </div>
      </div>

      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={rowIndex}
          className="border-b border-gray-100 px-4 py-3 last:border-0"
        >
          <div className="flex gap-4">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton
                key={colIndex}
                className="h-4 flex-1"
                style={{ animationDelay: `${(rowIndex * 0.1 + colIndex * 0.05)}s` }}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

/**
 * Chart skeleton
 */
export const ChartSkeleton: React.FC<{ height?: number }> = ({ height = 300 }) => {
  return (
    <div
      className="bg-white rounded-lg shadow p-4"
      style={{ height }}
    >
      <Skeleton className="h-5 w-32 mb-4" />
      <div className="flex items-end justify-between h-full pb-8 gap-2">
        {Array.from({ length: 7 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1 rounded-t"
            style={{
              height: `${30 + Math.random() * 60}%`,
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
      </div>
    </div>
  )
}

/**
 * Map skeleton
 */
export const MapSkeleton: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="relative h-96 bg-gray-100">
        <Skeleton className="absolute inset-0" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 mx-auto mb-2 border-4 border-gray-300 border-t-green-500 rounded-full animate-spin" />
            <p className="text-gray-500 text-sm">جاري تحميل الخريطة...</p>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * List skeleton
 */
export const ListSkeleton: React.FC<{ items?: number }> = ({ items = 5 }) => {
  return (
    <div className="space-y-3">
      {Array.from({ length: items }).map((_, i) => (
        <div
          key={i}
          className="bg-white rounded-lg shadow p-4 flex items-center gap-4"
        >
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="flex-1">
            <Skeleton className="h-4 w-3/4 mb-2" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-8 w-16 rounded" />
        </div>
      ))}
    </div>
  )
}

/**
 * Dashboard skeleton - full page
 */
export const DashboardSkeleton: React.FC = () => {
  return (
    <div className="p-6 space-y-6" dir="rtl">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <StatsCardSkeleton key={i} />
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartSkeleton height={300} />
        <ChartSkeleton height={300} />
      </div>

      {/* Table */}
      <TableSkeleton rows={5} columns={5} />
    </div>
  )
}

/**
 * Full page loading spinner
 */
export const PageLoader: React.FC<{ message?: string }> = ({
  message = 'جاري التحميل...',
}) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="w-16 h-16 mx-auto mb-4 border-4 border-gray-200 border-t-green-500 rounded-full animate-spin" />
        <p className="text-gray-600 font-medium">{message}</p>
      </div>
    </div>
  )
}

/**
 * Inline loader for buttons and small areas
 */
export const InlineLoader: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({
  size = 'md',
}) => {
  const sizes = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-3',
  }

  return (
    <div
      className={clsx(
        sizes[size],
        'border-gray-200 border-t-current rounded-full animate-spin'
      )}
    />
  )
}

/**
 * Empty state component
 */
export const EmptyState: React.FC<{
  title: string
  description?: string
  icon?: React.ReactNode
  action?: React.ReactNode
}> = ({ title, description, icon, action }) => {
  return (
    <div className="text-center py-12 px-4">
      {icon && (
        <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center text-gray-400">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-medium text-gray-900 mb-1">{title}</h3>
      {description && (
        <p className="text-gray-500 mb-4 max-w-sm mx-auto">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

/**
 * Error state component
 */
export const ErrorState: React.FC<{
  title?: string
  message?: string
  onRetry?: () => void
}> = ({
  title = 'حدث خطأ',
  message = 'لم نتمكن من تحميل البيانات. يرجى المحاولة مرة أخرى.',
  onRetry,
}) => {
  return (
    <div className="text-center py-12 px-4" dir="rtl">
      <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
        <svg
          className="w-8 h-8 text-red-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">{title}</h3>
      <p className="text-gray-500 mb-4 max-w-sm mx-auto">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          حاول مرة أخرى
        </button>
      )}
    </div>
  )
}

/**
 * Offline indicator
 */
export const OfflineIndicator: React.FC = () => {
  const [isOnline, setIsOnline] = React.useState(navigator.onLine)

  React.useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  if (isOnline) return null

  return (
    <div className="fixed bottom-4 right-4 bg-yellow-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 z-50">
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
        />
      </svg>
      <span>لا يوجد اتصال بالإنترنت</span>
    </div>
  )
}
