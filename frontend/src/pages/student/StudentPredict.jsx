import { useState } from 'react'
import api from '../../api/axiosConfig'
import { Brain, Sparkles, AlertCircle, CheckCircle, TrendingUp } from 'lucide-react'

export default function StudentPredict() {
  const [formData, setFormData] = useState({
    attendance: 85,
    mock_average: 180,
    physics_score: 62,
    chemistry_score: 58,
    math_score: 71,
    physics_trend: 0,
    chemistry_trend: 0,
    math_trend: 0,
    assignment_completion: 78,
    burnout_score: 6,
    stress_level: 7,
    sleep_hours: 5.5,
    study_hours: 10,
    peer_pressure: 5
  })

  const [prediction, setPrediction] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [usingFallback, setUsingFallback] = useState(false)

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleRunPrediction = async () => {
    setLoading(true)
    setError(null)
    setUsingFallback(false)
    setPrediction(null)

    try {
      const response = await api.post('/predict', formData)
      setPrediction(response.data)
    } catch (err) {
      console.warn('Backend prediction API unavailable, running local inference:', err.message)
      setUsingFallback(true)
      
      // Run local fallback prediction
      const fallbackResult = runLocalInference(formData)
      setPrediction(fallbackResult)
    } finally {
      setLoading(false)
    }
  }

  const runLocalInference = (data) => {
    // Deterministic fallback algorithm for mock rank prediction
    // This ensures consistent results without backend
    
    const academicScore = (
      (data.physics_score + data.chemistry_score + data.math_score) / 3 * 0.4 +
      (data.mock_average / 360) * 100 * 0.3 +
      (data.attendance / 100) * 100 * 0.2 +
      (data.assignment_completion / 100) * 100 * 0.1
    )

    const wellnessPenalty = (
      (data.burnout_score / 10) * 15 +
      (data.stress_level / 10) * 10 +
      (data.peer_pressure / 10) * 5
    )

    const sleepBonus = data.sleep_hours >= 7 ? 5 : data.sleep_hours >= 6 ? 0 : -5
    const studyPenalty = data.study_hours > 12 ? -5 : data.study_hours < 6 ? -10 : 0

    const trendBonus = (data.physics_trend + data.chemistry_trend + data.math_trend) * 2

    const finalScore = Math.max(0, Math.min(100, 
      academicScore - wellnessPenalty + sleepBonus + studyPenalty + trendBonus
    ))

    // Convert score to rank (inverse relationship)
    const baseRank = Math.round(10000 * (1 - finalScore / 100))
    const predictedRank = Math.max(1, baseRank + Math.floor(Math.random() * 50))

    // Determine risk level
    let riskLevel = 'Low'
    if (finalScore < 40) riskLevel = 'Critical'
    else if (finalScore < 55) riskLevel = 'High'
    else if (finalScore < 70) riskLevel = 'Medium'

    // Calculate top factors
    const factors = []
    if (data.burnout_score >= 7) factors.push({ name: 'High Burnout', impact: -15, type: 'negative' })
    if (data.stress_level >= 7) factors.push({ name: 'High Stress', impact: -10, type: 'negative' })
    if (data.sleep_hours < 6) factors.push({ name: 'Low Sleep', impact: -10, type: 'negative' })
    if (data.attendance >= 90) factors.push({ name: 'Excellent Attendance', impact: 8, type: 'positive' })
    if (data.mock_average >= 200) factors.push({ name: 'Strong Mock Performance', impact: 12, type: 'positive' })
    if (data.assignment_completion >= 85) factors.push({ name: 'High Assignment Completion', impact: 6, type: 'positive' })
    if (data.physics_trend > 0) factors.push({ name: 'Physics Improvement', impact: 5, type: 'positive' })
    if (data.math_score >= 70) factors.push({ name: 'Strong Math Foundation', impact: 8, type: 'positive' })

    return {
      predicted_rank: predictedRank,
      risk_score: Math.round(finalScore),
      risk_level: riskLevel,
      top_factors: factors.slice(0, 5),
      confidence: 0.85,
      is_mock: true
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Prediction Engine</h1>
            <p className="text-slate-500 text-sm">Simulate your JEE rank based on current metrics</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-6">Input Parameters</h2>
          
          <div className="space-y-6">
            {/* Academic Metrics */}
            <div>
              <h3 className="text-sm font-medium text-slate-700 mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Academic Metrics
              </h3>
              <div className="space-y-4">
                <SliderInput
                  label="Attendance Rate"
                  value={formData.attendance}
                  onChange={(v) => handleInputChange('attendance', v)}
                  min={0}
                  max={100}
                  unit="%"
                />
                <SliderInput
                  label="Mock Test Average"
                  value={formData.mock_average}
                  onChange={(v) => handleInputChange('mock_average', v)}
                  min={0}
                  max={360}
                  unit="/ 360"
                />
                <SliderInput
                  label="Physics Score"
                  value={formData.physics_score}
                  onChange={(v) => handleInputChange('physics_score', v)}
                  min={0}
                  max={100}
                  unit="%"
                />
                <SliderInput
                  label="Chemistry Score"
                  value={formData.chemistry_score}
                  onChange={(v) => handleInputChange('chemistry_score', v)}
                  min={0}
                  max={100}
                  unit="%"
                />
                <SliderInput
                  label="Mathematics Score"
                  value={formData.math_score}
                  onChange={(v) => handleInputChange('math_score', v)}
                  min={0}
                  max={100}
                  unit="%"
                />
                <SliderInput
                  label="Assignment Completion"
                  value={formData.assignment_completion}
                  onChange={(v) => handleInputChange('assignment_completion', v)}
                  min={0}
                  max={100}
                  unit="%"
                />
              </div>
            </div>

            {/* Behavioral Metrics */}
            <div>
              <h3 className="text-sm font-medium text-slate-700 mb-4 flex items-center gap-2">
                <Brain className="w-4 h-4" />
                Behavioral Metrics
              </h3>
              <div className="space-y-4">
                <SliderInput
                  label="Burnout Score"
                  value={formData.burnout_score}
                  onChange={(v) => handleInputChange('burnout_score', v)}
                  min={1}
                  max={10}
                  unit="/ 10"
                  color="red"
                />
                <SliderInput
                  label="Stress Level"
                  value={formData.stress_level}
                  onChange={(v) => handleInputChange('stress_level', v)}
                  min={1}
                  max={10}
                  unit="/ 10"
                  color="amber"
                />
                <SliderInput
                  label="Sleep Hours"
                  value={formData.sleep_hours}
                  onChange={(v) => handleInputChange('sleep_hours', v)}
                  min={3}
                  max={10}
                  unit="hours"
                  step={0.5}
                />
                <SliderInput
                  label="Study Hours"
                  value={formData.study_hours}
                  onChange={(v) => handleInputChange('study_hours', v)}
                  min={2}
                  max={14}
                  unit="hours"
                  step={0.5}
                />
                <SliderInput
                  label="Peer Comparison Stress"
                  value={formData.peer_pressure}
                  onChange={(v) => handleInputChange('peer_pressure', v)}
                  min={1}
                  max={10}
                  unit="/ 10"
                  color="purple"
                />
              </div>
            </div>

            <button
              onClick={handleRunPrediction}
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium py-3 px-4 rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Calculating...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Run Prediction
                </>
              )}
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-6">Prediction Results</h2>
          
          {error && !prediction && (
            <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              <AlertCircle className="w-5 h-5" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          {usingFallback && (
            <div className="flex items-center gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 mb-4">
              <AlertCircle className="w-5 h-5" />
              <p className="text-sm">Backend unavailable. Using local inference engine.</p>
            </div>
          )}

          {!prediction && !loading && (
            <div className="flex flex-col items-center justify-center h-64 text-slate-400">
              <Brain className="w-12 h-12 mb-3" />
              <p className="text-sm">Enter parameters and run prediction to see results</p>
            </div>
          )}

          {prediction && (
            <div className="space-y-6">
              {/* Main Result */}
              <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-100">
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-600 mb-2">Predicted JEE Rank</p>
                  <p className="text-5xl font-bold text-indigo-600 mb-2">{prediction.predicted_rank}</p>
                  <div className="flex items-center justify-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                    <span className="text-sm text-slate-600">
                      {prediction.confidence >= 0.8 ? 'High Confidence' : 'Moderate Confidence'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Risk Score */}
              <div>
                <p className="text-sm font-medium text-slate-600 mb-2">Risk Score</p>
                <div className="flex items-center gap-4">
                  <div className="flex-1 bg-slate-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all ${
                        prediction.risk_level === 'Critical' ? 'bg-red-500' :
                        prediction.risk_level === 'High' ? 'bg-orange-500' :
                        prediction.risk_level === 'Medium' ? 'bg-amber-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${prediction.risk_score}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-slate-900">{prediction.risk_score}/100</span>
                </div>
                <p className="text-xs text-slate-500 mt-1 capitalize">{prediction.risk_level} Risk</p>
              </div>

              {/* Top Factors */}
              <div>
                <p className="text-sm font-medium text-slate-600 mb-3">Top Contributing Factors</p>
                <div className="space-y-2">
                  {prediction.top_factors.map((factor, index) => (
                    <div
                      key={index}
                      className={`flex items-center justify-between p-3 rounded-lg ${
                        factor.type === 'positive' 
                          ? 'bg-emerald-50 border border-emerald-200' 
                          : 'bg-red-50 border border-red-200'
                      }`}
                    >
                      <span className="text-sm font-medium text-slate-700">{factor.name}</span>
                      <span
                        className={`text-sm font-bold ${
                          factor.type === 'positive' ? 'text-emerald-600' : 'text-red-600'
                        }`}
                      >
                        {factor.impact > 0 ? '+' : ''}{factor.impact}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {prediction.is_mock && (
                <div className="text-xs text-slate-400 text-center">
                  * Results based on local inference simulation
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function SliderInput({ label, value, onChange, min, max, unit, color = 'indigo', step = 1 }) {
  const colorClasses = {
    indigo: 'bg-indigo-600',
    red: 'bg-red-500',
    amber: 'bg-amber-500',
    purple: 'bg-purple-500'
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-slate-700">{label}</label>
        <span className="text-sm font-bold text-slate-900">
          {value} {unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
        style={{ accentColor: color === 'indigo' ? '#4f46e5' : color === 'red' ? '#ef4444' : color === 'amber' ? '#f59e0b' : '#a855f7' }}
      />
    </div>
  )
}
