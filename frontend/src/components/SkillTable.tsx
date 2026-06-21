interface Row {
  skill: string
  demand: string
  haveIt: boolean
  trending: boolean
}

interface SkillTableProps {
  rows: Row[]
}

export default function SkillTable({ rows }: SkillTableProps) {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }} aria-label="Top recommended skills">
      <thead>
        <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          {['Skill', 'Demand', 'Have it', 'Trending'].map(h => (
            <th
              key={h}
              style={{
                padding: '8px 12px', textAlign: 'left', fontWeight: 500,
                color: 'rgba(255,255,255,0.4)', fontSize: 11,
                letterSpacing: '0.04em', textTransform: 'uppercase',
              }}
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr
            key={row.skill}
            style={{
              borderBottom: i < rows.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
            }}
          >
            <td style={{ padding: '10px 12px', color: '#fff', fontWeight: 500 }}>{row.skill}</td>
            <td style={{ padding: '10px 12px' }}>
              <span style={{
                fontSize: 11, fontWeight: 500, padding: '2px 7px', borderRadius: 3,
                background: row.demand === 'High' ? 'rgba(0,102,255,0.15)' : row.demand === 'Medium' ? 'rgba(255,149,0,0.12)' : 'rgba(255,255,255,0.06)',
                color: row.demand === 'High' ? '#4D94FF' : row.demand === 'Medium' ? '#FF9500' : 'rgba(255,255,255,0.4)',
              }}>
                {row.demand}
              </span>
            </td>
            <td style={{ padding: '10px 12px', textAlign: 'center' }}>
              {row.haveIt
                ? <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-label="Yes"><path d="M2 7l4 4 6-7" stroke="#00C853" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" /></svg>
                : <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-label="No"><path d="M3 3l8 8M11 3l-8 8" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" strokeLinecap="round" /></svg>
              }
            </td>
            <td style={{ padding: '10px 12px', textAlign: 'center' }}>
              {row.trending && (
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-label="Trending up">
                  <path d="M1 10L5 6l3 3 5-7" stroke="#0066FF" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M9 3h4v4" stroke="#0066FF" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
