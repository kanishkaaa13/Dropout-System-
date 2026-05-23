import { useEffect, useState, useCallback } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import api from '../../api/axiosConfig'
import RiskBadge from '../../components/RiskBadge'
import clsx from 'clsx'
import { Search, ChevronLeft, ChevronRight, UserPlus } from 'lucide-react'

const Skeleton = ({ className }) => (
  <div className={clsx('animate-pulse bg-slate-100 rounded', className)} />
)

const RISK_LEVELS = ['', 'Low', 'Medium', 'High', 'Critical']

export default function StudentList({ facultyOnly = false }) {
  const [students, setStudents]   = useState([])
  const [total, setTotal]         = useState(0)
  const [pages, setPages]         = useState(1)
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate                  = useNavigate()

  const page      = parseInt(searchParams.get('page') || '1', 10)
  const search    = searchParams.get('search') || ''
  const riskLevel = searchParams.get('risk_level') || ''

  const fetchStudents = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, size: 20, ...(search && { search }), ...(riskLevel && { risk_level: riskLevel }) }
      const { data } = await api.get('/students', { params })
      setStudents(data.items)
      setTotal(data.total)
      setPages(data.pages)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load students')
    } finally {
      setLoading(false)
    }
  }, [page, search, riskLevel])

  useEffect(() => { fetchStudents() }, [fetchStudents])

  const setParam = (key, value) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value); else next.delete(key)
    if (key !== 'page') next.delete('page')
    setSearchParams(next)
  }

  const basePath = facultyOnly ? '/faculty/students' : '/students'

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <div className="flex-1">
          <h1 className="text-xl font-bold text-slate-900">
            {facultyOnly ? 'My Students' : 'All Students'}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">{total} students total</p>
        </div>
        {!facultyOnly && (
          <button
            onClick={() => navigate('/admin/students/new')}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition-colors"
          >
            <UserPlus className="w-4 h-4" />
            Add Student
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by name or code…"
            value={search}
            onChange={(e) => setParam('search', e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          />
        </div>
        <select
          value={riskLevel}
          onChange={(e) => setParam('risk_level', e.target.value)}
          className="border border-slate-200 rounded-xl px-4 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-700"
        >
          {RISK_LEVELS.map((l) => (
            <option key={l} value={l}>{l || 'All Risk Levels'}</option>
          ))}
        </select>
      </div>

      {error && (
        <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">{error}</div>
      )}

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>
                {['Student', 'Code', 'Batch', 'Risk Level', 'Score', 'Target', ''].map((h) => (
                  <th key={h} className="px-5 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {loading
                ? Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 7 }).map((_, j) => (
                        <td key={j} className="px-5 py-3.5">
                          <Skeleton className="h-4 w-full" />
                        </td>
                      ))}
                    </tr>
                  ))
                : students.length === 0
                  ? (
                    <tr>
                      <td colSpan={7} className="px-5 py-12 text-center text-slate-400 text-sm">
                        No students found
                      </td>
                    </tr>
                  )
                  : students.map((s) => (
                    <tr
                      key={s.id}
                      className="hover:bg-slate-50 transition-colors cursor-pointer"
                      onClick={() => navigate(`${basePath}/${s.id}`)}
                    >
                      <td className="px-5 py-3.5">
                        <div>
                          <p className="font-semibold text-slate-800">{s.full_name}</p>
                          <p className="text-xs text-slate-400">{s.email}</p>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 font-mono text-xs text-slate-500">{s.student_code || '—'}</td>
                      <td className="px-5 py-3.5 text-slate-500">{s.batch_id ? `Batch ${s.batch_id}` : '—'}</td>
                      <td className="px-5 py-3.5">
                        {s.latest_risk?.risk_level
                          ? <RiskBadge level={s.latest_risk.risk_level} />
                          : <span className="text-slate-300 text-xs">No data</span>
                        }
                      </td>
                      <td className="px-5 py-3.5 tabular-nums font-semibold text-slate-700">
                        {s.latest_risk?.risk_score?.toFixed(1) ?? '—'}
                      </td>
                      <td className="px-5 py-3.5 text-slate-500">
                        {s.target_rank ? `Rank ${s.target_rank.toLocaleString()}` : '—'}
                      </td>
                      <td className="px-5 py-3.5">
                        <Link
                          to={`${basePath}/${s.id}`}
                          className="text-indigo-600 hover:text-indigo-800 font-medium text-xs"
                          onClick={(e) => e.stopPropagation()}
                        >
                          View →
                        </Link>
                      </td>
                    </tr>
                  ))
              }
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex items-center justify-between px-5 py-4 border-t border-slate-100">
            <p className="text-sm text-slate-500">
              Page {page} of {pages} · {total} students
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setParam('page', String(page - 1))}
                disabled={page <= 1}
                className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4 text-slate-600" />
              </button>
              <button
                onClick={() => setParam('page', String(page + 1))}
                disabled={page >= pages}
                className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-4 h-4 text-slate-600" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
