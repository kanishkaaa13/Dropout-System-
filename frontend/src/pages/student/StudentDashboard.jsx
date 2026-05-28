import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import api from '../../api/axiosConfig'
import RiskBadge from '../../components/RiskBadge'
import { TrendingUp, TrendingDown, Activity, Clock, Target, Award } from 'lucide-react'

export default function StudentDashboard() {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await api.get('/students/me/dashboard')
      setDashboardData(response.data)
    } catch (err) {
      console.warn('Backend dashboard API unavailable, using mock data:', err.message)
      setError(err.message)
      // Fallback to mock data
      setDashboardData(getMockDashboardData())
    } finally {
      setLoading(false)
    }
  }

  const getMockDashboardData = () => ({
    student_name: user?.full_name || 'Ananya Singh',
    registration_code: 'JEE2025_004',
    batch: 'Batch A - 2025',
    predicted_rank: 939,
    target_rank: 500,
    mock_average: 180,
    mock_total: 360,
    risk_level: 'Medium',
    attendance_rate: 85,
    assignment_completion: 78,
    subjects: {
      physics: { score: 62, trend: 'up', mock_score: 112 },
      chemistry: { score: 58, trend: 'down', mock_score: 105 },
      mathematics: { score: 71, trend: 'up', mock_score: 128 }
    },
    wellness: {
      burnout_score: 6,
      stress_level: 7,
      sleep_hours: 5.5,
      study_hours: 10,
      peer_pressure: 5
    },
    score_history: [
      { test: 'Mock 1', score: 165 },
      { test: 'Mock 2', score: 172 },
      { test: 'Mock 3', score: 158 },
      { test: 'Mock 4', score: 180 },
      { test: 'Mock 5', score: 175 }
    ]
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  const data = dashboardData || getMockDashboardData()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              Welcome back, {data.student_name}
            </h1>
            <p className="text-slate-500 mt-1">
              {data.registration_code} • {data.batch}
            </p>
          </div>
          {error && (
            <div className="text-xs text-amber-600 bg-amber-50 px-3 py-1.5 rounded-full">
              Using offline mode
            </div>
          )}
        </div>
      </div>

      {/* Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Predicted Rank */}
        <MetricCard
          title="Predicted Rank"
          value={data.predicted_rank}
          subtitle={`Target: Top ${data.target_rank}`}
          icon={<Target className="w-5 h-5" />}
          trend={data.predicted_rank <= data.target_rank ? 'up' : 'down'}
          color={data.predicted_rank <= data.target_rank ? 'green' : 'red'}
        />

        {/* Mock Test Average */}
        <MetricCard
          title="Mock Test Average"
          value={`${data.mock_average} / ${data.mock_total}`}
          subtitle="Last 5 tests"
          icon={<Award className="w-5 h-5" />}
          trend="neutral"
          color="blue"
        />

        {/* Risk Profile */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium text-slate-600">Risk Profile</p>
            <Activity className="w-5 h-5 text-slate-400" />
          </div>
          <div className="flex items-center justify-between">
            <RiskBadge level={data.risk_level} size="lg" showLabel />
          </div>
        </div>

        {/* Engagement Metrics */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium text-slate-600">Engagement</p>
            <Clock className="w-5 h-5 text-slate-400" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Attendance</span>
              <span className="font-medium text-slate-900">{data.attendance_rate}%</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Assignments</span>
              <span className="font-medium text-slate-900">{data.assignment_completion}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Academic Analytics */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-6">Academic Analytics</h2>
        
        {/* Subject Health */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {Object.entries(data.subjects).map(([subject, info]) => (
            <SubjectCard
              key={subject}
              subject={subject}
              score={info.score}
              trend={info.trend}
              mockScore={info.mock_score}
            />
          ))}
        </div>

        {/* Score Trend */}
        <div>
          <h3 className="text-sm font-medium text-slate-600 mb-3">Score Trend</h3>
          <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
            <ScoreTrendPlaceholder data={data.score_history} />
          </div>
        </div>
      </div>

      {/* Stress & Wellness Index */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-6">Stress & Wellness Index</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <WellnessMetric
            label="Burnout Score"
            value={data.wellness.burnout_score}
            max={10}
            color="red"
          />
          <WellnessMetric
            label="Stress Level"
            value={data.wellness.stress_level}
            max={10}
            color="amber"
          />
          <WellnessMetric
            label="Sleep vs Study"
            value={`${data.wellness.sleep_hours}h / ${data.wellness.study_hours}h`}
            type="ratio"
          />
          <WellnessMetric
            label="Peer Pressure"
            value={data.wellness.peer_pressure}
            max={10}
            color="purple"
          />
        </div>
      </div>
    </div>
  )
}

// Sub-components

function MetricCard({ title, value, subtitle, icon, trend, color }) {
  const trendIcon = trend === 'up' ? (
    <TrendingUp className="w-4 h-4 text-emerald-500" />
  ) : trend === 'down' ? (
    <TrendingDown className="w-4 h-4 text-red-500" />
  ) : null

  return (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-slate-600">{title}</p>
        <div className={`text-${color}-500`}>{icon}</div>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-2xl font-bold text-slate-900">{value}</p>
          <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
        </div>
        {trendIcon}
      </div>
    </div>
  )
}

function SubjectCard({ subject, score, trend, mockScore }) {
  const subjectColors = {
    physics: 'bg-blue-500',
    chemistry: 'bg-green-500',
    mathematics: 'bg-purple-500'
  }

  const trendIcon = trend === 'up' ? (
    <TrendingUp className="w-4 h-4 text-emerald-500" />
  ) : (
    <TrendingDown className="w-4 h-4 text-red-500" />
  )

  return (
    <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-2 h-2 rounded-full ${subjectColors[subject.toLowerCase()]}`} />
        <p className="text-sm font-medium text-slate-900 capitalize">{subject}</p>
        {trendIcon}
      </div>
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-slate-500">Score</span>
          <span className="font-medium text-slate-900">{score}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-500">Mock</span>
          <span className="font-medium text-slate-900">{mockScore}/120</span>
        </div>
      </div>
    </div>
  )
}

function WellnessMetric({ label, value, max, type, color }) {
  if (type === 'ratio') {
    return (
      <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
        <p className="text-sm font-medium text-slate-600 mb-2">{label}</p>
        <p className="text-lg font-bold text-slate-900">{value}</p>
      </div>
    )
  }

  const percentage = (value / max) * 100
  const colorClasses = {
    red: 'bg-red-500',
    amber: 'bg-amber-500',
    purple: 'bg-purple-500'
  }

  return (
    <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
      <p className="text-sm font-medium text-slate-600 mb-2">{label}</p>
      <div className="flex items-center gap-3">
        <div className="flex-1 bg-slate-200 rounded-full h-2">
          <div
            className={`${colorClasses[color]} h-2 rounded-full transition-all`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className="text-sm font-bold text-slate-900">{value}/{max}</span>
      </div>
    </div>
  )
}

function ScoreTrendPlaceholder({ data }) {
  const maxScore = Math.max(...data.map(d => d.score))
  const minScore = Math.min(...data.map(d => d.score))
  const range = maxScore - minScore || 1

  return (
    <div className="flex items-end justify-between h-32 gap-2">
      {data.map((point, index) => {
        const height = ((point.score - minScore) / range) * 80 + 20
        return (
          <div key={index} className="flex-1 flex flex-col items-center gap-2">
            <div
              className="w-full bg-indigo-500 rounded-t transition-all hover:bg-indigo-600"
              style={{ height: `${height}%` }}
            />
            <span className="text-xs text-slate-500">{point.test}</span>
          </div>
        )
      })}
    </div>
  )
}
