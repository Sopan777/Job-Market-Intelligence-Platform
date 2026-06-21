import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import Plot from 'react-plotly.js'
import { api, type ResumeReport } from '../lib/api'
import SkillTable from '../components/SkillTable'
import Badge from '../components/Badge'

const DARK = { paper_bgcolor: '#111111', plot_bgcolor: '#111111', font: { color: '#fff', family: 'Inter, sans-serif' } }
const page = { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -8 }, transition: { duration: 0.2 } }

export default function ResumeAnalyzer() {
  const [roles, setRoles] = useState<string[]>([])
  const [role, setRole] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<ResumeReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    api.roles().then(({ roles }) => {
      setRoles(roles)
      if (roles.length > 0) setRole(roles[0])
    }).catch(() => {})
  }, [])

  async function submit() {
    if (!file) return
    setLoading(true)
    setError(null)
    setReport(null)
    try {
      const result = await api.resume(file, role)
      setReport(result)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Analysis failed.')
    } finally {
      setLoading(false)
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) setFile(dropped)
  }

  return (
    <motion.div {...page} style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: '#fff', letterSpacing: '-0.02em' }}>Resume Analyzer</h1>
        <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', marginTop: 4 }}>Upload your resume and target a role to see your skill gap</p>
      </div>

      <div style={{ background: '#111111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 16, marginBottom: 20 }}>
          <div>
            <label htmlFor="role-select" style={{ fontSize: 12, fontWeight: 500, color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: 6, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Target Role
            </label>
            <select
              id="role-select"
              value={role}
              onChange={e => setRole(e.target.value)}
              style={{
                width: '100%', padding: '9px 12px', background: '#1A1A1A',
                border: '1px solid rgba(255,255,255,0.1)', borderRadius: 7,
                color: '#fff', fontSize: 13, cursor: 'pointer', outline: 'none',
                appearance: 'none',
              }}
            >
              {roles.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>

          <div>
            <label style={{ fontSize: 12, fontWeight: 500, color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: 6, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Resume (PDF or DOCX)
            </label>
            <div
              role="button"
              tabIndex={0}
              aria-label="Upload resume file"
              onClick={() => inputRef.current?.click()}
              onKeyDown={e => e.key === 'Enter' && inputRef.current?.click()}
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              style={{
                border: `1px dashed ${dragging ? '#0066FF' : file ? 'rgba(0,102,255,0.4)' : 'rgba(255,255,255,0.12)'}`,
                borderRadius: 7, padding: '14px 16px', cursor: 'pointer',
                background: dragging ? 'rgba(0,102,255,0.06)' : 'rgba(255,255,255,0.02)',
                transition: 'all 150ms ease', display: 'flex', alignItems: 'center', gap: 10,
              }}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M8 2v8M4 6l4-4 4 4" stroke={file ? '#0066FF' : 'rgba(255,255,255,0.3)'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 12h12" stroke={file ? '#0066FF' : 'rgba(255,255,255,0.15)'} strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              <span style={{ fontSize: 13, color: file ? '#fff' : 'rgba(255,255,255,0.4)' }}>
                {file ? file.name : 'Drop file here or click to browse'}
              </span>
              <input
                ref={inputRef}
                type="file"
                accept=".pdf,.docx"
                style={{ display: 'none' }}
                aria-label="Resume file input"
                onChange={e => e.target.files?.[0] && setFile(e.target.files[0])}
              />
            </div>
          </div>
        </div>

        <button
          onClick={submit}
          disabled={!file || loading}
          style={{
            padding: '9px 20px', background: !file || loading ? 'rgba(0,102,255,0.3)' : '#0066FF',
            color: '#fff', border: 'none', borderRadius: 7, fontSize: 13, fontWeight: 500,
            cursor: !file || loading ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: 8,
            transition: 'background 150ms ease',
          }}
        >
          {loading && (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true" style={{ animation: 'spin 1s linear infinite' }}>
              <circle cx="7" cy="7" r="5.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" />
              <path d="M7 1.5A5.5 5.5 0 0112.5 7" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          )}
          {loading ? 'Analysing…' : 'Analyze Resume'}
        </button>

        {error && (
          <p style={{ marginTop: 12, fontSize: 13, color: '#FF3B30' }}>{error}</p>
        )}
      </div>

      {report && <ReportView report={report} role={role} />}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </motion.div>
  )
}

function ReportView({ report, role }: { report: ResumeReport; role: string }) {
  const scoreColor = report.readiness_score >= 70 ? '#00C853' : report.readiness_score >= 40 ? '#FF9500' : '#FF3B30'
  const presentSet = new Set(report.skills_present.map(s => s.toLowerCase()))
  const emergingSet = new Set(report.emerging_skills.map(s => s.toLowerCase()))

  const tableRows = report.role_top_skills.slice(0, 10).map(skill => ({
    skill,
    demand: report.skill_demand[skill] ?? 'Low',
    haveIt: presentSet.has(skill.toLowerCase()),
    trending: emergingSet.has(skill.toLowerCase()),
  }))

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 1fr', gap: 12 }}>
        <div style={{ background: '#111111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '20px 24px' }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>Readiness Score</p>
          <p style={{ fontSize: 36, fontWeight: 700, color: scoreColor, letterSpacing: '-0.03em', fontVariantNumeric: 'tabular-nums' }}>{report.readiness_score}<span style={{ fontSize: 16, color: 'rgba(255,255,255,0.3)' }}>/100</span></p>
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)', marginTop: 6 }}>Based on {report.jobs_analysed.toLocaleString()} {role} postings</p>
        </div>

        <div style={{ background: '#111111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '8px 16px' }}>
          <Plot
            data={[{
              type: 'indicator', mode: 'gauge+number',
              value: report.readiness_score,
              number: { suffix: '/100', font: { size: 24, color: scoreColor } },
              gauge: {
                axis: { range: [0, 100], tickwidth: 0, tickcolor: 'transparent' },
                bar: { color: scoreColor, thickness: 0.25 },
                bgcolor: 'transparent',
                borderwidth: 0,
                steps: [
                  { range: [0, 40], color: 'rgba(255,59,48,0.1)' },
                  { range: [40, 70], color: 'rgba(255,149,0,0.1)' },
                  { range: [70, 100], color: 'rgba(0,200,83,0.1)' },
                ],
              },
            }]}
            layout={{ ...DARK, height: 160, margin: { t: 20, b: 20, l: 40, r: 40 } }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%' }}
          />
        </div>

        {report.market_percentile !== null && (
          <div style={{ background: '#111111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '20px 24px' }}>
            <p style={{ fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>Market Position</p>
            <p style={{ fontSize: 32, fontWeight: 700, color: '#fff', letterSpacing: '-0.02em' }}>Top {100 - report.market_percentile}%</p>
            <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)', marginTop: 6 }}>Better than {report.market_percentile}% of postings</p>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <SkillSection title={`Skills Found (${report.skills_present.length})`} skills={report.skills_present} demand={report.skill_demand} variant="present" />
        <SkillSection title={`Missing Skills (${report.skills_missing.length})`} skills={report.skills_missing} demand={report.skill_demand} variant="missing" />
      </div>

      {tableRows.length > 0 && (
        <div style={{ background: '#111111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '20px 24px' }}>
          <p style={{ fontSize: 13, fontWeight: 500, color: 'rgba(255,255,255,0.6)', marginBottom: 16 }}>Top 10 Recommended Skills</p>
          <SkillTable rows={tableRows} />
        </div>
      )}

      {report.emerging_skills.length > 0 && (
        <div style={{ background: 'rgba(0,102,255,0.06)', border: '1px solid rgba(0,102,255,0.2)', borderRadius: 10, padding: '20px 24px' }}>
          <p style={{ fontSize: 13, fontWeight: 600, color: '#4D94FF', marginBottom: 10 }}>Ahead of the Curve</p>
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', marginBottom: 12 }}>Skills on your resume trending strongly upward in the market.</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {report.emerging_skills.map(s => <Badge key={s} label={s} variant="rising" />)}
          </div>
        </div>
      )}
    </motion.div>
  )
}

function SkillSection({ title, skills, demand, variant }: { title: string; skills: string[]; demand: Record<string, string>; variant: 'present' | 'missing' }) {
  if (skills.length === 0) {
    return (
      <div style={{ background: '#111111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '20px 24px' }}>
        <p style={{ fontSize: 13, fontWeight: 500, color: 'rgba(255,255,255,0.6)', marginBottom: 12 }}>{title}</p>
        <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.3)' }}>
          {variant === 'present' ? 'No matching skills found.' : 'All top skills accounted for.'}
        </p>
      </div>
    )
  }

  return (
    <div style={{ background: '#111111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '20px 24px' }}>
      <p style={{ fontSize: 13, fontWeight: 500, color: 'rgba(255,255,255,0.6)', marginBottom: 12 }}>{title}</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 300, overflowY: 'auto' }}>
        {skills.map(skill => {
          const d = demand[skill] ?? 'Low'
          const color = variant === 'present'
            ? (d === 'High' ? '#00C853' : d === 'Medium' ? '#FF9500' : 'rgba(255,255,255,0.3)')
            : (d === 'High' ? '#FF3B30' : d === 'Medium' ? '#FF9500' : 'rgba(255,255,255,0.3)')
          return (
            <div key={skill} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px', borderRadius: 6, background: 'rgba(255,255,255,0.03)' }}>
              <span style={{ fontSize: 13, color: '#fff' }}>{skill}</span>
              <span style={{ fontSize: 11, fontWeight: 500, color, padding: '2px 7px', borderRadius: 3, background: `${color}1a` }}>{d}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
