/**
 * Authentication Store
 * متجر المصادقة
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'farmer' | 'agronomist' | 'viewer'
  tenant_id: string
  region_id?: number
}

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  login: (token: string, refreshToken: string, user: User) => void
  logout: () => void
  setUser: (user: User) => void
  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: (token, refreshToken, user) => {
        localStorage.setItem('token', token)
        set({
          token,
          refreshToken,
          user,
          isAuthenticated: true,
          error: null,
        })
      },

      logout: () => {
        localStorage.removeItem('token')
        set({
          token: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        })
      },

      setUser: (user) => set({ user }),

      setError: (error) => set({ error }),

      setLoading: (isLoading) => set({ isLoading }),

      clearError: () => set({ error: null }),
    }),
    {
      name: 'sahool-auth',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

export default useAuthStore
