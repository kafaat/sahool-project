import { Outlet, NavLink } from 'react-router-dom'
import { useState } from 'react'

const navigation = [
  { name: 'لوحة التحكم', href: '/', icon: '📊' },
  { name: 'الحقول', href: '/fields', icon: '🌾' },
  { name: 'الطقس', href: '/weather', icon: '🌤️' },
  { name: 'المستشار الزراعي', href: '/advisor', icon: '🤖' },
  { name: 'المحافظات', href: '/regions', icon: '🗺️' },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside
        className={`fixed top-0 right-0 h-full bg-emerald-700 text-white transition-all duration-300 z-50 ${
          sidebarOpen ? 'w-64' : 'w-20'
        }`}
      >
        {/* Logo */}
        <div className="flex items-center justify-between p-4 border-b border-emerald-600">
          <div className={`flex items-center gap-3 ${!sidebarOpen && 'justify-center'}`}>
            <span className="text-2xl">🌱</span>
            {sidebarOpen && (
              <div>
                <h1 className="font-bold text-lg">سهول اليمن</h1>
                <p className="text-xs text-emerald-200">Field Suite v6.0</p>
              </div>
            )}
          </div>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-emerald-600 rounded-lg"
          >
            {sidebarOpen ? '→' : '←'}
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {navigation.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center gap-3 p-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-emerald-600 text-white'
                    : 'text-emerald-100 hover:bg-emerald-600/50'
                } ${!sidebarOpen && 'justify-center'}`
              }
            >
              <span className="text-xl">{item.icon}</span>
              {sidebarOpen && <span>{item.name}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        {sidebarOpen && (
          <div className="absolute bottom-4 right-4 left-4 p-4 bg-emerald-600/50 rounded-lg">
            <p className="text-xs text-emerald-200 text-center">
              المنصة الزراعية الذكية لليمن
              <br />
              <span className="text-emerald-300">© 2024</span>
            </p>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main
        className={`transition-all duration-300 ${
          sidebarOpen ? 'mr-64' : 'mr-20'
        }`}
      >
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
          <div className="px-6 py-4 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-800">مرحباً بك في سهول اليمن</h2>
              <p className="text-sm text-gray-500">نظام إدارة الحقول الزراعية</p>
            </div>
            <div className="flex items-center gap-4">
              <button className="p-2 hover:bg-gray-100 rounded-full">
                🔔
              </button>
              <button className="p-2 hover:bg-gray-100 rounded-full">
                ⚙️
              </button>
              <div className="flex items-center gap-2 bg-emerald-50 px-3 py-2 rounded-lg">
                <span className="w-8 h-8 bg-emerald-600 text-white rounded-full flex items-center justify-center text-sm">
                  م
                </span>
                <span className="text-sm font-medium text-emerald-700">مدير النظام</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
