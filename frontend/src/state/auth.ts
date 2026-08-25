import { create } from 'zustand'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface AuthUser {
  id: string
  email: string
  name: string
  picture: string
  tier: string
  rate_limit: {
    tier: string
    daily_limit: number
    used_today: number
    remaining: number
    cooldown_seconds: number
  }
}

interface AuthState {
  token: string | null
  user: AuthUser | null
  loading: boolean
  setAuth: (token: string, user: AuthUser) => void
  logout: () => void
  fetchMe: () => Promise<void>
  refreshRateLimit: () => Promise<void>
  getHeaders: () => Record<string, string>
}

export const useAuth = create<AuthState>((set, get) => ({
  token: localStorage.getItem('archatlas_token'),
  user: null,
  loading: true,

  setAuth: (token: string, user: AuthUser) => {
    localStorage.setItem('archatlas_token', token)
    set({ token, user })
  },

  logout: () => {
    localStorage.removeItem('archatlas_token')
    set({ token: null, user: null })
  },

  fetchMe: async () => {
    const { token } = get()
    if (!token) {
      set({ loading: false })
      return
    }
    try {
      const resp = await fetch(`${API}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (resp.ok) {
        const user = await resp.json()
        set({ user, loading: false })
      } else {
        get().logout()
        set({ loading: false })
      }
    } catch {
      set({ loading: false })
    }
  },

  refreshRateLimit: async () => {
    const { token } = get()
    if (!token) return
    try {
      const resp = await fetch(`${API}/api/auth/rate-limit`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (resp.ok) {
        const user = get().user
        if (user) {
          set({ user: { ...user, rate_limit: await resp.json() } })
        }
      }
    } catch {
      // ignore
    }
  },

  getHeaders: () => {
    const { token } = get()
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    return headers
  },
}))
