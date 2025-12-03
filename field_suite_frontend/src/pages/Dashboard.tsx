import { useQuery } from '@tanstack/react-query'
import { fetchDashboard, fetchRegions } from '../api/client'
import StatsCard from '../components/StatsCard'
import NDVIChart from '../components/NDVIChart'
import AlertsList from '../components/AlertsList'

export default function Dashboard() {
  const { data: dashboard, isLoading: dashboardLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
  })

  const { data: regions } = useQuery({
    queryKey: ['regions'],
    queryFn: fetchRegions,
  })

  if (dashboardLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-500 border-t-transparent"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">لوحة التحكم</h1>
          <p className="text-gray-500">نظرة عامة على القطاع الزراعي في اليمن</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-secondary">
            📥 تصدير التقرير
          </button>
          <button className="btn btn-primary">
            ➕ إضافة حقل جديد
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="إجمالي المزارعين"
          value={dashboard?.summary?.total_farmers?.toLocaleString() || '0'}
          icon="👨‍🌾"
          trend="+12%"
          trendUp={true}
        />
        <StatsCard
          title="إجمالي الحقول"
          value={dashboard?.summary?.total_fields?.toLocaleString() || '0'}
          icon="🌾"
          trend="+8%"
          trendUp={true}
        />
        <StatsCard
          title="المساحة الكلية"
          value={`${(dashboard?.summary?.total_area_ha / 1000).toFixed(0) || '0'} ألف هكتار`}
          icon="📐"
          trend="+5%"
          trendUp={true}
        />
        <StatsCard
          title="المحافظات النشطة"
          value={dashboard?.summary?.active_regions || '20'}
          icon="🗺️"
          trend="ثابت"
          trendUp={null}
        />
      </div>

      {/* NDVI Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card">
          <h3 className="text-lg font-bold text-gray-800 mb-4">حالة NDVI للمحاصيل</h3>
          <NDVIChart data={dashboard?.ndvi_status} />
        </div>

        <div className="card">
          <h3 className="text-lg font-bold text-gray-800 mb-4">توزيع حالة المحاصيل</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                <span>ممتاز</span>
              </div>
              <span className="font-bold text-green-600">{dashboard?.ndvi_status?.excellent || 0}%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-emerald-400 rounded-full"></span>
                <span>جيد</span>
              </div>
              <span className="font-bold text-emerald-600">{dashboard?.ndvi_status?.good || 0}%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-yellow-400 rounded-full"></span>
                <span>متوسط</span>
              </div>
              <span className="font-bold text-yellow-600">{dashboard?.ndvi_status?.moderate || 0}%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-red-400 rounded-full"></span>
                <span>يحتاج متابعة</span>
              </div>
              <span className="font-bold text-red-600">{dashboard?.ndvi_status?.poor || 0}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts and Weather */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-bold text-gray-800 mb-4">التنبيهات</h3>
          <AlertsList alerts={dashboard?.alerts} />
        </div>

        <div className="card">
          <h3 className="text-lg font-bold text-gray-800 mb-4">الطقس اليوم</h3>
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <span className="text-6xl mb-4 block">☀️</span>
              <p className="text-4xl font-bold text-gray-800">
                {dashboard?.weather?.avg_temp_celsius || 28}°C
              </p>
              <p className="text-gray-500 mt-2">
                احتمالية الأمطار: {dashboard?.weather?.rain_probability || 0}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Regions Overview */}
      <div className="card">
        <h3 className="text-lg font-bold text-gray-800 mb-4">المحافظات اليمنية</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {regions?.regions?.slice(0, 10).map((region: any) => (
            <div
              key={region.id}
              className="p-4 bg-gray-50 rounded-lg hover:bg-emerald-50 transition-colors cursor-pointer"
            >
              <p className="font-bold text-gray-800">{region.name_ar}</p>
              <p className="text-sm text-gray-500">{region.name_en}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
