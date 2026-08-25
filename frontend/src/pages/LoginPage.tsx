import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../state/auth'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

export function LoginPage() {
  const { token, user, setAuth, fetchMe } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (token && user) {
      navigate('/', { replace: true })
    }
  }, [token, user, navigate])

  // Handle redirect callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const credential = params.get('credential')
    if (credential) {
      setLoading(true)
      handleCredentialResponse(credential)
      // Clean URL
      window.history.replaceState({}, '', '/login')
    }
  }, [])

  const handleCredentialResponse = async (credential: string) => {
    setError('')
    setLoading(true)
    try {
      const resp = await fetch(`${API}/api/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential }),
      })
      if (!resp.ok) {
        const data = await resp.json()
        setError(data.detail || 'Login failed')
        setLoading(false)
        return
      }
      const data = await resp.json()
      setAuth(data.access_token, data.user)
      await fetchMe()
      navigate('/', { replace: true })
    } catch (err) {
      setError(`Network error: ${err}`)
      setLoading(false)
    }
  }

  const handleGoogleLogin = () => {
    if (!CLIENT_ID) {
      setError('Google OAuth not configured')
      return
    }
    setLoading(true)
    // Build Google OAuth URL for redirect flow
    const redirectUri = `${window.location.origin}/login`
    const scope = 'email profile openid'
    const url = `https://accounts.google.com/o/oauth2/v2/auth?` +
      `client_id=${CLIENT_ID}` +
      `&redirect_uri=${encodeURIComponent(redirectUri)}` +
      `&response_type=id_token` +
      `&scope=${encodeURIComponent(scope)}` +
      `&nonce=${crypto.randomUUID()}` +
      `&prompt=select_account`
    window.location.href = url
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
            <button
              className="google-signin-btn"
              onClick={handleGoogleLogin}
              disabled={loading}
            >
              <svg width="18" height="18" viewBox="0 0 48 48" style={{ marginRight: 10 }}>
                <path fill="#FFC107" d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 12.955 4 4 12.955 4 24s8.955 20 20 20 20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z"/>
                <path fill="#FF3D00" d="M6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 16.318 4 9.656 8.337 6.306 14.691z"/>
                <path fill="#4CAF50" d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238A11.91 11.91 0 0124 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z"/>
                <path fill="#1976D2" d="M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 01-4.087 5.571l.003-.002 6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z"/>
              </svg>
              {loading ? 'Signing in...' : 'Sign in with Google'}
            </button>
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
