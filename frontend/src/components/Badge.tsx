interface BadgeProps {
  label: string
  variant: 'rising' | 'falling' | 'neutral'
}

const styles: Record<BadgeProps['variant'], React.CSSProperties> = {
  rising: { background: 'rgba(0,200,83,0.12)', color: '#00C853', border: '1px solid rgba(0,200,83,0.2)' },
  falling: { background: 'rgba(255,59,48,0.12)', color: '#FF3B30', border: '1px solid rgba(255,59,48,0.2)' },
  neutral: { background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.5)', border: '1px solid rgba(255,255,255,0.08)' },
}

export default function Badge({ label, variant }: BadgeProps) {
  return (
    <span
      style={{
        ...styles[variant],
        fontSize: 12,
        fontWeight: 500,
        padding: '3px 8px',
        borderRadius: 4,
        display: 'inline-block',
        lineHeight: 1.5,
      }}
    >
      {label}
    </span>
  )
}
