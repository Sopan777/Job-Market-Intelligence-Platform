import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import Plot from 'react-plotly.js'
import { api } from '../lib/api'
import EmptyState from '../components/EmptyState'

const DARK = {
  paper_bgcolor: '#111111',
  plot_bgcolor: '#111111',
  font: { color: '#ffffff', family: 'Inter, sans-serif', size: 12 },
}

const page = { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -8 }, transition: { duration: 0.2 } }

export default function SkillHeatmap() {
  const [selected, setSelected] = useState<string[]>([])

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['heatmap', selected],
    queryFn: () => api.heatmap(selected),
  })

  const allClusters = data?.all_clusters ?? []

  function toggle(cluster: string) {
    setSelected(prev =>
      prev.includes(cluster) ? prev.filter(c => c !== cluster) : [...prev, cluster]
    )
  }

  if (isLoading) return <Skeleton />
  if (isError) return <ErrorState onRetry={refetch} />

  if (data?.empty) {
    return (
      <motion.div {...page}>
        <PageHeader />
        <EmptyState
          title="No clustering data"
          description="Run the clustering step to generate role clusters and skill heatmap."
          command="python pipeline.py --cluster"
        />
      </motion.div>
    )
  }

  return (
    <motion.div {...page} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <PageHeader />

      {allClusters.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {allClusters.map(c => {
            const active = selected.length === 0 || selected.includes(c)
            return (
              <button
                key={c}
                onClick={() => toggle(c)}
                style={{
                  padding: '4px 10px', borderRadius: 4, fontSize: 12, fontWeight: 500,
                  cursor: 'pointer', border: '1px solid',
                  transition: 'all 150ms ease',
                  background: active ? 'rgba(0,102,255,0.15)' : 'rgba(255,255,255,0.04)',
                  color: active ? '#4D94FF' : 'rgba(255,255,255,0.4)',
                  borderColor: active ? 'rgba(0,102,255,0.3)' : 'rgba(255,255,255,0.08)',
                }}
              >
                {c}
              </button>
            )
          })}
          {selected.length > 0 && (
            <button
              onClick={() => setSelected([])}
              style={{ padding: '4px 10px', borderRadius: 4, fontSize: 12, cursor: 'pointer', background: 'transparent', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.3)' }}
            >
              Reset
            </button>
          )}
        </div>
      )}

      <div style={{ background: '#111111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '20px 24px' }}>
        <Plot
          data={[{
            type: 'heatmap',
            z: data!.values,
            x: data!.skills,
            y: data!.clusters,
            colorscale: 'YlOrRd',
            hovertemplate: '<b>%{y}</b><br>%{x}<br>%{z} jobs<extra></extra>',
          }]}
          layout={{
            ...DARK,
            height: Math.max(380, data!.clusters.length * 38),
            margin: { l: 180, r: 24, t: 16, b: 100 },
            xaxis: { tickangle: -40, tickfont: { size: 11 } },
            yaxis: { tickfont: { size: 12 } },
          }}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: '100%' }}
        />
      </div>
    </motion.div>
  )
}

function PageHeader() {
  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 600, color: '#fff', letterSpacing: '-0.02em' }}>Skill Heatmap</h1>
      <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', marginTop: 4 }}>Skill frequency across role clusters</p>
    </div>
  )
}

function Skeleton() {
  return <div style={{ height: 500, borderRadius: 10, background: 'rgba(255,255,255,0.04)' }} />
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div style={{ padding: 40, textAlign: 'center' }}>
      <p style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 12 }}>Failed to load heatmap data.</p>
      <button onClick={onRetry} style={{ padding: '7px 16px', background: '#0066FF', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, cursor: 'pointer' }}>Retry</button>
    </div>
  )
}
