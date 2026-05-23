import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts'
import { format, parseISO } from 'date-fns'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 shadow-xl text-sm">
      <p className="text-slate-400 text-xs mb-2">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }} className="font-medium">
          {p.name}: <span className="text-white">{p.value?.toFixed(1)}</span>
        </p>
      ))}
    </div>
  )
}

/**
 * ScoreTrendChart
 * @param {{
 *   mockResults: Array<{test_name, test_date, total_score, physics_score, chemistry_score, maths_score}>,
 *   showSubjects?: boolean
 * }} props
 */
export default function ScoreTrendChart({ mockResults = [], showSubjects = false }) {
  if (!mockResults.length) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
        No mock test data available
      </div>
    )
  }

  const data = mockResults.map((r) => ({
    name: r.test_name || format(parseISO(r.test_date), 'dd MMM'),
    total:   r.total_score,
    physics:    r.physics_score,
    chemistry:  r.chemistry_score,
    maths:      r.maths_score,
  }))

  const avg = data.reduce((s, d) => s + (d.total || 0), 0) / data.length

  // Determine trend color
  const first = data[0]?.total || 0
  const last  = data[data.length - 1]?.total || 0
  const trendColor = last >= first ? '#10B981' : '#EF4444'

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 11, fill: '#94A3B8' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 360]}
          tick={{ fontSize: 11, fill: '#94A3B8' }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        {showSubjects && <Legend iconType="circle" iconSize={8} />}

        {/* Average reference line */}
        <ReferenceLine
          y={avg}
          stroke="#94A3B8"
          strokeDasharray="5 3"
          label={{ value: `Avg ${avg.toFixed(0)}`, fill: '#94A3B8', fontSize: 10, position: 'insideTopRight' }}
        />

        {showSubjects ? (
          <>
            <Line type="monotone" dataKey="physics"   name="Physics"   stroke="#6366F1" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="chemistry" name="Chemistry" stroke="#EC4899" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="maths"     name="Maths"     stroke="#F59E0B" strokeWidth={2} dot={false} />
          </>
        ) : (
          <Line
            type="monotone"
            dataKey="total"
            name="Total Score"
            stroke={trendColor}
            strokeWidth={2.5}
            dot={{ r: 4, fill: trendColor, strokeWidth: 0 }}
            activeDot={{ r: 6 }}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  )
}
