import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Grid2x2,
  Network,
  TrendingUp,
  FileText,
} from 'lucide-react'

const links = [
  { to: '/overview', label: 'Overview', icon: LayoutDashboard },
  { to: '/heatmap', label: 'Skill Heatmap', icon: Grid2x2 },
  { to: '/clusters', label: 'Role Clusters', icon: Network },
  { to: '/trends', label: 'Skill Trends', icon: TrendingUp },
  { to: '/resume', label: 'Resume Analyzer', icon: FileText },
]

export default function Nav() {
  const location = useLocation()

  return (
    <nav
      style={{
        position: 'fixed',
        top: 16,
        left: 16,
        bottom: 16,
        width: 224,
        background: '#111111',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 12,
        display: 'flex',
        flexDirection: 'column',
        padding: '20px 12px',
        zIndex: 50,
      }}
      aria-label="Main navigation"
    >
      <div style={{ padding: '4px 8px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 6,
            background: '#0066FF', display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <rect x="1" y="7" width="3" height="6" fill="white" rx="1" />
              <rect x="5.5" y="4" width="3" height="9" fill="white" rx="1" />
              <rect x="10" y="1" width="3" height="12" fill="white" rx="1" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', lineHeight: 1.2 }}>Job Market</div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', lineHeight: 1.2 }}>Intelligence</div>
          </div>
        </div>
      </div>

      <ul style={{ listStyle: 'none', marginTop: 12, display: 'flex', flexDirection: 'column', gap: 2 }} role="list">
        {links.map(({ to, label, icon: Icon }) => {
          const active = location.pathname === to
          return (
            <li key={to}>
              <NavLink
                to={to}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '8px 10px',
                  borderRadius: 8,
                  textDecoration: 'none',
                  fontSize: 13,
                  fontWeight: active ? 500 : 400,
                  color: active ? '#ffffff' : 'rgba(255,255,255,0.5)',
                  background: active ? 'rgba(255,255,255,0.06)' : 'transparent',
                  transition: 'all 150ms ease',
                  cursor: 'pointer',
                }}
                onMouseEnter={e => {
                  if (!active) (e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.8)'
                }}
                onMouseLeave={e => {
                  if (!active) (e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.5)'
                }}
                aria-current={active ? 'page' : undefined}
              >
                <Icon size={15} strokeWidth={1.75} aria-hidden="true" />
                {label}
                {active && (
                  <div style={{
                    marginLeft: 'auto',
                    width: 3, height: 3, borderRadius: '50%',
                    background: '#0066FF',
                  }} />
                )}
              </NavLink>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
