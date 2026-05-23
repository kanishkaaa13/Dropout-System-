import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts'
import { format, parseISO } from 'date-fns'
import api from '../../api/axiosConfig'
import RiskBadge from '../../components/RiskBadge'
import RiskGauge from '../../components/RiskGauge'
import ShapChart from '../../components/ShapChart'
import ScoreTrendChart from '../../components/ScoreTrendChart'
import clsx from 'clsx'
import { RefreshCw, User, Calendar, Hash, GraduationCap } from 'lucide-react'

const TABS = ['Overview', 'Mock Tests', 'Surveys', 'Risk History', 'Alerts']

const Skeleton = ({ className }) => <div className={clsx('animate-pulse bg-slate-100 rounded-lg', className)} />

// ── Metric card ───────────────────────────────────────────────────────────────
function MetricCard({ label, value, sub, color = 'text-slate-800' }) {
  return (
    <div className="bg-white rounded-xl border border-slate-100 p-4">
      <p className={clsx('text-2xl font-bold tabular-nums', color)}>{value ?? '—'}</p>
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mt-1">{label}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  )
}

// ── Subject Radar ─────────────────────────────────────────────────────────────
function SubjectRadar({ mockResults }) {
  if (!mockResults?.length) return null
  const last = mockResults[mockResults.length - 1]
  const data = [
    { subject: 'Physics',   score: last.physics_score   || 0, max: 120 },
    { subject: 'Chemistry', score: last.chemistry_score || 0, max: 120 },
    { subject: 'Maths',     score: last.maths_score     || 0, max: 120 },
  ]
  return (
    <ResponsiveContainer width="100%" height={200}>
      <RadarChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
        <PolarGrid stroke="#E2E8F0" />
        <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: '#64748B' }} />
        <PolarRadiusAxis domain={[0, 120]} tick={false} axisLine={false} />
        <Radar dataKey="score" stroke="#6366F1" fill="#6366F1" fillOpacity={0.2} strokeWidth={2} />
      </RadarChart>
    </ResponsiveContainer>
  )
}

