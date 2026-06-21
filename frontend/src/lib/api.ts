const BASE = (import.meta.env.VITE_API_URL ?? '') + '/api'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export interface OverviewData {
  empty: boolean
  total_jobs: number
  unique_skills: number
  n_clusters: number
  n_sources: number
  top_skills: { skill: string; count: number }[]
  weekly_postings: { week: string; count: number }[]
}

export interface HeatmapData {
  empty: boolean
  all_clusters: string[]
  clusters: string[]
  skills: string[]
  values: number[][]
}

export interface ClusterPoint {
  umap_x: number
  umap_y: number
  cluster_name: string
  title: string
  company: string
  location: string
}

export interface ClustersData {
  empty: boolean
  points: ClusterPoint[]
  cluster_sizes: { cluster: string; count: number }[]
}

export interface TrendRow {
  skill: string
  ds: string
  y: number | null
  yhat: number | null
  yhat_lower: number | null
  yhat_upper: number | null
}

export interface TrendsData {
  empty: boolean
  skills: string[]
  rising: string[]
  falling: string[]
  data: TrendRow[]
}

export interface ResumeReport {
  readiness_score: number
  market_percentile: number | null
  jobs_analysed: number
  skills_present: string[]
  skills_missing: string[]
  skill_demand: Record<string, string>
  role_top_skills: string[]
  emerging_skills: string[]
}

export const api = {
  overview: () => get<OverviewData>('/overview'),
  heatmap: (clusters?: string[]) => {
    const qs = clusters?.length ? '?' + clusters.map(c => `clusters=${encodeURIComponent(c)}`).join('&') : ''
    return get<HeatmapData>(`/heatmap${qs}`)
  },
  clusters: () => get<ClustersData>('/clusters'),
  roles: () => get<{ roles: string[] }>('/roles'),
  resume: async (file: File, role: string): Promise<ResumeReport> => {
    const form = new FormData()
    form.append('file', file)
    form.append('role', role)
    const res = await fetch(`${BASE}/resume`, { method: 'POST', body: form })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || res.statusText)
    }
    return res.json()
  },
}
