/**
 * Login Page
 * صفحة تسجيل الدخول
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import api from '../api/client'

interface LoginForm {
  email: string
  password: string
}

export default function Login() {
  const navigate = useNavigate()
  const { login, setError, error, clearError } = useAuthStore()
  const [form, setForm] = useState<LoginForm>({ email: '', password: '' })

  const loginMutation = useMutation({
    mutationFn: async (data: LoginForm) => {
      const response = await api.post('/v1/auth/login', data)
      return response.data
    },
    onSuccess: (data) => {
      login(data.access_token, data.refresh_token, data.user)
      navigate('/')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'فشل تسجيل الدخول')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    loginMutation.mutate(form)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 to-emerald-100">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="text-5xl mb-4">🌾</div>
            <h1 className="text-2xl font-bold text-gray-800">سهول اليمن</h1>
            <p className="text-gray-500 mt-2">المنصة الزراعية الذكية</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-center">
              {error}
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-gray-700 text-sm font-medium mb-2">
                البريد الإلكتروني
              </label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                placeholder="example@email.com"
                required
                dir="ltr"
              />
            </div>

            <div>
              <label className="block text-gray-700 text-sm font-medium mb-2">
                كلمة المرور
              </label>
              <input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                placeholder="••••••••"
                required
                dir="ltr"
              />
            </div>

            <button
              type="submit"
              disabled={loginMutation.isPending}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loginMutation.isPending ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></span>
                  جاري التسجيل...
                </span>
              ) : (
                'تسجيل الدخول'
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-8 text-center text-sm text-gray-500">
            <p>ليس لديك حساب؟{' '}
              <a href="/register" className="text-emerald-600 hover:underline">
                إنشاء حساب جديد
              </a>
            </p>
          </div>

          {/* Demo credentials */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500 text-center mb-2">للتجربة:</p>
            <div className="text-xs text-gray-600 text-center" dir="ltr">
              <p>demo@sahool.ye / demo123</p>
            </div>
          </div>
        </div>

        {/* Copyright */}
        <p className="text-center text-gray-500 text-sm mt-6">
          &copy; 2024 سهول اليمن. جميع الحقوق محفوظة.
        </p>
      </div>
    </div>
  )
}
