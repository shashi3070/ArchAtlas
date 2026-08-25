import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../state/auth'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, loading, fetchMe } = useAuth()

  useEffect(() => {
    fetchMe()
  }, [fetchMe])

  if (loading) {
    return (
      <div className="page" style={{ textAlign: 'center', paddingTop: 80 }}>
        <p style={{ color: '#64748b' }}>Loading...</p>
      </div>
    )
  }

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
