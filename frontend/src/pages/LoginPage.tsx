import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../state/auth'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: Record<string, unknown>) => void
          renderButton: (element: HTMLElement, config: Record<string, unknown>) => void
          prompt: () => void
        }
      }
    }
  }
}

interface GoogleCredentialResponse {
  credential: string
  select_by: string
}

export function LoginPage() {
  const { token, user, setAuth, fetchMe } = useAuth()
  const navigate = useNavigate()
  const googleBtnRef = useRef<HTMLDivElement>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (token && user) {
      navigate('/', { replace: true })
    }
  }, [token, user, navigate])

  useEffect(() => {
    if (user) return

    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    if (!clientId) {
      setError('Google OAuth not configured. Set VITE_GOOGLE_CLIENT_ID in .env')
      return
    }

    const initGoogle = () => {
      if (!window.google) {
        // Retry after a short delay (script loading)
        const timer = setTimeout(initGoogle, 200)
        return () => clearTimeout(timer)
      }

      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: handleCredentialResponse,
      })

      if (googleBtnRef.current) {
        window.google.accounts.id.renderButton(googleBtnRef.current, {
          theme: 'outline',
          size: 'large',
          width: 300,
          text: 'signin_with',
        })
      }
    }

    initGoogle()
  }, [user])

  const handleCredentialResponse = async (response: GoogleCredentialResponse) => {
    setError('')
    try {
      const resp = await fetch(`${API}/api/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: response.credential }),
      })
      if (!resp.ok) {
        const data = await resp.json()
        setError(data.detail || 'Login failed')
        return
      }
      const data = await resp.json()
      setAuth(data.access_token, data.user)
      await fetchMe()
      navigate('/', { replace: true })
    } catch (err) {
      setError(`Network error: ${err}`)
    }
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
            {!import.meta.env.VITE_GOOGLE_CLIENT_ID && (
              <p className="login-hint">Google OAuth not configured yet</p>
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
