import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import Nav from './components/Nav'
import Overview from './pages/Overview'
import SkillHeatmap from './pages/SkillHeatmap'
import RoleClusters from './pages/RoleClusters'
import SkillTrends from './pages/SkillTrends'
import ResumeAnalyzer from './pages/ResumeAnalyzer'

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', height: '100%', background: '#0A0A0A' }}>
        <Nav />
        <main style={{ flex: 1, marginLeft: 256, padding: '32px 40px', overflowY: 'auto', minHeight: '100vh' }}>
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<Navigate to="/overview" replace />} />
              <Route path="/overview" element={<Overview />} />
              <Route path="/heatmap" element={<SkillHeatmap />} />
              <Route path="/clusters" element={<RoleClusters />} />
              <Route path="/trends" element={<SkillTrends />} />
              <Route path="/resume" element={<ResumeAnalyzer />} />
            </Routes>
          </AnimatePresence>
        </main>
      </div>
    </BrowserRouter>
  )
}
