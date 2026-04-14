/**
 * سهول اليمن - Imagery Page
 * صفحة صور الأقمار الصناعية وتحليل NDVI
 */
import React, { useState, useEffect } from 'react'

interface SatelliteImage {
  id: string
  satellite: string
  date: string
  cloudCover: number
  resolution: number
  thumbnailUrl: string
  available: boolean
}

interface NDVIZone {
  zone: string
  color: string
  minValue: number
  maxValue: number
  areaHa: number
  percentage: number
  description: string
}

interface VegetationIndex {
  name: string
  nameAr: string
  value: number
  status: 'excellent' | 'good' | 'moderate' | 'poor'
  description: string
}

interface StressDetection {
  type: string
  typeAr: string
  severity: 'low' | 'medium' | 'high'
  affectedArea: number
  recommendation: string
}

const Imagery: React.FC = () => {
  const [selectedField, setSelectedField] = useState<string>('field-001')
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0])
  const [images, setImages] = useState<SatelliteImage[]>([])
  const [ndviZones, setNdviZones] = useState<NDVIZone[]>([])
  const [indices, setIndices] = useState<VegetationIndex[]>([])
  const [stressAreas, setStressAreas] = useState<StressDetection[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'indices' | 'stress'>('overview')

  useEffect(() => {
    loadImageryData()
  }, [selectedField, selectedDate])

  const loadImageryData = async () => {
    setIsLoading(true)
    // Simulated data
    setTimeout(() => {
      setImages([
        { id: '1', satellite: 'Sentinel-2A', date: '2024-12-01', cloudCover: 5, resolution: 10, thumbnailUrl: '', available: true },
        { id: '2', satellite: 'Sentinel-2B', date: '2024-11-26', cloudCover: 12, resolution: 10, thumbnailUrl: '', available: true },
        { id: '3', satellite: 'Landsat-8', date: '2024-11-20', cloudCover: 8, resolution: 30, thumbnailUrl: '', available: true },
        { id: '4', satellite: 'Landsat-9', date: '2024-11-15', cloudCover: 22, resolution: 30, thumbnailUrl: '', available: true },
      ])

      setNdviZones([
        { zone: 'A', color: '#1a9850', minValue: 0.7, maxValue: 1.0, areaHa: 8.5, percentage: 25, description: 'غطاء نباتي كثيف - ممتاز' },
        { zone: 'B', color: '#91cf60', minValue: 0.5, maxValue: 0.7, areaHa: 12.2, percentage: 36, description: 'غطاء نباتي جيد' },
        { zone: 'C', color: '#d9ef8b', minValue: 0.35, maxValue: 0.5, areaHa: 8.0, percentage: 24, description: 'غطاء نباتي متوسط' },
        { zone: 'D', color: '#fee08b', minValue: 0.2, maxValue: 0.35, areaHa: 3.8, percentage: 11, description: 'غطاء نباتي ضعيف' },
        { zone: 'E', color: '#d73027', minValue: 0, maxValue: 0.2, areaHa: 1.5, percentage: 4, description: 'تربة عارية / إجهاد شديد' },
      ])

      setIndices([
        { name: 'NDVI', nameAr: 'مؤشر الغطاء النباتي', value: 0.58, status: 'good', description: 'يقيس كثافة الغطاء النباتي الأخضر' },
        { name: 'EVI', nameAr: 'مؤشر النباتات المحسن', value: 0.52, status: 'good', description: 'أكثر حساسية في المناطق ذات الكثافة العالية' },
        { name: 'SAVI', nameAr: 'مؤشر النباتات المعدل للتربة', value: 0.45, status: 'moderate', description: 'يقلل تأثير التربة على القياسات' },
        { name: 'NDWI', nameAr: 'مؤشر المياه', value: 0.32, status: 'moderate', description: 'يقيس محتوى الماء في النباتات' },
        { name: 'MSAVI', nameAr: 'مؤشر النباتات المعدل', value: 0.48, status: 'good', description: 'تحسين لمؤشر SAVI' },
      ])

      setStressAreas([
        { type: 'water_stress', typeAr: 'إجهاد مائي', severity: 'medium', affectedArea: 2.5, recommendation: 'زيادة كمية الري بنسبة 20%' },
        { type: 'nutrient_deficiency', typeAr: 'نقص غذائي', severity: 'low', affectedArea: 1.2, recommendation: 'إضافة سماد نيتروجيني' },
      ])

      setIsLoading(false)
    }, 500)
  }

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      excellent: 'text-green-600 bg-green-100',
      good: 'text-blue-600 bg-blue-100',
      moderate: 'text-yellow-600 bg-yellow-100',
      poor: 'text-red-600 bg-red-100',
    }
    return colors[status] || 'text-gray-600 bg-gray-100'
  }

  const getStatusLabel = (status: string): string => {
    const labels: Record<string, string> = {
      excellent: 'ممتاز',
      good: 'جيد',
      moderate: 'متوسط',
      poor: 'ضعيف',
    }
    return labels[status] || status
  }

  const getSeverityColor = (severity: string): string => {
    const colors: Record<string, string> = {
      low: 'text-yellow-600 bg-yellow-100',
      medium: 'text-orange-600 bg-orange-100',
      high: 'text-red-600 bg-red-100',
    }
    return colors[severity] || 'text-gray-600 bg-gray-100'
  }

  const getSeverityLabel = (severity: string): string => {
    const labels: Record<string, string> = {
      low: 'منخفض',
      medium: 'متوسط',
      high: 'مرتفع',
    }
    return labels[severity] || severity
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
          <h1 className="text-2xl font-bold text-gray-900">صور الأقمار الصناعية</h1>
          <p className="text-gray-600">تحليل NDVI ومراقبة صحة المحاصيل</p>
        </div>
        <div className="flex gap-4">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
          <select
            value={selectedField}
            onChange={(e) => setSelectedField(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
          >
            <option value="field-001">حقل البركة 1</option>
            <option value="field-002">حقل الخير 2</option>
            <option value="field-003">حقل السلام 3</option>
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {[
          { id: 'overview', label: 'نظرة عامة' },
          { id: 'indices', label: 'المؤشرات النباتية' },
          { id: 'stress', label: 'كشف الإجهاد' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'text-green-600 border-b-2 border-green-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* NDVI Map Placeholder */}
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">خريطة NDVI</h2>
            </div>
            <div className="aspect-video bg-gradient-to-br from-green-200 via-yellow-200 to-red-200 flex items-center justify-center">
              <div className="text-center text-gray-600">
                <svg className="w-16 h-16 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
                <p>خريطة NDVI التفاعلية</p>
                <p className="text-sm">Sentinel-2A - {selectedDate}</p>
              </div>
            </div>
          </div>

          {/* NDVI Zones */}
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">مناطق NDVI</h2>
            <div className="space-y-3">
              {ndviZones.map((zone) => (
                <div key={zone.zone} className="flex items-center gap-3">
                  <div
                    className="w-6 h-6 rounded"
                    style={{ backgroundColor: zone.color }}
                  />
                  <div className="flex-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-700">{zone.description}</span>
                      <span className="text-gray-500">{zone.percentage}%</span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {zone.minValue.toFixed(2)} - {zone.maxValue.toFixed(2)} | {zone.areaHa} هـ
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Available Images */}
          <div className="lg:col-span-3 bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">الصور المتاحة</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {images.map((image) => (
                <div
                  key={image.id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-green-500 cursor-pointer transition-colors"
                >
                  <div className="aspect-video bg-gray-100 rounded mb-3 flex items-center justify-center">
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="text-sm">
                    <p className="font-medium text-gray-900">{image.satellite}</p>
                    <p className="text-gray-500">{image.date}</p>
                    <div className="flex justify-between mt-1 text-xs text-gray-500">
                      <span>غيوم: {image.cloudCover}%</span>
                      <span>{image.resolution}م</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'indices' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {indices.map((index) => (
            <div key={index.name} className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-semibold text-gray-900">{index.name}</h3>
                  <p className="text-sm text-gray-500">{index.nameAr}</p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(index.status)}`}>
                  {getStatusLabel(index.status)}
                </span>
              </div>
              <div className="text-3xl font-bold text-gray-900 mb-2">
                {index.value.toFixed(2)}
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${index.value * 100}%` }}
                />
              </div>
              <p className="text-sm text-gray-600">{index.description}</p>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'stress' && (
        <div className="space-y-4">
          {stressAreas.length === 0 ? (
            <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
              <svg className="w-16 h-16 mx-auto text-green-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-lg font-semibold text-green-800">لا يوجد إجهاد مكتشف</h3>
              <p className="text-green-600">الحقل في حالة صحية ممتازة</p>
            </div>
          ) : (
            stressAreas.map((stress, index) => (
              <div key={index} className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-semibold text-gray-900">{stress.typeAr}</h3>
                    <p className="text-sm text-gray-500">{stress.type}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(stress.severity)}`}>
                    {getSeverityLabel(stress.severity)}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-sm text-gray-500">المساحة المتأثرة</p>
                    <p className="text-lg font-semibold text-gray-900">{stress.affectedArea} هكتار</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-sm text-gray-500">النسبة</p>
                    <p className="text-lg font-semibold text-gray-900">{((stress.affectedArea / 34) * 100).toFixed(1)}%</p>
                  </div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm font-medium text-blue-800 mb-1">التوصية:</p>
                  <p className="text-blue-700">{stress.recommendation}</p>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default Imagery
