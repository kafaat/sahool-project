import { useQuery } from '@tanstack/react-query'
import { fetchRegions } from '../api/client'

export default function Regions() {
  const { data, isLoading } = useQuery({
    queryKey: ['regions'],
    queryFn: fetchRegions,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-500 border-t-transparent"></div>
      </div>
    )
  }

  const regions = data?.regions || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">المحافظات اليمنية</h1>
          <p className="text-gray-500">نظرة عامة على جميع المحافظات الـ 20</p>
        </div>
      </div>

      {/* Map Placeholder */}
      <div className="card bg-gradient-to-br from-emerald-50 to-cyan-50 h-64 flex items-center justify-center">
        <div className="text-center">
          <span className="text-6xl mb-4 block">🗺️</span>
          <p className="text-gray-600">خريطة تفاعلية للمحافظات اليمنية</p>
          <p className="text-sm text-gray-400">(قريباً)</p>
        </div>
      </div>

      {/* Regions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {regions.map((region: any) => (
          <div
            key={region.id}
            className="card card-hover cursor-pointer group"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-bold text-lg text-gray-800 group-hover:text-emerald-600 transition-colors">
                  {region.name_ar}
                </h3>
                <p className="text-sm text-gray-500">{region.name_en}</p>
              </div>
              <span className="text-2xl opacity-50 group-hover:opacity-100 transition-opacity">
                📍
              </span>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">الإحداثيات:</span>
                <span className="text-gray-700">
                  {region.lat?.toFixed(2)}°N, {region.lon?.toFixed(2)}°E
                </span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-100">
              <button className="w-full btn btn-secondary text-sm group-hover:bg-emerald-50 group-hover:text-emerald-600">
                عرض التفاصيل ←
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card text-center">
          <span className="text-4xl mb-2 block">🏛️</span>
          <p className="text-3xl font-bold text-emerald-600">20</p>
          <p className="text-gray-500">محافظة</p>
        </div>
        <div className="card text-center">
          <span className="text-4xl mb-2 block">📐</span>
          <p className="text-3xl font-bold text-emerald-600">527,968</p>
          <p className="text-gray-500">كم² المساحة الكلية</p>
        </div>
        <div className="card text-center">
          <span className="text-4xl mb-2 block">🌱</span>
          <p className="text-3xl font-bold text-emerald-600">1.6M</p>
          <p className="text-gray-500">هكتار زراعي</p>
        </div>
      </div>
    </div>
  )
}
