import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../state/auth'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: Record<string, unknown>) => void
          renderButton: (element: HTMLElement, config: Record<string, unknown>) => void
          prompt: (callback?: (notification: unknown) => void) => void
        }
      }
    }
  }
}

interface GoogleCredentialResponse {
  credential: string
  select_by: string
}

function getIdTokenFromHash(): string | null {
  const hash = window.location.hash
  if (!hash) return null
  const params = new URLSearchParams(hash.substring(1))
  return params.get('id_token')
}

function clearHash() {
  window.history.replaceState({}, '', window.location.pathname)
}

export function LoginPage() {
  const { token, user, setAuth, fetchMe } = useAuth()
  const navigate = useNavigate()
  const googleBtnRef = useRef<HTMLDivElement>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const initRef = useRef(false)

  useEffect(() => {
    if (token && user) {
      navigate('/', { replace: true })
    }
  }, [token, user, navigate])

  // Handle redirect callback — Google returns id_token in URL fragment
  useEffect(() => {
    const idToken = getIdTokenFromHash()
    if (idToken) {
      clearHash()
      setLoading(true)
      exchangeCredential(idToken)
    }
  }, [])

  // Initialize Google button
  useEffect(() => {
    if (user || initRef.current) return
    if (!CLIENT_ID) {
      setError('Google OAuth not configured')
      return
    }

    let cancelled = false
    let attempts = 0

    const tryInit = () => {
      if (cancelled) return
      if (!window.google?.accounts?.id) {
        attempts++
        if (attempts < 50) setTimeout(tryInit, 200)
        return
      }
      initRef.current = true
      window.google.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: handleCredentialResponse,
        auto_select: false,
      })
      if (googleBtnRef.current) {
        window.google.accounts.id.renderButton(googleBtnRef.current, {
          theme: 'outline',
          size: 'large',
          width: 300,
        })
      }
    }

    tryInit()
    return () => { cancelled = true }
  }, [user])

  const exchangeCredential = async (credential: string) => {
    setError('')
    try {
      const resp = await fetch(`${API}/api/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential }),
      })
      const data = await resp.json()
      if (!resp.ok) {
        setError(data.detail || 'Login failed')
        setLoading(false)
        return
      }
      setAuth(data.access_token, data.user)
      await fetchMe()
      navigate('/', { replace: true })
    } catch (err) {
      setError(`Network error: ${err}`)
      setLoading(false)
    }
  }

  const handleCredentialResponse = async (response: GoogleCredentialResponse) => {
    await exchangeCredential(response.credential)
  }

  if (token && user) return null

  return (
    <div className="page">
      <div className="login-container">
        <div className="login-card">
          <div className="login-brand">
            <span style={{ fontSize: 32, fontWeight: 700 }}>
              Arch<span style={{ color: '#4338ca' }}>Atlas</span>
            </span>
          </div>
          <h2 className="login-title">System Design Learning Platform</h2>
          <p className="login-subtitle">
            Sign in to track your progress, save architectures, and access AI-powered features.
          </p>

          <div className="login-divider" />

          <div className="login-tier-info">
            <div className="tier-card">
              <div className="tier-badge free">Free</div>
              <p>100 AI requests/day &middot; 10s cooldown</p>
            </div>
            <div className="tier-card">
              <div className="tier-badge premium">Premium</div>
              <p>Unlimited AI requests &middot; No cooldown</p>
            </div>
          </div>

          <div className="login-divider" />

          <div className="google-btn-wrapper">
            <div ref={googleBtnRef} />
            {loading && (
              <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13 }}>
                Signing in...
              </p>
            )}
          </div>

          {error && <div className="login-error">{error}</div>}

          <p className="login-footer-text">
            By signing in, you agree to our terms of service.
          </p>
        </div>
      </div>
    </div>
  )
}
