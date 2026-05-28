import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function SHAPBarChart({ shapData }) {
  if (!shapData || shapData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No SHAP data available
      </div>
    )
  }

  // Transform SHAP data for Recharts
  const chartData = shapData.map((item, index) => ({
    name: item.feature || `Feature ${index + 1}`,
    value: item.impact || item.shap_value || 0,
    original: item
  }))

  // Sort by absolute impact for better visualization
  chartData.sort((a, b) => Math.abs(b.value) - Math.abs(a.value))

  // Color based on positive/negative impact
  const getBarColor = (value) => {
    return value >= 0 ? '#10b981' : '#ef4444' // green for positive, red for negative
  }

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="horizontal"
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" tick={{ fontSize: 12 }} />
          <YAxis 
            type="category" 
            dataKey="name" 
            tick={{ fontSize: 11 }}
            width={120}
          />
          <Tooltip
            formatter={(value) => [value.toFixed(4), 'SHAP Value']}
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.value)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
