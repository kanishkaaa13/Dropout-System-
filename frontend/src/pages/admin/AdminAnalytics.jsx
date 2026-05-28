import { LineChart, Line, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function AdminAnalytics() {
  // Mock data for charts
  const riskTrendData = [
    { month: 'Jan', riskScore: 45 },
    { month: 'Feb', riskScore: 48 },
    { month: 'Mar', riskScore: 52 },
    { month: 'Apr', riskScore: 50 },
    { month: 'May', riskScore: 55 },
    { month: 'Jun', riskScore: 53 },
  ]

  const subjectScoreData = [
    { subject: 'Physics', avgScore: 65 },
    { subject: 'Chemistry', avgScore: 58 },
    { subject: 'Mathematics', avgScore: 72 },
  ]

  const batchRiskData = [
    { batch: 'Batch A', avgRisk: 42 },
    { batch: 'Batch B', avgRisk: 48 },
    { batch: 'Batch C', avgRisk: 55 },
    { batch: 'Batch D', avgRisk: 38 },
  ]

  const stressPerformanceData = [
    { stress: 3, performance: 85 },
    { stress: 4, performance: 82 },
    { stress: 5, performance: 78 },
    { stress: 6, performance: 72 },
    { stress: 7, performance: 65 },
    { stress: 8, performance: 58 },
    { stress: 9, performance: 50 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-500 mt-1">Comprehensive insights into student performance and risk factors</p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Dropout Risk Trend */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Dropout Risk Trend Over Time</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={riskTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
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
                dataKey="riskScore" 
                stroke="#6B5CE7" 
                strokeWidth={2}
                dot={{ fill: '#6B5CE7', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Subject Score Distribution */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Subject Score Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={subjectScoreData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="subject" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1f2937', 
                  border: 'none', 
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Legend />
              <Bar dataKey="avgScore" fill="#6B5CE7" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Batch-wise Average Risk */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Batch-wise Average Risk</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={batchRiskData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="batch" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1f2937', 
                  border: 'none', 
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Legend />
              <Bar dataKey="avgRisk" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Stress vs Performance Scatter */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Stress vs Performance Correlation</h2>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart data={stressPerformanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                type="number" 
                dataKey="stress" 
                name="Stress Level" 
                stroke="#6b7280"
                label={{ value: 'Stress Level', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                type="number" 
                dataKey="performance" 
                name="Performance Score" 
                stroke="#6b7280"
                label={{ value: 'Performance', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{ 
                  backgroundColor: '#1f2937', 
                  border: 'none', 
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Scatter fill="#6B5CE7" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
