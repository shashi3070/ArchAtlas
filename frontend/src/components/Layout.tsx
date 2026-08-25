import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../state/auth'

const LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/learn', label: 'Learn' },
  { to: '/lab', label: 'Lab' },
  { to: '/challenges', label: 'Challenges' },
  { to: '/interview', label: 'Interview' },
  { to: '/glossary', label: 'Glossary' },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="app-shell">
      <nav className="topbar">
        <NavLink to="/" className="brand-link">
          <span className="brand">Arch<span className="brand-accent">Atlas</span></span>
        </NavLink>
        <div className="nav-links">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              {l.label}
            </NavLink>
          ))}
        </div>

        <div className="topbar-spacer" />

        {user ? (
          <div className="user-menu-wrapper">
            <button
              className="user-avatar-btn"
              onClick={() => setMenuOpen(!menuOpen)}
            >
              {user.picture ? (
                <img src={user.picture} alt="" className="user-avatar-img" />
              ) : (
                <span className="user-avatar-placeholder">
                  {user.name?.[0]?.toUpperCase() || user.email[0]?.toUpperCase()}
                </span>
              )}
              <span className="user-name">{user.name || user.email}</span>
            </button>

            {menuOpen && (
              <div className="user-dropdown">
                <div className="user-dropdown-header">
                  <strong>{user.name}</strong>
                  <span className="user-email">{user.email}</span>
                  <span className={`user-tier-badge ${user.tier}`}>
                    {user.tier}
                  </span>
                </div>
                {user.rate_limit && (
                  <div className="user-dropdown-rate">
                    <span>API: {user.rate_limit.used_today}/{user.rate_limit.daily_limit} used</span>
                    {user.rate_limit.cooldown_seconds > 0 && (
                      <span> &middot; Cooldown: {user.rate_limit.cooldown_seconds}s</span>
                    )}
                  </div>
                )}
                <div className="user-dropdown-divider" />
                <button
                  className="user-dropdown-logout"
                  onClick={() => { logout(); setMenuOpen(false) }}
                >
                  Sign out
                </button>
              </div>
            )}
          </div>
        ) : (
          <NavLink to="/login" className="nav-link login-nav-link">
            Sign in
          </NavLink>
        )}
      </nav>
      {children}
    </div>
  )
}