export default function StudentDetail() {
  const { id } = useParams()
  const [student, setStudent]       = useState(null)
  const [assessment, setAssessment] = useState(null)
  const [explanation, setExplanation] = useState(null)
  const [mockTests, setMockTests]   = useState([])
  const [surveys, setSurveys]       = useState([])
  const [riskHistory, setRiskHistory] = useState([])
  const [alerts, setAlerts]         = useState([])
  const [activeTab, setActiveTab]   = useState('Overview')
  const [loading, setLoading]       = useState(true)
  const [predicting, setPredicting] = useState(false)
  const [error, setError]           = useState(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [stuRes, mockRes, histRes] = await Promise.all([
        api.get(`/students/${id}`),
        api.get(`/students/${id}/mock-tests`),
        api.get(`/students/${id}/risk-history`),
      ])
      setStudent(stuRes.data)
      setMockTests(mockRes.data)
      setRiskHistory(histRes.data)

      // Latest explanation
      try {
        const exRes = await api.get(`/predict/explain/${id}`)
        setExplanation(exRes.data)
        setAssessment({ risk_score: exRes.data.risk_score, risk_level: exRes.data.risk_level })
      } catch (_) { /* no prediction yet */ }
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load student data')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { fetchData() }, [fetchData])

  const runPrediction = async () => {
    setPredicting(true)
    try {
      const { data } = await api.post(`/predict/${id}`)
      setAssessment(data)
      // Refresh explanation
      const exRes = await api.get(`/predict/explain/${id}`)
      setExplanation(exRes.data)
      // Refresh risk history
      const histRes = await api.get(`/students/${id}/risk-history`)
      setRiskHistory(histRes.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Prediction failed')
    } finally {
      setPredicting(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-28" />
        <div className="grid grid-cols-2 gap-4"><Skeleton className="h-48" /><Skeleton className="h-48" /></div>
      </div>
    )
  }

  if (error && !student) {
    return <div className="bg-red-50 text-red-700 rounded-xl p-4 text-sm">{error}</div>
  }

  const riskLevel = assessment?.risk_level || 'Low'
  const riskScore = assessment?.risk_score || 0

  return (
    <div className="space-y-6">
      {/* Student header */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <div className="flex flex-col sm:flex-row sm:items-start gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-3 mb-1">
              <h1 className="text-xl font-bold text-slate-900">{student?.full_name}</h1>
              <RiskBadge level={riskLevel} size="md" showLabel />
            </div>
            <div className="flex flex-wrap gap-4 text-sm text-slate-500 mt-2">
              <span className="flex items-center gap-1.5"><Hash className="w-3.5 h-3.5" />{student?.student_code || 'No code'}</span>
              <span className="flex items-center gap-1.5"><GraduationCap className="w-3.5 h-3.5" />Batch {student?.batch_id || '—'}</span>
              <span className="flex items-center gap-1.5"><User className="w-3.5 h-3.5" />Faculty ID {student?.assigned_faculty_id || '—'}</span>
              {student?.enrollment_date && (
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5" />
                  Enrolled {format(parseISO(student.enrollment_date), 'dd MMM yyyy')}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={runPrediction}
            disabled={predicting}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition-colors shrink-0"
          >
            <RefreshCw className={clsx('w-4 h-4', predicting && 'animate-spin')} />
            {predicting ? 'Running…' : 'Run New Prediction'}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">{error}</div>
      )}

      {/* Gauge + SHAP side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 flex flex-col items-center justify-center lg:col-span-2">
          <h2 className="text-sm font-semibold text-slate-700 mb-4 self-start">Dropout Risk Score</h2>
          <RiskGauge score={riskScore} level={riskLevel} size={220} />
          {explanation?.counselor_summary && (
            <p className="text-xs text-slate-500 text-center mt-4 leading-relaxed max-w-xs">
              {explanation.counselor_summary}
            </p>
          )}
        </div>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 lg:col-span-3">
          <ShapChart impacts={explanation?.top_factors || []} />
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="flex border-b border-slate-100 overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={clsx(
                'px-5 py-3.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2',
                activeTab === tab
                  ? 'border-indigo-600 text-indigo-600 bg-indigo-50/50'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="p-6">
          {/* OVERVIEW TAB */}
          {activeTab === 'Overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <MetricCard label="Mock Tests" value={mockTests.length} />
                <MetricCard
                  label="Last Score"
                  value={mockTests.at(-1)?.total_score?.toFixed(0)}
                  sub="out of 360"
                  color={mockTests.at(-1)?.total_score > 180 ? 'text-emerald-600' : 'text-red-600'}
                />
                <MetricCard label="Risk Score" value={riskScore?.toFixed(1)} sub="/ 100" />
                <MetricCard label="Target Rank" value={student?.target_rank?.toLocaleString()} />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">Score Trend</h3>
                  <ScoreTrendChart mockResults={mockTests} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">Last Test Breakdown</h3>
                  <SubjectRadar mockResults={mockTests} />
                </div>
              </div>
            </div>
          )}

          {/* MOCK TESTS TAB */}
          {activeTab === 'Mock Tests' && (
            <div className="space-y-5">
              <ScoreTrendChart mockResults={mockTests} showSubjects />
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100">
                      {['Date', 'Name', 'Type', 'Total', 'Physics', 'Chemistry', 'Maths', 'Percentile'].map((h) => (
                        <th key={h} className="pb-3 text-left text-xs font-semibold text-slate-500 pr-4">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {mockTests.map((t) => (
                      <tr key={t.id} className="hover:bg-slate-50">
                        <td className="py-2.5 pr-4 text-slate-500 text-xs">{t.test_date ? format(parseISO(t.test_date), 'dd MMM yy') : '—'}</td>
                        <td className="py-2.5 pr-4 font-medium text-slate-800">{t.test_name}</td>
                        <td className="py-2.5 pr-4">
                          <span className="text-xs bg-slate-100 text-slate-600 rounded px-1.5 py-0.5 capitalize">{t.test_type}</span>
                        </td>
                        <td className="py-2.5 pr-4 font-bold tabular-nums text-slate-800">{t.total_score?.toFixed(0)}</td>
                        <td className="py-2.5 pr-4 tabular-nums text-slate-600">{t.physics_score?.toFixed(0)}</td>
                        <td className="py-2.5 pr-4 tabular-nums text-slate-600">{t.chemistry_score?.toFixed(0)}</td>
                        <td className="py-2.5 pr-4 tabular-nums text-slate-600">{t.maths_score?.toFixed(0)}</td>
                        <td className="py-2.5 tabular-nums text-slate-600">{t.percentile?.toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SURVEYS TAB */}
          {activeTab === 'Surveys' && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    {['Week', 'Date', 'Burnout', 'Stress', 'Sleep hrs', 'Study hrs', 'Parental Pressure', 'Motivation'].map((h) => (
                      <th key={h} className="pb-3 text-left text-xs font-semibold text-slate-500 pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {surveys.length === 0 && (
                    <tr><td colSpan={8} className="py-8 text-center text-slate-400 text-sm">No surveys recorded</td></tr>
                  )}
                  {surveys.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50">
                      <td className="py-2.5 pr-4 font-mono text-xs text-slate-500">W{s.week_number}</td>
                      <td className="py-2.5 pr-4 text-slate-500 text-xs">{s.survey_date ? format(parseISO(s.survey_date), 'dd MMM yy') : '—'}</td>
                      <td className={clsx('py-2.5 pr-4 font-semibold', s.burnout_score >= 7 ? 'text-red-600' : 'text-slate-700')}>{s.burnout_score}/10</td>
                      <td className={clsx('py-2.5 pr-4 font-semibold', s.stress_level >= 7 ? 'text-red-600' : 'text-slate-700')}>{s.stress_level}/10</td>
                      <td className="py-2.5 pr-4 tabular-nums text-slate-600">{s.sleep_hours_avg}h</td>
                      <td className="py-2.5 pr-4 tabular-nums text-slate-600">{s.study_hours_per_day}h</td>
                      <td className={clsx('py-2.5 pr-4 font-semibold', s.parental_pressure >= 7 ? 'text-red-600' : 'text-slate-700')}>{s.parental_pressure}/10</td>
                      <td className="py-2.5 tabular-nums text-slate-600">{s.motivation_level}/10</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* RISK HISTORY TAB */}
          {activeTab === 'Risk History' && (
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-4">Risk Score Over Time</h3>
              {riskHistory.length === 0
                ? <p className="text-slate-400 text-sm text-center py-8">No risk history yet. Run a prediction to begin tracking.</p>
                : (
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart
                      data={riskHistory.map((r) => ({
                        date: format(parseISO(r.assessed_at), 'dd MMM'),
                        score: r.risk_score,
                        level: r.risk_level,
                      }))}
                      margin={{ top: 8, right: 16, bottom: 8, left: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
                      <Tooltip formatter={(v) => [`${v?.toFixed(1)} / 100`, 'Risk Score']} />
                      <Line type="monotone" dataKey="score" stroke="#7C3AED" strokeWidth={2.5}
                        dot={{ r: 4, fill: '#7C3AED', strokeWidth: 0 }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                )
              }
            </div>
          )}

          {/* ALERTS TAB */}
          {activeTab === 'Alerts' && (
            <div className="space-y-3">
              {alerts.length === 0
                ? <p className="text-slate-400 text-sm text-center py-8">No alerts for this student</p>
                : alerts.map((a) => (
                  <div key={a.id} className={clsx(
                    'rounded-xl border p-4',
                    a.is_resolved ? 'border-slate-100 bg-slate-50' : 'border-amber-100 bg-amber-50'
                  )}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <RiskBadge level={a.risk_level} size="sm" />
                        <p className="text-sm text-slate-700 mt-1.5">{a.message}</p>
                        <p className="text-xs text-slate-400 mt-1">{a.created_at ? format(parseISO(a.created_at), 'dd MMM yyyy HH:mm') : ''}</p>
                      </div>
                      {a.is_resolved && (
                        <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full shrink-0">Resolved</span>
                      )}
                    </div>
                  </div>
                ))
              }
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
