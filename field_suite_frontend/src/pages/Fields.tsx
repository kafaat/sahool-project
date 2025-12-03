import { useState } from 'react'

const mockFields = [
  { id: 1, name: 'حقل الخير', crop: 'قمح', area: 12.5, region: 'صنعاء', ndvi: 0.72, status: 'ممتاز' },
  { id: 2, name: 'حقل البركة', crop: 'ذرة', area: 8.3, region: 'تعز', ndvi: 0.58, status: 'جيد' },
  { id: 3, name: 'حقل السلام', crop: 'طماطم', area: 5.0, region: 'إب', ndvi: 0.45, status: 'متوسط' },
  { id: 4, name: 'حقل النور', crop: 'بن', area: 15.2, region: 'حضرموت', ndvi: 0.65, status: 'جيد' },
  { id: 5, name: 'حقل الأمل', crop: 'بصل', area: 3.8, region: 'الحديدة', ndvi: 0.32, status: 'يحتاج متابعة' },
]

export default function Fields() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCrop, setSelectedCrop] = useState('')

  const filteredFields = mockFields.filter(field => {
    const matchesSearch = field.name.includes(searchTerm) || field.region.includes(searchTerm)
    const matchesCrop = !selectedCrop || field.crop === selectedCrop
    return matchesSearch && matchesCrop
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ممتاز': return 'bg-green-100 text-green-700'
      case 'جيد': return 'bg-emerald-100 text-emerald-700'
      case 'متوسط': return 'bg-yellow-100 text-yellow-700'
      case 'يحتاج متابعة': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">إدارة الحقول</h1>
          <p className="text-gray-500">عرض وإدارة جميع الحقول الزراعية</p>
        </div>
        <button className="btn btn-primary">
          ➕ إضافة حقل جديد
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="🔍 البحث عن حقل..."
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <select
            className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            value={selectedCrop}
            onChange={(e) => setSelectedCrop(e.target.value)}
          >
            <option value="">جميع المحاصيل</option>
            <option value="قمح">قمح</option>
            <option value="ذرة">ذرة</option>
            <option value="طماطم">طماطم</option>
            <option value="بن">بن</option>
            <option value="بصل">بصل</option>
          </select>
        </div>
      </div>

      {/* Fields Table */}
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-right text-sm font-bold text-gray-700">اسم الحقل</th>
              <th className="px-6 py-3 text-right text-sm font-bold text-gray-700">المحصول</th>
              <th className="px-6 py-3 text-right text-sm font-bold text-gray-700">المساحة (هكتار)</th>
              <th className="px-6 py-3 text-right text-sm font-bold text-gray-700">المحافظة</th>
              <th className="px-6 py-3 text-right text-sm font-bold text-gray-700">NDVI</th>
              <th className="px-6 py-3 text-right text-sm font-bold text-gray-700">الحالة</th>
              <th className="px-6 py-3 text-right text-sm font-bold text-gray-700">إجراءات</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filteredFields.map((field) => (
              <tr key={field.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <span className="w-10 h-10 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center text-xl">
                      🌾
                    </span>
                    <span className="font-medium text-gray-800">{field.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-600">{field.crop}</td>
                <td className="px-6 py-4 text-gray-600">{field.area}</td>
                <td className="px-6 py-4 text-gray-600">{field.region}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{ width: `${field.ndvi * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600">{field.ndvi}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`badge ${getStatusColor(field.status)}`}>
                    {field.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex gap-2">
                    <button className="p-2 hover:bg-gray-100 rounded-lg" title="عرض">
                      👁️
                    </button>
                    <button className="p-2 hover:bg-gray-100 rounded-lg" title="تعديل">
                      ✏️
                    </button>
                    <button className="p-2 hover:bg-gray-100 rounded-lg" title="تحليل">
                      📊
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          عرض {filteredFields.length} من {mockFields.length} حقل
        </p>
        <div className="flex gap-2">
          <button className="btn btn-secondary">السابق</button>
          <button className="btn btn-primary">التالي</button>
        </div>
      </div>
    </div>
  )
}
