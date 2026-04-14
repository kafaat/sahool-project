import { useState } from 'react'

const regions = [
  { id: 1, name: 'صنعاء' },
  { id: 2, name: 'عدن' },
  { id: 3, name: 'تعز' },
  { id: 4, name: 'حضرموت' },
  { id: 5, name: 'الحديدة' },
]

const forecast = [
  { day: 'اليوم', temp: 28, icon: '☀️', rain: 0 },
  { day: 'غداً', temp: 30, icon: '🌤️', rain: 10 },
  { day: 'الأربعاء', temp: 27, icon: '⛅', rain: 30 },
  { day: 'الخميس', temp: 25, icon: '🌧️', rain: 60 },
  { day: 'الجمعة', temp: 26, icon: '🌤️', rain: 20 },
  { day: 'السبت', temp: 29, icon: '☀️', rain: 5 },
  { day: 'الأحد', temp: 31, icon: '☀️', rain: 0 },
]

export default function Weather() {
  const [selectedRegion, setSelectedRegion] = useState(regions[0])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">الطقس والمناخ</h1>
          <p className="text-gray-500">بيانات الطقس والتنبؤات للمحافظات اليمنية</p>
        </div>
        <select
          className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          value={selectedRegion.id}
          onChange={(e) => setSelectedRegion(regions.find(r => r.id === Number(e.target.value)) || regions[0])}
        >
          {regions.map(region => (
            <option key={region.id} value={region.id}>{region.name}</option>
          ))}
        </select>
      </div>

      {/* Current Weather */}
      <div className="card bg-gradient-to-br from-emerald-500 to-emerald-700 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-emerald-100 mb-2">الطقس الآن في {selectedRegion.name}</p>
            <p className="text-6xl font-bold mb-4">28°C</p>
            <p className="text-emerald-100">صحو مع ارتفاع في درجات الحرارة</p>
          </div>
          <div className="text-center">
            <span className="text-8xl">☀️</span>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mt-8 pt-6 border-t border-emerald-400/30">
          <div className="text-center">
            <p className="text-emerald-100 text-sm">الرطوبة</p>
            <p className="text-2xl font-bold">45%</p>
          </div>
          <div className="text-center">
            <p className="text-emerald-100 text-sm">الرياح</p>
            <p className="text-2xl font-bold">12 كم/س</p>
          </div>
          <div className="text-center">
            <p className="text-emerald-100 text-sm">الضغط</p>
            <p className="text-2xl font-bold">1015 hPa</p>
          </div>
          <div className="text-center">
            <p className="text-emerald-100 text-sm">الأشعة فوق البنفسجية</p>
            <p className="text-2xl font-bold">8</p>
          </div>
        </div>
      </div>

      {/* 7-Day Forecast */}
      <div className="card">
        <h3 className="text-lg font-bold text-gray-800 mb-4">توقعات الأسبوع</h3>
        <div className="grid grid-cols-7 gap-4">
          {forecast.map((day, index) => (
            <div
              key={index}
              className={`text-center p-4 rounded-xl ${
                index === 0 ? 'bg-emerald-50 border-2 border-emerald-500' : 'bg-gray-50'
              }`}
            >
              <p className="text-sm font-medium text-gray-600 mb-2">{day.day}</p>
              <span className="text-4xl block mb-2">{day.icon}</span>
              <p className="text-xl font-bold text-gray-800">{day.temp}°</p>
              <p className="text-xs text-gray-500 mt-1">
                💧 {day.rain}%
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Agricultural Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-bold text-gray-800 mb-4">تنبيهات زراعية</h3>
          <div className="space-y-4">
            <div className="flex items-start gap-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <span className="text-2xl">⚠️</span>
              <div>
                <p className="font-medium text-yellow-800">موجة حرارة متوقعة</p>
                <p className="text-sm text-yellow-600">
                  يُنصح بزيادة الري خلال الأيام الثلاثة القادمة
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <span className="text-2xl">💧</span>
              <div>
                <p className="font-medium text-blue-800">احتمالية أمطار</p>
                <p className="text-sm text-blue-600">
                  أمطار خفيفة متوقعة يوم الخميس
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-bold text-gray-800 mb-4">توصيات الري</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🌾</span>
                <div>
                  <p className="font-medium">القمح</p>
                  <p className="text-sm text-gray-500">المساحة: 1,200 هكتار</p>
                </div>
              </div>
              <div className="text-left">
                <p className="font-bold text-emerald-600">20 مم</p>
                <p className="text-xs text-gray-500">كل 3 أيام</p>
              </div>
            </div>
            <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🍅</span>
                <div>
                  <p className="font-medium">الطماطم</p>
                  <p className="text-sm text-gray-500">المساحة: 450 هكتار</p>
                </div>
              </div>
              <div className="text-left">
                <p className="font-bold text-emerald-600">30 مم</p>
                <p className="text-xs text-gray-500">كل يومين</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
