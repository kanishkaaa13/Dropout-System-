import { useState, useEffect } from 'react'
import { ArrowUpDown, AlertTriangle, Shield, TrendingUp, Download, Upload } from 'lucide-react'
import api from '../../api/axiosConfig'

export default function StudentRiskDashboard() {
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [sortConfig, setSortConfig] = useState({ key: 'risk_score', direction: 'desc' })
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    fetchStudents()
  }, [])

  const fetchStudents = async () => {
    try {
      const response = await api.get('/students')
      setStudents(response.data)
    } catch (error) {
      console.error('Failed to fetch students:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSort = (key) => {
    let direction = 'asc'
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }
    setSortConfig({ key, direction })
  }

  const sortedStudents = [...students].sort((a, b) => {
    if (a[sortConfig.key] < b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? -1 : 1
    }
    if (a[sortConfig.key] > b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? 1 : -1
    }
    return 0
  })

  const filteredStudents = sortedStudents.filter(student => {
    if (filter === 'all') return true
    return student.risk_level === filter
  })

  const getRiskBadge = (riskLevel, riskScore) => {
    const colors = {
      Critical: 'bg-red-100 text-red-800 border-red-300',
      High: 'bg-orange-100 text-orange-800 border-orange-300',
      Medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      Low: 'bg-green-100 text-green-800 border-green-300',
    }
    const icons = {
      Critical: <AlertTriangle className="w-4 h-4" />,
      High: <AlertTriangle className="w-4 h-4" />,
      Medium: <TrendingUp className="w-4 h-4" />,
      Low: <Shield className="w-4 h-4" />,
    }
    
    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${colors[riskLevel] || colors.Low}`}>
        {icons[riskLevel] || icons.Low}
        {riskLevel} ({riskScore?.toFixed(1) || 0})
      </span>
    )
  }

  const getProbabilityColor = (probability) => {
    if (probability >= 0.7) return 'bg-red-500'
    if (probability >= 0.5) return 'bg-orange-500'
    if (probability >= 0.3) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Student Risk Dashboard</h1>
          <p className="text-gray-600 mt-1">Monitor and manage student dropout risk levels</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition">
            <Upload className="w-4 h-4" />
            Bulk Upload CSV
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            <Download className="w-4 h-4" />
            Export Data
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {['Critical', 'High', 'Medium', 'Low'].map(level => (
          <div key={level} className="bg-white rounded-lg shadow p-4 border-l-4 border-l-red-500">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-medium text-gray-600">{level} Risk</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {students.filter(s => s.risk_level === level).length}
                </p>
              </div>
              {level === 'Critical' && <AlertTriangle className="w-5 h-5 text-red-500" />}
              {level === 'High' && <AlertTriangle className="w-5 h-5 text-orange-500" />}
              {level === 'Medium' && <TrendingUp className="w-5 h-5 text-yellow-500" />}
              {level === 'Low' && <Shield className="w-5 h-5 text-green-500" />}
            </div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        {['all', 'Critical', 'High', 'Medium', 'Low'].map(level => (
          <button
            key={level}
            onClick={() => setFilter(level)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              filter === level
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            {level.charAt(0).toUpperCase() + level.slice(1)}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {[
                { key: 'full_name', label: 'Student Name' },
                { key: 'email', label: 'Email' },
                { key: 'batch_name', label: 'Batch' },
                { key: 'risk_score', label: 'Risk Score' },
                { key: 'risk_level', label: 'Risk Level' },
                { key: 'ml_probability', label: 'Dropout Probability' },
                { key: 'last_assessment', label: 'Last Assessment' },
              ].map(({ key, label }) => (
                <th
                  key={key}
                  onClick={() => handleSort(key)}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition"
                >
                  <div className="flex items-center gap-1">
                    {label}
                    {sortConfig.key === key && (
                      <ArrowUpDown className="w-4 h-4" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredStudents.map((student) => (
              <tr key={student.id} className="hover:bg-gray-50 transition">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{student.full_name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">{student.email}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">{student.batch_name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{student.risk_score?.toFixed(1) || 0}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getRiskBadge(student.risk_level, student.risk_score)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getProbabilityColor(student.ml_probability)}`}
                        style={{ width: `${(student.ml_probability || 0) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600">{((student.ml_probability || 0) * 100).toFixed(1)}%</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {student.last_assessment ? new Date(student.last_assessment).toLocaleDateString() : 'N/A'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
