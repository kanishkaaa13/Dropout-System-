import { useState, useEffect } from 'react'
import { Info, TrendingUp, TrendingDown } from 'lucide-react'
import api from '../api/axiosConfig'

export default function ExplanationCard({ studentId }) {
  const [explanation, setExplanation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchExplanation = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get(`/predict/students/${studentId}/explanation`)
      setExplanation(response.data)
    } catch (err) {
      setError('Failed to load explanation')
      console.error('Error fetching explanation:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (studentId) {
      fetchExplanation()
    }
  }, [studentId])

  const getFeatureTooltip = (feature) => {
    const tooltips = {
      attendance_rate: 'Percentage of classes attended',
      mock_test_avg: 'Average score across mock tests',
      physics_score: 'Performance in Physics subject',
      chemistry_score: 'Performance in Chemistry subject',
      maths_score: 'Performance in Mathematics subject',
      mock_score_trend: 'Trend in mock test scores over time',
      assignment_completion_rate: 'Percentage of assignments completed',
      dpp_accuracy: 'Accuracy in Daily Practice Problems',
      test_attempt_rate: 'Percentage of tests attempted',
      burnout_score: 'Level of academic burnout (1-10)',
      stress_level: 'Self-reported stress level (1-10)',
      sleep_hours_avg: 'Average hours of sleep per day',
      study_hours_per_day: 'Average study hours per day',
      study_consistency_score: 'Consistency of study routine',
      parental_pressure_level: 'Pressure from parents (1-10)',
      peer_comparison_stress: 'Stress from peer comparison (1-10)',
      coaching_engagement_score: 'Engagement in coaching classes',
    }
    return tooltips[feature] || 'Feature impact on dropout risk'
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-8 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <p className="text-sm text-gray-500">{error}</p>
      </div>
    )
  }

  if (!explanation) {
    return null
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Risk Factors</h3>
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-500">
            Risk Score: {(explanation.risk_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="space-y-4">
        {explanation.factors.map((factor, index) => (
          <div
            key={index}
            className="group relative"
            title={getFeatureTooltip(factor.feature)}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                {factor.direction === 'risk' ? (
                  <TrendingUp className="w-4 h-4 text-red-500" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-green-500" />
                )}
                <span className="text-sm font-medium text-gray-700 capitalize">
                  {factor.feature.replace(/_/g, ' ')}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500">{factor.value}</span>
                <span
                  className={`text-sm font-semibold ${
                    factor.direction === 'risk' ? 'text-red-600' : 'text-green-600'
                  }`}
                >
                  {factor.impact > 0 ? '+' : ''}{factor.impact}%
                </span>
              </div>
            </div>

            {/* Animated horizontal bar */}
            <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`absolute top-0 left-0 h-full rounded-full transition-all duration-500 ease-out ${
                  factor.direction === 'risk' ? 'bg-red-500' : 'bg-green-500'
                }`}
                style={{
                  width: `${Math.min(Math.abs(factor.impact), 100)}%`,
                  animation: 'slideIn 0.5s ease-out forwards',
                  animationDelay: `${index * 0.1}s`,
                }}
              />
            </div>

            {/* Tooltip */}
            <div className="absolute left-0 -top-8 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
              {getFeatureTooltip(factor.feature)}
            </div>
          </div>
        ))}
      </div>

      <style jsx>{`
        @keyframes slideIn {
          from {
            width: 0%;
          }
          to {
            width: var(--final-width);
          }
        }
      `}</style>
    </div>
  )
}
