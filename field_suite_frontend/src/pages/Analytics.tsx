/**
 * سهول اليمن - Analytics Page
 * صفحة التحليلات والإحصاءات
 */
import React, { useState, useEffect } from 'react'

interface DashboardStats {
  totalFields: number
  totalArea: number
  totalFarmers: number
  avgNdvi: number
  healthDistribution: {
    excellent: number
    good: number
    moderate: number
    needsAttention: number
    critical: number
  }
}

interface RegionStats {
  regionId: number
  regionName: string
  fieldsCount: number
  totalArea: number
  avgNdvi: number
  topCrop: string
}

interface CropStats {
  cropName: string
  fieldsCount: number
  totalArea: number
  avgYield: number
}

interface TrendData {
  date: string
  value: number
}

const Analytics: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [regionStats, setRegionStats] = useState<RegionStats[]>([])
  const [cropStats, setCropStats] = useState<CropStats[]>([])
  const [ndviTrend, setNdviTrend] = useState<TrendData[]>([])
  const [selectedPeriod, setSelectedPeriod] = useState<'week' | 'month' | 'year'>('month')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadAnalyticsData()
  }, [selectedPeriod])

  const loadAnalyticsData = async () => {
    setIsLoading(true)
    // Simulated data - in production, fetch from API
    setTimeout(() => {
      setStats({
        totalFields: 45230,
        totalArea: 125000,
        totalFarmers: 18500,
        avgNdvi: 0.52,
        healthDistribution: {
          excellent: 22,
          good: 35,
          moderate: 25,
          needsAttention: 13,
          critical: 5,
        },
      })

      setRegionStats([
        { regionId: 1, regionName: 'صنعاء', fieldsCount: 5200, totalArea: 15000, avgNdvi: 0.55, topCrop: 'قمح' },
        { regionId: 5, regionName: 'الحديدة', fieldsCount: 8100, totalArea: 28000, avgNdvi: 0.48, topCrop: 'ذرة' },
        { regionId: 3, regionName: 'تعز', fieldsCount: 6300, totalArea: 18500, avgNdvi: 0.58, topCrop: 'بن' },
        { regionId: 6, regionName: 'إب', fieldsCount: 5800, totalArea: 16200, avgNdvi: 0.61, topCrop: 'خضروات' },
        { regionId: 4, regionName: 'حضرموت', fieldsCount: 4200, totalArea: 12800, avgNdvi: 0.42, topCrop: 'نخيل' },
      ])

      setCropStats([
        { cropName: 'قمح', fieldsCount: 12500, totalArea: 35000, avgYield: 2.8 },
        { cropName: 'ذرة', fieldsCount: 9800, totalArea: 28000, avgYield: 3.5 },
        { cropName: 'بن', fieldsCount: 6200, totalArea: 15000, avgYield: 1.2 },
        { cropName: 'خضروات', fieldsCount: 8500, totalArea: 22000, avgYield: 15.0 },
        { cropName: 'أعلاف', fieldsCount: 5100, totalArea: 18000, avgYield: 8.5 },
      ])

      // Generate trend data
      const trend: TrendData[] = []
      const days = selectedPeriod === 'week' ? 7 : selectedPeriod === 'month' ? 30 : 365
      for (let i = days; i >= 0; i--) {
        const date = new Date()
        date.setDate(date.getDate() - i)
        trend.push({
          date: date.toISOString().split('T')[0],
          value: 0.45 + Math.random() * 0.2,
        })
      }
      setNdviTrend(trend)

      setIsLoading(false)
    }, 500)
  }

  const getHealthColor = (status: string): string => {
    const colors: Record<string, string> = {
      excellent: 'bg-green-500',
      good: 'bg-blue-500',
      moderate: 'bg-yellow-500',
      needsAttention: 'bg-orange-500',
      critical: 'bg-red-500',
    }
    return colors[status] || 'bg-gray-500'
  }

  const getHealthLabel = (status: string): string => {
    const labels: Record<string, string> = {
      excellent: 'ممتاز',
      good: 'جيد',
      moderate: 'متوسط',
      needsAttention: 'يحتاج متابعة',
      critical: 'حرج',
    }
    return labels[status] || status
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6" dir="rtl">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">التحليلات والإحصاءات</h1>
          <p className="text-gray-600">نظرة شاملة على الأداء الزراعي</p>
        </div>
        <div className="flex gap-2">
          {(['week', 'month', 'year'] as const).map((period) => (
            <button
              key={period}
              onClick={() => setSelectedPeriod(period)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedPeriod === period
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {period === 'week' ? 'أسبوع' : period === 'month' ? 'شهر' : 'سنة'}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">إجمالي الحقول</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalFields.toLocaleString()}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">إجمالي المساحة</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalArea.toLocaleString()} <span className="text-sm font-normal">هكتار</span></p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">عدد المزارعين</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalFarmers.toLocaleString()}</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">متوسط NDVI</p>
                <p className="text-2xl font-bold text-gray-900">{stats.avgNdvi.toFixed(2)}</p>
              </div>
              <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Health Distribution */}
      {stats && (
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">توزيع الحالة الصحية للحقول</h2>
          <div className="flex gap-4 items-center">
            <div className="flex-1 h-8 bg-gray-100 rounded-full overflow-hidden flex">
              {Object.entries(stats.healthDistribution).map(([status, percentage]) => (
                <div
                  key={status}
                  className={`h-full ${getHealthColor(status)} transition-all`}
                  style={{ width: `${percentage}%` }}
                  title={`${getHealthLabel(status)}: ${percentage}%`}
                />
              ))}
            </div>
          </div>
          <div className="flex flex-wrap gap-4 mt-4">
            {Object.entries(stats.healthDistribution).map(([status, percentage]) => (
              <div key={status} className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${getHealthColor(status)}`} />
                <span className="text-sm text-gray-600">{getHealthLabel(status)}: {percentage}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Regions */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">أفضل المحافظات</h2>
          <div className="space-y-4">
            {regionStats.map((region, index) => (
              <div key={region.regionId} className="flex items-center gap-4">
                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-700 font-bold text-sm">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-900">{region.regionName}</span>
                    <span className="text-sm text-gray-500">{region.fieldsCount.toLocaleString()} حقل</span>
                  </div>
                  <div className="flex justify-between items-center text-sm text-gray-500">
                    <span>{region.totalArea.toLocaleString()} هكتار</span>
                    <span>NDVI: {region.avgNdvi.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Crops */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">أهم المحاصيل</h2>
          <div className="space-y-4">
            {cropStats.map((crop, index) => (
              <div key={crop.cropName} className="flex items-center gap-4">
                <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center text-amber-700 font-bold text-sm">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-900">{crop.cropName}</span>
                    <span className="text-sm text-gray-500">{crop.fieldsCount.toLocaleString()} حقل</span>
                  </div>
                  <div className="flex justify-between items-center text-sm text-gray-500">
                    <span>{crop.totalArea.toLocaleString()} هكتار</span>
                    <span>الإنتاجية: {crop.avgYield} طن/هـ</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* NDVI Trend Chart Placeholder */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">اتجاه مؤشر NDVI</h2>
        <div className="h-64 flex items-end gap-1">
          {ndviTrend.slice(-30).map((point, index) => (
            <div
              key={index}
              className="flex-1 bg-green-500 rounded-t opacity-70 hover:opacity-100 transition-opacity"
              style={{ height: `${(point.value / 0.8) * 100}%` }}
              title={`${point.date}: ${point.value.toFixed(3)}`}
            />
          ))}
        </div>
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          <span>{ndviTrend[0]?.date}</span>
          <span>{ndviTrend[ndviTrend.length - 1]?.date}</span>
        </div>
      </div>
    </div>
  )
}

export default Analytics
