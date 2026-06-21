import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import Plot from 'react-plotly.js'
import { api } from '../lib/api'
import MetricCard from '../components/MetricCard'
import EmptyState from '../components/EmptyState'

const DARK = {
  paper_bgcolor: '#111111',
  plot_bgcolor: '#111111',
  font: { color: '#ffffff', family: 'Inter, sans-serif', size: 12 },
}

const page = { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -8 }, transition: { duration: 0.2 } }

export default function Overview() {
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ['overview'], queryFn: api.overview })

  if (isLoading) return <Skeleton />
  if (isError) return <ErrorState onRetry={refetch} />

  if (data?.empty) {
    return (
      <motion.div {...page}>
        <PageHeader title="Market Overview" />
        <EmptyState
          title="No data yet"
          description="Run the pipeline to populate market data."
          command="python pipeline.py --all"
        />
      </motion.div>
    )
  }

  return (
    <motion.div {...page} style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <PageHeader title="Market Overview" />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        <MetricCard label="Total Jobs" value={data!.total_jobs} />
        <MetricCard label="Unique Skills" value={data!.unique_skills} />
        <MetricCard label="Role Clusters" value={data!.n_clusters} />
        <MetricCard label="Data Sources" value={data!.n_sources} />
      </div>

      {data!.top_skills.length > 0 && (
        <ChartCard title="Top 30 Skills by Job Mention Count">
          <Plot
            data={[{
              type: 'bar',
              orientation: 'h',
              x: data!.top_skills.map(s => s.count),
              y: data!.top_skills.map(s => s.skill),
              marker: {
                color: data!.top_skills.map(s => s.count),
                colorscale: [[0, '#1A3A6E'], [1, '#0066FF']],
                showscale: false,
              },
              hovertemplate: '<b>%{y}</b><br>%{x:,} postings<extra></extra>',
            }]}
            layout={{
              ...DARK,
              height: 620,
              margin: { l: 160, r: 24, t: 16, b: 40 },
              yaxis: { categoryorder: 'total ascending', tickfont: { size: 12 } },
              xaxis: { title: { text: 'Job Postings', standoff: 10 }, gridcolor: 'rgba(255,255,255,0.05)' },
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%' }}
          />
        </ChartCard>
      )}

      {data!.weekly_postings.length > 0 && (
        <ChartCard title="Weekly Job Postings">
          <Plot
            data={[{
              type: 'scatter',
              fill: 'tozeroy',
              mode: 'lines',
              x: data!.weekly_postings.map(w => w.week),
              y: data!.weekly_postings.map(w => w.count),
              line: { color: '#0066FF', width: 2 },
              fillcolor: 'rgba(0,102,255,0.08)',
              hovertemplate: '%{x|%b %d, %Y}<br><b>%{y:,}</b> postings<extra></extra>',
            }]}
            layout={{
              ...DARK,
              height: 240,
              margin: { l: 50, r: 24, t: 16, b: 40 },
              xaxis: { gridcolor: 'rgba(255,255,255,0.05)' },
              yaxis: { gridcolor: 'rgba(255,255,255,0.05)' },
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%' }}
          />
        </ChartCard>
      )}
    </motion.div>
  )
}

function PageHeader({ title }: { title: string }) {
  return <h1 style={{ fontSize: 22, fontWeight: 600, color: '#fff', letterSpacing: '-0.02em', marginBottom: 4 }}>{title}</h1>
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: '#111111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '20px 24px' }}>
      <p style={{ fontSize: 13, fontWeight: 500, color: 'rgba(255,255,255,0.6)', marginBottom: 16 }}>{title}</p>
      {children}
    </div>
  )
}

function Skeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ height: 28, width: 180, borderRadius: 6, background: 'rgba(255,255,255,0.06)' }} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        {[0,1,2,3].map(i => <div key={i} style={{ height: 88, borderRadius: 10, background: 'rgba(255,255,255,0.04)' }} />)}
      </div>
      <div style={{ height: 640, borderRadius: 10, background: 'rgba(255,255,255,0.04)' }} />
    </div>
  )
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div style={{ padding: 40, textAlign: 'center' }}>
      <p style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 12 }}>Failed to load data. Is the API running?</p>
      <button
        onClick={onRetry}
        style={{ padding: '7px 16px', background: '#0066FF', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, cursor: 'pointer' }}
      >
        Retry
      </button>
    </div>
  )
}
