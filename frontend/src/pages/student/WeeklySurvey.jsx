import { useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../../api/axiosConfig'
import clsx from 'clsx'
import { CheckCircle2 } from 'lucide-react'

// ── Slider with emoji icon and value bubble ───────────────────────────────────
function SurveySlider({ id, label, name, value, min, max, step = 1, emoji, lowLabel, highLabel, onChange }) {
  const pct = ((value - min) / (max - min)) * 100

  // Dynamic color based on whether high = bad or high = good
  const isInverted = name === 'motivation_level' || name === 'sleep_hours_avg' || name === 'study_hours_per_day'
  const trackColor = isInverted
    ? pct > 60 ? '#10B981' : pct > 30 ? '#F59E0B' : '#EF4444'
    : pct > 60 ? '#EF4444' : pct > 30 ? '#F59E0B' : '#10B981'

  return (
    <div className="space-y-3 bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
      <div className="flex items-center justify-between">
        <label htmlFor={id} className="flex items-center gap-2 font-semibold text-slate-800 text-sm">
          <span className="text-xl">{emoji}</span>
          {label}
        </label>
        <span
          className="text-lg font-bold tabular-nums min-w-[2.5rem] text-center py-0.5 px-2 rounded-lg"
          style={{ color: trackColor, background: `${trackColor}15` }}
        >
          {value}
        </span>
      </div>

      <input
        id={id}
        type="range"
        name={name}
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={onChange}
        className="w-full h-2.5 rounded-full appearance-none cursor-pointer"
        style={{
          background: `linear-gradient(to right, ${trackColor} ${pct}%, #E2E8F0 ${pct}%)`,
        }}
      />

      {(lowLabel || highLabel) && (
        <div className="flex justify-between text-xs text-slate-400">
          <span>{lowLabel}</span>
          <span>{highLabel}</span>
        </div>
      )}
    </div>
  )
}

const SURVEY_FIELDS = [
  { id: 'burnout_score', name: 'burnout_score', label: 'Burnout Level', emoji: '🔥',
    min: 1, max: 10, lowLabel: 'Fully recharged', highLabel: 'Completely drained' },
  { id: 'stress_level', name: 'stress_level', label: 'Stress Level', emoji: '😰',
    min: 1, max: 10, lowLabel: 'Very calm', highLabel: 'Extremely stressed' },
  { id: 'sleep_hours_avg', name: 'sleep_hours_avg', label: 'Average Sleep', emoji: '😴',
    min: 3, max: 10, step: 0.5, lowLabel: '3 hrs', highLabel: '10 hrs' },
  { id: 'study_hours_per_day', name: 'study_hours_per_day', label: 'Study Hours / Day', emoji: '📖',
    min: 0, max: 16, step: 0.5, lowLabel: '0 hrs', highLabel: '16 hrs' },
  { id: 'parental_pressure', name: 'parental_pressure', label: 'Parental Pressure', emoji: '👨‍👩‍👧',
    min: 1, max: 10, lowLabel: 'Very supportive', highLabel: 'Extremely pressurising' },
  { id: 'motivation_level', name: 'motivation_level', label: 'Motivation Level', emoji: '⚡',
    min: 1, max: 10, lowLabel: 'Very low', highLabel: 'Highly motivated' },
]

const HEALTH_MESSAGES = {
  high:   { emoji: '🎉', title: 'Great job! You\'re doing well!', body: 'Your preparation health is strong. Keep the momentum — consistency is key to cracking JEE!' },
  medium: { emoji: '💪', title: 'You\'re managing — keep pushing!', body: 'A few areas need attention. Try to improve sleep, reduce stress with short breaks, and stay consistent with your DPPs.' },
  low:    { emoji: '🤝', title: 'We\'re here for you.', body: 'It\'s okay to feel overwhelmed sometimes. Please talk to your faculty or a counsellor. Taking care of yourself IS part of JEE prep.' },
}

function computeHealthScore(form) {
  const inv = (v, max) => ((max - v) / (max - 1)) * 100   // invert 1-10 scale
  const norm = (v, max) => ((v - 1) / (max - 1)) * 100

  const score =
    inv(form.burnout_score, 10) * 0.25 +
    inv(form.stress_level, 10) * 0.20 +
    norm(form.sleep_hours_avg - 3, 7) * 0.20 +
    norm(form.study_hours_per_day, 16) * 0.15 +
    inv(form.parental_pressure, 10) * 0.10 +
    norm(form.motivation_level, 10) * 0.10

  return Math.round(Math.min(100, Math.max(0, score)))
}

export default function WeeklySurvey() {
  const { id } = useParams()
  const [form, setForm]       = useState({
    burnout_score: 5, stress_level: 5, sleep_hours_avg: 6.5,
    study_hours_per_day: 8, parental_pressure: 5, motivation_level: 6,
    peer_comparison_stress: 5, notes: '',
  })
  const [submitted, setSubmitted] = useState(false)
  const [healthScore, setHealth]  = useState(null)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((f) => ({ ...f, [name]: name === 'notes' ? value : parseFloat(value) }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await api.post(`/students/${id}/surveys`, {
        ...form,
        peer_comparison_stress: form.peer_comparison_stress,
      })
      setHealth(computeHealthScore(form))
      setSubmitted(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit survey')
    } finally {
      setLoading(false)
    }
  }

  const healthCategory = healthScore >= 65 ? 'high' : healthScore >= 40 ? 'medium' : 'low'
  const healthMsg = HEALTH_MESSAGES[healthCategory]

  // ── Success state ────────────────────────────────────────────────────────
  if (submitted) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <div className="w-full max-w-md text-center space-y-6">
          <div className="text-6xl">{healthMsg.emoji}</div>

          <div>
            <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
            <h2 className="text-xl font-bold text-slate-900">{healthMsg.title}</h2>
            <p className="text-slate-500 text-sm mt-2 leading-relaxed">{healthMsg.body}</p>
          </div>

          {/* Health score ring */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Preparation Health Score</p>
            <div className="flex items-center justify-center gap-4">
              <div
                className={clsx(
                  'text-4xl font-bold tabular-nums',
                  healthScore >= 65 ? 'text-emerald-600' : healthScore >= 40 ? 'text-amber-600' : 'text-red-600'
                )}
              >
                {healthScore}
              </div>
              <div className="text-left">
                <div className="text-xs text-slate-400">out of 100</div>
                <div className={clsx(
                  'text-sm font-semibold capitalize',
                  healthScore >= 65 ? 'text-emerald-600' : healthScore >= 40 ? 'text-amber-600' : 'text-red-600'
                )}>
                  {healthCategory} wellbeing
                </div>
              </div>
            </div>

            {/* Progress bar */}
            <div className="mt-4 h-2.5 rounded-full bg-slate-100 overflow-hidden">
              <div
                className={clsx(
                  'h-full rounded-full transition-all duration-1000',
                  healthScore >= 65 ? 'bg-emerald-500' : healthScore >= 40 ? 'bg-amber-500' : 'bg-red-500'
                )}
                style={{ width: `${healthScore}%` }}
              />
            </div>
          </div>

          <button
            onClick={() => setSubmitted(false)}
            className="text-indigo-600 text-sm font-medium hover:text-indigo-800"
          >
            ← Submit another response
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="max-w-lg mx-auto space-y-5">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-900">Weekly Check-in 📋</h1>
          <p className="text-slate-500 text-sm mt-1.5">
            How are you feeling this week? Be honest — this helps your faculty support you better.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {SURVEY_FIELDS.map((f) => (
            <SurveySlider
              key={f.id}
              {...f}
              value={form[f.name]}
              onChange={handleChange}
            />
          ))}

          {/* Notes */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 space-y-2">
            <label htmlFor="notes" className="flex items-center gap-2 font-semibold text-slate-800 text-sm">
              <span className="text-xl">💬</span>
              Anything else on your mind? <span className="text-slate-400 font-normal">(optional)</span>
            </label>
            <textarea
              id="notes"
              name="notes"
              value={form.notes}
              onChange={handleChange}
              rows={3}
              placeholder="Share anything you'd like your faculty to know…"
              className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-700 placeholder:text-slate-300"
            />
          </div>

          {error && (
            <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-semibold py-4 rounded-2xl transition-colors text-base"
          >
            {loading ? 'Submitting…' : '✅ Submit Weekly Check-in'}
          </button>
        </form>
      </div>
    </div>
  )
}
