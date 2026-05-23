import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 shadow-xl text-sm max-w-xs">
      <p className="font-semibold text-white mb-1">{d.human_label}</p>
      <div className="space-y-0.5 text-slate-300">
        <p>Actual value: <span className="text-white font-medium">{d.actual_value}</span></p>
        <p>
          SHAP contribution:
          <span className={`font-medium ml-1 ${d.shap_value >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
            {d.shap_value >= 0 ? '+' : ''}{d.shap_value.toFixed(3)}
          </span>
        </p>
        <p className="text-xs text-slate-400 mt-1">
          {d.direction === 'increases_risk' ? '⬆ Increases dropout risk' : '⬇ Decreases dropout risk'}
        </p>
      </div>
    </div>
  )
}

/**
 * ShapChart — horizontal bar chart of SHAP feature impacts
 * @param {{ impacts: Array<{feature, human_label, shap_value, actual_value, direction}> }} props
 */
export default function ShapChart({ impacts = [] }) {
  if (!impacts.length) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
        No SHAP explanation available
      </div>
    )
  }

  // Sort by absolute SHAP value descending, take top 10
  const sorted = [...impacts]
    .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
    .slice(0, 10)
    .reverse() // highest at top in horizontal bar

  const chartH = Math.max(220, sorted.length * 36)

  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
        <span className="inline-block w-3 h-3 rounded-sm bg-red-400" />
        Why is this student at risk?
      </h3>

      <div className="flex gap-3 text-xs text-slate-500 mb-3">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-2 rounded-sm bg-red-400 opacity-80" /> Increases risk
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-2 rounded-sm bg-emerald-400 opacity-80" /> Decreases risk
        </span>
      </div>

      <ResponsiveContainer width="100%" height={chartH}>
        <BarChart
          data={sorted}
          layout="vertical"
          margin={{ top: 4, right: 24, bottom: 4, left: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
          <XAxis
            type="number"
            tick={{ fontSize: 11, fill: '#94A3B8' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => v.toFixed(2)}
          />
          <YAxis
            type="category"
            dataKey="human_label"
            width={160}
            tick={{ fontSize: 11, fill: '#475569' }}
            axisLine={false}
            tickLine={false}
          />
          <ReferenceLine x={0} stroke="#94A3B8" strokeWidth={1} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#F1F5F9' }} />
          <Bar dataKey="shap_value" radius={[0, 3, 3, 0]} maxBarSize={20}>
            {sorted.map((entry, idx) => (
              <Cell
                key={idx}
                fill={entry.direction === 'increases_risk' ? '#F87171' : '#34D399'}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
