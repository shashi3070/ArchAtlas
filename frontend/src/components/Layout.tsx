import { NavLink } from 'react-router-dom'

const LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/learn', label: 'Learn' },
  { to: '/lab', label: 'Lab' },
  { to: '/challenges', label: 'Challenges' },
  { to: '/interview', label: 'Interview' },
  { to: '/glossary', label: 'Glossary' },
]

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <nav className="topbar">
        <span className="brand">Arch<span className="brand-accent">Atlas</span></span>
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
      </nav>
      {children}
    </div>
  )
}
