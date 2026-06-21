import { useEffect, useRef } from 'react'
import { motion, useMotionValue, useTransform, animate } from 'framer-motion'

interface MetricCardProps {
  label: string
  value: number | string
  animate?: boolean
  suffix?: string
}

export default function MetricCard({ label, value, animate: shouldAnimate = true, suffix = '' }: MetricCardProps) {
  const motionVal = useMotionValue(0)
  const rounded = useTransform(motionVal, v => Math.round(v).toLocaleString() + suffix)
  const hasAnimated = useRef(false)

  useEffect(() => {
    if (typeof value === 'number' && shouldAnimate && !hasAnimated.current) {
      hasAnimated.current = true
      const controls = animate(motionVal, value, { duration: 1.2, ease: 'easeOut' })
      return () => controls.stop()
    }
  }, [value, shouldAnimate, motionVal])

  return (
    <div
      style={{
        background: '#111111',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 10,
        padding: '20px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        cursor: 'default',
        transition: 'border-color 150ms ease',
      }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.14)')}
      onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)')}
    >
      <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', fontWeight: 500, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
        {label}
      </span>
      {typeof value === 'number' && shouldAnimate ? (
        <motion.span style={{ fontSize: 28, fontWeight: 600, color: '#fff', letterSpacing: '-0.02em', fontVariantNumeric: 'tabular-nums' }}>
          {rounded}
        </motion.span>
      ) : (
        <span style={{ fontSize: 28, fontWeight: 600, color: '#fff', letterSpacing: '-0.02em' }}>
          {typeof value === 'number' ? value.toLocaleString() : value}{suffix}
        </span>
      )}
    </div>
  )
}
