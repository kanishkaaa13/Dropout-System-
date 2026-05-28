import clsx from 'clsx'

const CONFIG = {
  Low:      { dot: 'bg-emerald-400', badge: 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 ring-emerald-200 dark:ring-emerald-800',  label: 'Low Risk'      },
  Medium:   { dot: 'bg-amber-400',   badge: 'bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 ring-amber-200 dark:ring-amber-800',       label: 'Medium Risk'   },
  High:     { dot: 'bg-red-400',     badge: 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 ring-red-200 dark:ring-red-800',          label: 'High Risk'     },
  Critical: { dot: 'bg-red-600',     badge: 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300 ring-red-300 dark:ring-red-800',          label: 'Critical Risk' },
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
