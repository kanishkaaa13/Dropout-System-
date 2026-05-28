import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import api from '../../api/axiosConfig'
import RiskBadge from '../../components/RiskBadge'
import CreativePlanner from '../../components/CreativePlanner'
import ExplanationCard from '../../components/ExplanationCard'
import InterventionPanel from '../../components/InterventionPanel'
import { TrendingUp, TrendingDown, Activity, Clock, Target, Award, LayoutDashboard, BookOpen } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function StudentDashboard() {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState(null)
  const [error, setError] = useState(null)
  const [shapFeatures, setShapFeatures] = useState([])
  const [activeView, setActiveView] = useState('dashboard') // 'dashboard' or 'planner'

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await api.get('/students/me/dashboard')
      setDashboardData(response.data)
      
      // Fetch SHAP features for chat context
      try {
        const shapResponse = await api.get('/predict/explain/me')
        if (shapResponse.data) {
          setShapFeatures(shapResponse.data.top_factors?.map(f => f.feature) || [])
        }
      } catch (shapErr) {
        console.warn('SHAP data unavailable:', shapErr.message)
        // Set default SHAP features
        setShapFeatures(['attendance_rate', 'mock_test_avg', 'burnout_score'])
      }
    } catch (err) {
      console.warn('Backend dashboard API unavailable, using mock data:', err.message)
      setError(err.message)
      // Fallback to mock data
      setDashboardData(getMockDashboardData())
      setShapFeatures(['attendance_rate', 'mock_test_avg', 'burnout_score'])
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
    risk_score: 55,
    attendance_rate: 85,
    assignment_completion: 78,
    weekly_study_target: 40,
    weekly_study_actual: 35,
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
    score_trend_data: [
      { name: 'Mock 1', physics: 58, chemistry: 52, maths: 65 },
      { name: 'Mock 2', physics: 62, chemistry: 55, maths: 68 },
      { name: 'Mock 3', physics: 60, chemistry: 58, maths: 72 },
      { name: 'Mock 4', physics: 65, chemistry: 62, maths: 69 },
      { name: 'Mock 5', physics: 62, chemistry: 58, maths: 71 },
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

  // Prepare student data for chat panel (removed - now separate page)
  // const studentDataForChat = {
  //   full_name: data.student_name,
  //   risk_score: data.risk_score,
  //   risk_level: data.risk_level
  // }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">
              Welcome back, {data.student_name}
            </h1>
            <p className="text-gray-500 mt-1">
              {data.registration_code} • {data.batch}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* View Toggle Buttons */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setActiveView('dashboard')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all ${
                  activeView === 'dashboard'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </button>
              <button
                onClick={() => setActiveView('planner')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all ${
                  activeView === 'planner'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <BookOpen className="w-4 h-4" />
                Planner
              </button>
            </div>
            {error && (
              <div className="text-xs text-amber-600 bg-amber-50 px-3 py-1.5 rounded-full">
                Using offline mode
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Conditional Rendering based on active view */}
      {activeView === 'dashboard' ? (
        <>
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
            <div className="bg-white rounded-xl shadow-sm p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium text-gray-600">Risk Profile</p>
                <Activity className="w-5 h-5 text-gray-400" />
              </div>
              <div className="flex items-center justify-between">
                <RiskBadge level={data.risk_level} size="lg" showLabel />
              </div>
            </div>

            {/* Engagement Metrics */}
            <div className="bg-white rounded-xl shadow-sm p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium text-gray-600">Engagement</p>
                <Clock className="w-5 h-5 text-gray-400" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Attendance</span>
                  <span className="font-medium text-gray-900">{data.attendance_rate}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Assignments</span>
                  <span className="font-medium text-gray-900">{data.assignment_completion}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Weekly Goal Card */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-[#6B5CE7]" />
                Weekly Study Goal
              </h2>
              <span className="text-sm text-gray-500">
                {data.weekly_study_actual} / {data.weekly_study_target} hours
              </span>
            </div>
            <div className="relative h-4 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="absolute top-0 left-0 h-full bg-[#6B5CE7] rounded-full transition-all duration-500"
                style={{ width: `${(data.weekly_study_actual / data.weekly_study_target) * 100}%` }}
              />
            </div>
            <p className="text-sm text-gray-500 mt-2">
              {data.weekly_study_actual >= data.weekly_study_target 
                ? "🎉 You've met your weekly study goal!" 
                : `Keep going! ${data.weekly_study_target - data.weekly_study_actual} more hours to reach your goal.`}
            </p>
          </div>

          {/* Academic Analytics */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Academic Analytics</h2>
            
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
              <h3 className="text-sm font-medium text-gray-600 mb-3">Score Trend</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <ScoreTrendChart data={data.score_trend_data} />
              </div>
            </div>
          </div>

          {/* SHAP Explanation Card */}
          <ExplanationCard studentId={user?.id} />

          {/* AI Intervention Panel */}
          <InterventionPanel
            studentId={user?.id}
            riskFactors={data}
            riskScore={data.risk_score}
            riskLevel={data.risk_level}
          />

          {/* Stress & Wellness Index */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Stress & Wellness Index</h2>
            
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
        </>
      ) : (
        /* Creative Planner View */
        <CreativePlanner />
      )}
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

  const colorClasses = {
    green: 'text-emerald-500',
    red: 'text-red-500',
    blue: 'text-blue-500'
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <div className={colorClasses[color] || 'text-gray-500'}>{icon}</div>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
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
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-2 h-2 rounded-full ${subjectColors[subject.toLowerCase()]}`} />
        <p className="text-sm font-medium text-gray-900 capitalize">{subject}</p>
        {trendIcon}
      </div>
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Score</span>
          <span className="font-medium text-gray-900">{score}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Mock</span>
          <span className="font-medium text-gray-900">{mockScore}/120</span>
        </div>
      </div>
    </div>
  )
}

function WellnessMetric({ label, value, max, type, color }) {
  if (type === 'ratio') {
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <p className="text-sm font-medium text-gray-600 mb-2">{label}</p>
        <p className="text-lg font-semibold text-gray-900">{value}</p>
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
    <div className="bg-gray-50 rounded-lg p-4">
      <p className="text-sm font-medium text-gray-600 mb-2">{label}</p>
      <div className="flex items-center gap-3">
        <div className="flex-1 bg-gray-200 rounded-full h-2">
          <div
            className={`${colorClasses[color]} h-2 rounded-full transition-all`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className="text-sm font-semibold text-gray-900">{value}/{max}</span>
      </div>
    </div>
  )
}

function ScoreTrendChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
        <YAxis stroke="#6b7280" fontSize={12} />
        <Tooltip 
          contentStyle={{ 
            backgroundColor: '#1f2937', 
            border: 'none', 
            borderRadius: '8px',
            color: '#fff'
          }}
        />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="physics" 
          stroke="#378ADD" 
          strokeWidth={2}
          dot={{ fill: '#378ADD', strokeWidth: 2, r: 4 }}
          name="Physics"
        />
        <Line 
          type="monotone" 
          dataKey="chemistry" 
          stroke="#D85A30" 
          strokeWidth={2}
          dot={{ fill: '#D85A30', strokeWidth: 2, r: 4 }}
          name="Chemistry"
        />
        <Line 
          type="monotone" 
          dataKey="maths" 
          stroke="#3B6D11" 
          strokeWidth={2}
          dot={{ fill: '#3B6D11', strokeWidth: 2, r: 4 }}
          name="Maths"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
