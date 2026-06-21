import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import Plot from 'react-plotly.js'
import { api } from '../lib/api'
import Badge from '../components/Badge'
import EmptyState from '../components/EmptyState'

const DARK = {
  paper_bgcolor: '#111111',
  plot_bgcolor: '#111111',
  font: { color: '#ffffff', family: 'Inter, sans-serif', size: 12 },
}

const page = { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -8 }, transition: { duration: 0.2 } }

const PLOTLY_COLORS = [
  '#0066FF','#FF6B35','#00C853','#FFB800','#9B59B6',
  '#1ABC9C','#E74C3C','#3498DB','#F39C12','#2ECC71',
]

export default function SkillTrends() {
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ['trends'], queryFn: api.trends })
  const [selected, setSelected] = useState<string[]>([])

  const skills = data?.skills ?? []
  const activeSkills = selected.length > 0 ? selected : skills.slice(0, 5)

  function toggle(skill: string) {
    setSelected(prev => prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill])
  }

  if (isLoading) return <Skeleton />
  if (isError) return <ErrorState onRetry={refetch} />

  if (data?.empty) {
    return (
      <motion.div {...page}>
        <PageHeader />
        <EmptyState title="No forecast data" description="Run the forecasting pipeline to generate skill demand trends." command="python pipeline.py --forecast" />
      </motion.div>
    )
  }

  const today = new Date().toISOString().split('T')[0]

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const traces: any[] = []
  activeSkills.forEach((skill, i) => {
    const color = PLOTLY_COLORS[i % PLOTLY_COLORS.length]
    const rows = data!.data.filter(r => r.skill === skill).sort((a, b) => a.ds.localeCompare(b.ds))
    const hist = rows.filter(r => r.ds <= today && r.y !== null)
    const fcast = rows.filter(r => r.ds > today)

    if (hist.length) {
      traces.push({
        type: 'scatter', mode: 'lines+markers',
        name: `${skill} (actual)`,
        x: hist.map(r => r.ds), y: hist.map(r => r.y),
        line: { color, width: 2 }, marker: { size: 4 },
        hovertemplate: `<b>${skill}</b><br>%{x|%b %d}<br>%{y:.0f} postings<extra>actual</extra>`,
      })
    }

    if (fcast.length) {
      traces.push({
        type: 'scatter', mode: 'lines',
        name: `${skill} (forecast)`,
        x: fcast.map(r => r.ds), y: fcast.map(r => r.yhat),
        line: { color, width: 2, dash: 'dash' },
        hovertemplate: `<b>${skill}</b><br>%{x|%b %d}<br>%{y:.0f} (forecast)<extra></extra>`,
      })

      const upper = fcast.map(r => r.yhat_upper ?? r.yhat)
      const lower = fcast.map(r => r.yhat_lower ?? r.yhat)
      const xs = fcast.map(r => r.ds)
      traces.push({
        type: 'scatter', mode: 'none',
        x: [...xs, ...[...xs].reverse()],
        y: [...upper, ...[...lower].reverse()],
        fill: 'toself',
        fillcolor: color.startsWith('#')
          ? hexToRgba(color, 0.1)
          : color,
        line: { color: 'transparent' },
        showlegend: false, hoverinfo: 'skip',
      })
    }
  })

  return (
    <motion.div {...page} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <PageHeader />

      {(data!.rising.length > 0 || data!.falling.length > 0) && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {data!.rising.length > 0 && (
            <div style={{ background: '#111111', border: '1px solid rgba(0,200,83,0.15)', borderRadius: 10, padding: '16px 20px' }}>
              <p style={{ fontSize: 11, fontWeight: 600, color: '#00C853', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Rising ({data!.rising.length})</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {data!.rising.slice(0, 15).map(s => <Badge key={s} label={s} variant="rising" />)}
              </div>
            </div>
          )}
          {data!.falling.length > 0 && (
            <div style={{ background: '#111111', border: '1px solid rgba(255,59,48,0.15)', borderRadius: 10, padding: '16px 20px' }}>
              <p style={{ fontSize: 11, fontWeight: 600, color: '#FF3B30', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Declining ({data!.falling.length})</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {data!.falling.slice(0, 15).map(s => <Badge key={s} label={s} variant="falling" />)}
              </div>
            </div>
          )}
        </div>
      )}

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {skills.map((s) => {
          const active = activeSkills.includes(s)
          const color = PLOTLY_COLORS[Math.max(0, activeSkills.indexOf(s)) % PLOTLY_COLORS.length]
          return (
            <button key={s} onClick={() => toggle(s)} style={{
              padding: '4px 10px', borderRadius: 4, fontSize: 12, fontWeight: 500,
              cursor: 'pointer', border: '1px solid', transition: 'all 150ms ease',
              background: active ? hexToRgba(color, 0.12) : 'rgba(255,255,255,0.04)',
              color: active ? color : 'rgba(255,255,255,0.4)',
              borderColor: active ? hexToRgba(color, 0.3) : 'rgba(255,255,255,0.08)',
            }}>
              {s}
            </button>
          )
        })}
      </div>

      <div style={{ background: '#111111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '20px 24px' }}>
        <Plot
          data={traces}
          layout={{
            ...DARK,
            height: 480,
            margin: { l: 50, r: 24, t: 16, b: 50 },
            xaxis: { title: { text: 'Week' }, gridcolor: 'rgba(255,255,255,0.05)' },
            yaxis: { title: { text: 'Job Postings' }, gridcolor: 'rgba(255,255,255,0.05)' },
            hovermode: 'x unified',
            shapes: [{
              type: 'line', x0: today, x1: today, y0: 0, y1: 1, yref: 'paper',
              line: { color: 'rgba(255,255,255,0.2)', width: 1, dash: 'dot' },
            }],
            annotations: [{
              x: today, y: 1, yref: 'paper', text: 'Today',
              showarrow: false, font: { size: 11, color: 'rgba(255,255,255,0.3)' }, xanchor: 'left', xshift: 6,
            }],
            legend: { font: { size: 11 }, bgcolor: 'rgba(0,0,0,0)', borderwidth: 0 },
          }}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: '100%' }}
        />
      </div>
    </motion.div>
  )
}

function hexToRgba(hex: string, alpha: number) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

function PageHeader() {
  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 600, color: '#fff', letterSpacing: '-0.02em' }}>Skill Trends</h1>
      <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', marginTop: 4 }}>Historical weekly demand + 26-week forecast</p>
    </div>
  )
}

function Skeleton() {
  return <div style={{ height: 540, borderRadius: 10, background: 'rgba(255,255,255,0.04)' }} />
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div style={{ padding: 40, textAlign: 'center' }}>
      <p style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 12 }}>Failed to load trends.</p>
      <button onClick={onRetry} style={{ padding: '7px 16px', background: '#0066FF', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, cursor: 'pointer' }}>Retry</button>
    </div>
  )
}
