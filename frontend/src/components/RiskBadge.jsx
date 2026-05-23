import clsx from 'clsx'

const CONFIG = {
  Low:      { dot: 'bg-emerald-400', badge: 'bg-emerald-50 text-emerald-700 ring-emerald-200',  label: 'Low Risk'      },
  Medium:   { dot: 'bg-amber-400',   badge: 'bg-amber-50  text-amber-700  ring-amber-200',       label: 'Medium Risk'   },
  High:     { dot: 'bg-red-400',     badge: 'bg-red-50    text-red-700    ring-red-200',          label: 'High Risk'     },
  Critical: { dot: 'bg-purple-500',  badge: 'bg-purple-50 text-purple-700 ring-purple-200',      label: 'Critical Risk' },
}

/**
 * RiskBadge
 * @param {{ level: 'Low'|'Medium'|'High'|'Critical', size?: 'sm'|'md'|'lg', showLabel?: boolean }} props
 */
export default function RiskBadge({ level, size = 'md', showLabel = false }) {
  const cfg = CONFIG[level] || CONFIG.Low
  const sizeClass = {
    sm: 'px-2 py-0.5 text-xs gap-1',
    md: 'px-2.5 py-1 text-sm gap-1.5',
    lg: 'px-3 py-1.5 text-base gap-2',
  }[size]
  const dotSize = { sm: 'size-1.5', md: 'size-2', lg: 'size-2.5' }[size]

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full font-medium ring-1 ring-inset',
        cfg.badge,
        sizeClass
      )}
    >
      <span className={clsx('rounded-full animate-pulse', cfg.dot, dotSize)} />
      {showLabel ? cfg.label : level}
    </span>
  )
}
