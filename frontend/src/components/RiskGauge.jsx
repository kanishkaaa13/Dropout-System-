import { RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts'

const COLORS = {
  Low:      '#10B981',
  Medium:   '#F59E0B',
  High:     '#EF4444',
  Critical: '#7C3AED',
}

const TRACK_COLOR = '#1E293B'

/**
 * RiskGauge — semicircular gauge built with Recharts RadialBarChart
 * @param {{ score: number, level: string, size?: number }} props
 */
export default function RiskGauge({ score = 0, level = 'Low', size = 200 }) {
  const color    = COLORS[level] || COLORS.Low
  const clampedScore = Math.min(100, Math.max(0, score))

  const data = [{ value: clampedScore, fill: color }]

  return (
    <div className="relative flex flex-col items-center" style={{ width: size }}>
      <RadialBarChart
        width={size}
        height={size * 0.6}
        innerRadius={size * 0.3}
        outerRadius={size * 0.46}
        data={data}
        startAngle={180}
        endAngle={0}
        barSize={size * 0.1}
      >
        {/* Track */}
        <RadialBar
          dataKey="value"
          background={{ fill: TRACK_COLOR }}
          cornerRadius={6}
          clockWise={false}
        />
        <PolarAngleAxis type="number" domain={[0, 100]} tick={false} axisLine={false} />
      </RadialBarChart>

      {/* Center label — overlaid absolutely */}
      <div
        className="absolute flex flex-col items-center"
        style={{ top: size * 0.28 }}
      >
        <span
          className="font-bold tabular-nums leading-none"
          style={{ fontSize: size * 0.18, color }}
        >
          {Math.round(clampedScore)}
        </span>
        <span className="text-xs text-slate-400 mt-0.5 font-medium tracking-wide uppercase">
          {level}
        </span>
      </div>

      {/* Min / Max labels */}
      <div
        className="flex justify-between w-full px-2 text-xs text-slate-500 font-medium"
        style={{ marginTop: -size * 0.05 }}
      >
        <span>0</span>
        <span className="text-slate-400 text-[10px]">RISK SCORE</span>
        <span>100</span>
      </div>
    </div>
  )
}
