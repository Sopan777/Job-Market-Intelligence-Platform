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

export default function RoleClusters() {
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ['clusters'], queryFn: api.clusters })

  if (isLoading) return <Skeleton />
  if (isError) return <ErrorState onRetry={refetch} />

  if (data?.empty) {
    return (
      <motion.div {...page}>
        <PageHeader />
        <EmptyState
          title="No UMAP data"
          description="Run the clustering pipeline to generate the 2D job role projection."
          command="python pipeline.py --cluster"
        />
      </motion.div>
    )
  }

  const clusterNames = [...new Set(data!.points.map(p => p.cluster_name))]

  const scatterTraces = clusterNames.map(name => {
    const pts = data!.points.filter(p => p.cluster_name === name)
    return {
      type: 'scatter' as const,
      mode: 'markers' as const,
      name,
      x: pts.map(p => p.umap_x),
      y: pts.map(p => p.umap_y),
      text: pts.map(p => `${p.title}<br>${p.company}<br>${p.location}`),
      hovertemplate: '%{text}<extra>%{fullData.name}</extra>',
      marker: { size: 4, opacity: 0.65 },
    }
  })

  return (
    <motion.div {...page} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <PageHeader />

      <div style={{ background: '#111111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '20px 24px' }}>
        <p style={{ fontSize: 13, fontWeight: 500, color: 'rgba(255,255,255,0.6)', marginBottom: 16 }}>
          2D UMAP Projection — {data!.points.length.toLocaleString()} jobs sampled
        </p>
        <Plot
          data={scatterTraces}
          layout={{
            ...DARK,
            height: 560,
            margin: { l: 40, r: 24, t: 16, b: 40 },
            xaxis: { title: { text: 'UMAP-1' }, gridcolor: 'rgba(255,255,255,0.05)', zeroline: false },
            yaxis: { title: { text: 'UMAP-2' }, gridcolor: 'rgba(255,255,255,0.05)', zeroline: false },
            legend: { itemsizing: 'constant', font: { size: 11 }, bgcolor: 'rgba(0,0,0,0)', bordercolor: 'rgba(255,255,255,0.08)', borderwidth: 1 },
            hovermode: 'closest',
          }}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: '100%' }}
        />
      </div>

      {data!.cluster_sizes.length > 0 && (
        <div style={{ background: '#111111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '20px 24px' }}>
          <p style={{ fontSize: 13, fontWeight: 500, color: 'rgba(255,255,255,0.6)', marginBottom: 16 }}>Cluster Sizes</p>
          <Plot
            data={[{
              type: 'bar',
              x: data!.cluster_sizes.map(c => c.cluster),
              y: data!.cluster_sizes.map(c => c.count),
              marker: { color: '#0066FF', opacity: 0.8 },
              hovertemplate: '<b>%{x}</b><br>%{y:,} jobs<extra></extra>',
            }]}
            layout={{
              ...DARK,
              height: 300,
              margin: { l: 50, r: 24, t: 16, b: 100 },
              xaxis: { tickangle: -30, tickfont: { size: 11 } },
              yaxis: { gridcolor: 'rgba(255,255,255,0.05)' },
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%' }}
          />
        </div>
      )}
    </motion.div>
  )
}

function PageHeader() {
  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 600, color: '#fff', letterSpacing: '-0.02em' }}>Role Clusters</h1>
      <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', marginTop: 4 }}>UMAP + HDBSCAN — jobs projected to 2D space</p>
    </div>
  )
}

function Skeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ height: 28, width: 160, borderRadius: 6, background: 'rgba(255,255,255,0.06)' }} />
      <div style={{ height: 580, borderRadius: 10, background: 'rgba(255,255,255,0.04)' }} />
    </div>
  )
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div style={{ padding: 40, textAlign: 'center' }}>
      <p style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 12 }}>Failed to load cluster data.</p>
      <button onClick={onRetry} style={{ padding: '7px 16px', background: '#0066FF', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, cursor: 'pointer' }}>Retry</button>
    </div>
  )
}
