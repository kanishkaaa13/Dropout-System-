export default function SkeletonLoader({ className = '' }) {
  return (
    <div className={`animate-pulse bg-gray-200 dark:bg-gray-700 rounded ${className}`} />
  )
}

export function CardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6 transition-colors duration-200">
      <div className="flex items-center justify-between mb-4">
        <SkeletonLoader className="h-5 w-32" />
        <SkeletonLoader className="h-5 w-5 rounded-full" />
      </div>
      <SkeletonLoader className="h-8 w-24 mb-4" />
      <SkeletonLoader className="h-4 w-full" />
    </div>
  )
}

export function MetricCardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-5 transition-colors duration-200">
      <div className="flex items-center justify-between mb-3">
        <SkeletonLoader className="h-4 w-24" />
        <SkeletonLoader className="h-5 w-5 rounded-full" />
      </div>
      <SkeletonLoader className="h-8 w-20 mb-2" />
      <SkeletonLoader className="h-3 w-16" />
    </div>
  )
}

export function TableSkeleton({ rows = 5 }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden transition-colors duration-200">
      <div className="p-4 border-b border-gray-200 dark:border-gray-800">
        <SkeletonLoader className="h-5 w-32" />
      </div>
      <div className="divide-y divide-gray-200 dark:divide-gray-800">
        {[...Array(rows)].map((_, i) => (
          <div key={i} className="p-4 flex items-center gap-4">
            <SkeletonLoader className="h-10 w-10 rounded-full" />
            <SkeletonLoader className="h-4 w-32" />
            <SkeletonLoader className="h-4 w-24" />
            <SkeletonLoader className="h-4 w-20" />
            <SkeletonLoader className="h-6 w-16 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  )
}
