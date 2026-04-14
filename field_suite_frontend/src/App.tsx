import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Fields from './pages/Fields'
import Weather from './pages/Weather'
import Advisor from './pages/Advisor'
import Regions from './pages/Regions'
import Login from './pages/Login'
import Settings from './pages/Settings'
import Analytics from './pages/Analytics'
import Imagery from './pages/Imagery'
import ErrorBoundary from './components/ErrorBoundary'
import { useAuthStore } from './store/authStore'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
})

// Protected Route component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />

            {/* Protected routes */}
            <Route path="/" element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }>
              <Route index element={<Dashboard />} />
              <Route path="fields" element={<Fields />} />
              <Route path="weather" element={<Weather />} />
              <Route path="advisor" element={<Advisor />} />
              <Route path="regions" element={<Regions />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="imagery" element={<Imagery />} />
              <Route path="settings" element={<Settings />} />
            </Route>

            {/* Catch all - redirect to dashboard */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
