interface EmptyStateProps {
  title: string
  description: string
  command?: string
}

export default function EmptyState({ title, description, command }: EmptyStateProps) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      padding: '80px 32px', gap: 16, textAlign: 'center',
      background: '#111111', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 12,
    }}>
      <div style={{
        width: 40, height: 40, borderRadius: 10,
        background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
          <circle cx="9" cy="9" r="7.5" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" />
          <path d="M9 5.5v4M9 11.5v1" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </div>
      <div>
        <p style={{ fontSize: 15, fontWeight: 600, color: '#fff', marginBottom: 6 }}>{title}</p>
        <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', maxWidth: 340, lineHeight: 1.6 }}>{description}</p>
      </div>
      {command && (
        <code style={{
          fontSize: 12, padding: '6px 12px', borderRadius: 6,
          background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
          color: 'rgba(255,255,255,0.6)', fontFamily: 'ui-monospace, Consolas, monospace',
        }}>
          {command}
        </code>
      )}
    </div>
  )
}
