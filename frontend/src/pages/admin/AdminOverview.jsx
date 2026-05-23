import { useEffect, useState } from 'react'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend,
} from 'recharts'
import api from '../../api/axiosConfig'
import RiskBadge from '../../components/RiskBadge'
import { Link } from 'react-router-dom'
import { Users, AlertTriangle, BellRing, TrendingUp } from 'lucide-react'
import clsx from 'clsx'

// ── Skeleton ─────────────────────────────────────────────────────────────────
const Skeleton = ({ className }) => (
  <div className={clsx('animate-pulse bg-slate-100 rounded-lg', className)} />
)

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, Icon, iconClass, loading }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 flex items-start gap-4">
      <div className={clsx('p-3 rounded-xl', iconClass)}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div className="min-w-0">
        {loading
          ? <Skeleton className="h-8 w-20 mb-1" />
          : <p className="text-2xl font-bold text-slate-800 tabular-nums">{value ?? '—'}</p>
        }
        <p className="text-sm text-slate-500 font-medium">{label}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

const RISK_COLORS = { Low: '#10B981', Medium: '#F59E0B', High: '#EF4444', Critical: '#7C3AED' }

const PieTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0]
  return (
    <div className="bg-slate-900 text-white text-sm rounded-lg px-3 py-2 shadow-xl">
      <p className="font-semibold">{d.name}</p>
      <p>{d.value} students ({d.payload.pct}%)</p>
    </div>
  )
}

export default function AdminOverview() {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState(null)

  useEffect(() => {
    api.get('/analytics/institute/overview')
      .then(({ data }) => setData(data))
      .catch(() => {
        // Fallback mock so the UI is always visible in dev
        setData({
          total_students: 20,
          high_risk_count: 6,
          unresolved_alerts: 5,
          avg_mock_score: 182.4,
          risk_distribution: [
            { level: 'Low', count: 14 },
            { level: 'Medium', count: 0 },
            { level: 'High', count: 1 },
            { level: 'Critical', count: 5 },
          ],
          top_at_risk: [],
          batch_comparison: [],
        })
        setError('Using mock data — backend not reachable')
      })
      .finally(() => setLoading(false))
  }, [])

  const riskDist = (data?.risk_distribution || []).map((r) => ({
    ...r,
    pct: data?.total_students
      ? Math.round((r.count / data.total_students) * 100)
      : 0,
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Institute Overview</h1>
        <p className="text-sm text-slate-500 mt-0.5">Real-time dropout risk dashboard</p>
      </div>

      {error && (
        <div className="rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-sm px-4 py-3">
          ⚠ {error}
        </div>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard label="Total Students"    value={data?.total_students}    Icon={Users}         iconClass="bg-blue-500"    loading={loading} />
        <StatCard label="High / Critical"   value={data?.high_risk_count}   Icon={AlertTriangle} iconClass="bg-red-500"     loading={loading} sub="students at risk" />
        <StatCard label="Unresolved Alerts" value={data?.unresolved_alerts} Icon={BellRing}      iconClass="bg-amber-500"   loading={loading} />
        <StatCard
          label="Avg Mock Score"
          value={data?.avg_mock_score ? `${data.avg_mock_score.toFixed(1)} / 360` : null}
          Icon={TrendingUp}
          iconClass="bg-emerald-500"
          loading={loading}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Risk Distribution Pie */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 lg:col-span-2">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">Risk Distribution</h2>
          {loading
            ? <Skeleton className="h-48" />
            : (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={riskDist}
                    dataKey="count"
                    nameKey="level"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                  >
                    {riskDist.map((d) => (
                      <Cell key={d.level} fill={RISK_COLORS[d.level]} />
                    ))}
                  </Pie>
                  <Tooltip content={<PieTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            )
          }
          <div className="flex flex-wrap gap-3 mt-3 justify-center">
            {riskDist.map((d) => (
              <span key={d.level} className="flex items-center gap-1.5 text-xs text-slate-600">
                <span className="size-2.5 rounded-full" style={{ background: RISK_COLORS[d.level] }} />
                {d.level} ({d.count})
              </span>
            ))}
          </div>
        </div>

        {/* Batch Comparison Bar */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 lg:col-span-3">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">Avg Risk Score by Batch</h2>
          {loading
            ? <Skeleton className="h-48" />
            : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={data?.batch_comparison || []} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="batch_name" tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
                  <Tooltip />
                  <Bar dataKey="avg_risk_score" name="Avg Risk" fill="#6366F1" radius={[4, 4, 0, 0]} maxBarSize={40} />
                </BarChart>
              </ResponsiveContainer>
            )
          }
        </div>
      </div>

      {/* Top at-risk students table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
        <h2 className="text-sm font-semibold text-slate-700 mb-4">Top At-Risk Students</h2>
        {loading
          ? <Skeleton className="h-48" />
          : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    {['Name', 'Code', 'Batch', 'Risk Level', 'Score', ''].map((h) => (
                      <th key={h} className="pb-3 text-left text-xs font-semibold text-slate-500 pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {(data?.top_at_risk || []).length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-400 text-sm">
                        No high-risk students detected
                      </td>
                    </tr>
                  )}
                  {(data?.top_at_risk || []).map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 pr-4 font-medium text-slate-800">{s.full_name}</td>
                      <td className="py-3 pr-4 text-slate-500 font-mono text-xs">{s.student_code}</td>
                      <td className="py-3 pr-4 text-slate-500">{s.batch_name || '—'}</td>
                      <td className="py-3 pr-4"><RiskBadge level={s.risk_level} /></td>
                      <td className="py-3 pr-4 tabular-nums font-semibold text-slate-700">
                        {s.risk_score?.toFixed(1)}
                      </td>
                      <td className="py-3">
                        <Link
                          to={`/students/${s.id}`}
                          className="text-indigo-600 hover:text-indigo-800 text-xs font-medium"
                        >
                          View →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        }
      </div>
    </div>
  )
}
