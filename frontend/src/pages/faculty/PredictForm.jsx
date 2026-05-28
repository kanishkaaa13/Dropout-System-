import { useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../../api/axiosConfig'
import RiskGauge from '../../components/RiskGauge'
import ShapChart from '../../components/ShapChart'
import RiskBadge from '../../components/RiskBadge'
import clsx from 'clsx'
import { Send, ChevronDown, ChevronUp } from 'lucide-react'

// ── Slider input ─────────────────────────────────────────────────────────────
function SliderField({ label, id, name, value, min = 1, max = 10, step = 1, onChange, hint }) {
  const pct = ((value - min) / (max - min)) * 100
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center">
        <label htmlFor={id} className="text-sm font-medium text-slate-700">{label}</label>
        <span className="text-sm font-bold text-indigo-600 tabular-nums w-8 text-right">{value}</span>
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
        className="w-full h-2 rounded-full appearance-none cursor-pointer"
        style={{
          background: `linear-gradient(to right, #6366F1 ${pct}%, #E2E8F0 ${pct}%)`,
        }}
      />
      {hint && <p className="text-xs text-slate-400">{hint}</p>}
    </div>
  )
}

// ── Number input ─────────────────────────────────────────────────────────────
function NumberField({ label, id, name, value, min, max, step = 1, unit, onChange }) {
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="text-sm font-medium text-slate-700">
        {label} {unit && <span className="text-slate-400 text-xs">({unit})</span>}
      </label>
      <input
        id={id}
        type="number"
        name={name}
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={onChange}
        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 tabular-nums"
      />
    </div>
  )
}

// ── Section wrapper ───────────────────────────────────────────────────────────
function Section({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-50 transition-colors"
      >
        <h2 className="font-semibold text-slate-800 text-sm">{title}</h2>
        {open ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>
      {open && <div className="px-6 pb-6 grid grid-cols-1 sm:grid-cols-2 gap-5">{children}</div>}
    </div>
  )
}

const DEFAULTS = {
  attendance_rate: 75, mock_test_avg: 180, physics_score: 60,
  chemistry_score: 60, maths_score: 60, mock_score_trend: 0,
  assignment_completion_rate: 70, dpp_accuracy: 60, test_attempt_rate: 80,
  burnout_score: 5, stress_level: 5, sleep_hours_avg: 6.0,
  study_hours_per_day: 8, study_consistency_score: 60,
  parental_pressure_level: 5, peer_comparison_stress: 5,
  coaching_engagement_score: 65,
}

const RECOMMENDATIONS = {
  Critical: [
    'Schedule immediate one-on-one counselling session',
    'Notify parents and arrange parent-teacher meeting',
    'Reduce syllabus load temporarily — focus on weak chapters only',
    'Consider psychological support / stress management program',
    'Assign a peer mentor from top-performing students',
  ],
  High: [
    'Weekly check-in calls with assigned faculty',
    'Review study plan and adjust difficulty',
    'Monitor attendance daily for the next two weeks',
    'Encourage peer study groups',
  ],
  Medium: [
    'Bi-weekly progress review with faculty',
    'Suggest mock test retake strategy',
    'Share sleep hygiene tips and stress relief resources',
  ],
  Low: [
    'Student is on track — continue current approach',
    'Encourage participation in advanced problem sessions',
  ],
}

export default function PredictForm() {
  const { id } = useParams()
  const [form, setForm]       = useState({ ...DEFAULTS })
  const [result, setResult]   = useState(null)
  const [explanation, setExp] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((f) => ({ ...f, [name]: parseFloat(value) || 0 }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const { data: pred } = await api.post(`/predict/${id}`, form)
      setResult(pred)
      const { data: exp } = await api.get(`/predict/explain/${id}`)
      setExp(exp)
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed')
    } finally {
      setLoading(false)
    }
  }

  const recs = RECOMMENDATIONS[result?.risk_level] || []

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Manual Prediction</h1>
        <p className="text-sm text-slate-500 mt-0.5">Enter feature values to run a dropout risk assessment</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Academic */}
        <Section title="📚 Academic Performance">
          <NumberField label="Attendance Rate" id="attendance_rate" name="attendance_rate" value={form.attendance_rate} min={0} max={100} step={0.1} unit="%" onChange={handleChange} />
          <NumberField label="Mock Test Average" id="mock_test_avg" name="mock_test_avg" value={form.mock_test_avg} min={0} max={360} step={0.5} unit="/ 360" onChange={handleChange} />
          <NumberField label="Physics Score" id="physics_score" name="physics_score" value={form.physics_score} min={0} max={120} step={0.5} unit="/ 120" onChange={handleChange} />
          <NumberField label="Chemistry Score" id="chemistry_score" name="chemistry_score" value={form.chemistry_score} min={0} max={120} step={0.5} unit="/ 120" onChange={handleChange} />
          <NumberField label="Maths Score" id="maths_score" name="maths_score" value={form.maths_score} min={0} max={120} step={0.5} unit="/ 120" onChange={handleChange} />
          <NumberField label="Score Trend (slope)" id="mock_score_trend" name="mock_score_trend" value={form.mock_score_trend} min={-100} max={100} step={0.1} unit="pts/test" onChange={handleChange} />
          <NumberField label="Assignment Completion" id="assignment_completion_rate" name="assignment_completion_rate" value={form.assignment_completion_rate} min={0} max={100} step={1} unit="%" onChange={handleChange} />
          <NumberField label="DPP Accuracy" id="dpp_accuracy" name="dpp_accuracy" value={form.dpp_accuracy} min={0} max={100} step={1} unit="%" onChange={handleChange} />
          <NumberField label="Test Attempt Rate" id="test_attempt_rate" name="test_attempt_rate" value={form.test_attempt_rate} min={0} max={100} step={1} unit="%" onChange={handleChange} />
          <NumberField label="Coaching Engagement" id="coaching_engagement_score" name="coaching_engagement_score" value={form.coaching_engagement_score} min={0} max={100} step={1} unit="/ 100" onChange={handleChange} />
        </Section>

        {/* Behavioral */}
        <Section title="🧠 Behavioral Indicators">
          <SliderField label="Burnout Score" id="burnout_score" name="burnout_score" value={form.burnout_score} onChange={handleChange} hint="1 = No burnout, 10 = Severe" />
          <SliderField label="Stress Level" id="stress_level" name="stress_level" value={form.stress_level} onChange={handleChange} hint="1 = Calm, 10 = Extreme stress" />
          <SliderField label="Sleep (hours/night)" id="sleep_hours_avg" name="sleep_hours_avg" value={form.sleep_hours_avg} min={3} max={10} step={0.5} onChange={handleChange} />
          <SliderField label="Study Hours/Day" id="study_hours_per_day" name="study_hours_per_day" value={form.study_hours_per_day} min={0} max={16} step={0.5} onChange={handleChange} />
          <NumberField label="Study Consistency Score" id="study_consistency_score" name="study_consistency_score" value={form.study_consistency_score} min={0} max={100} step={1} unit="/ 100" onChange={handleChange} />
        </Section>

        {/* Social */}
        <Section title="👨‍👩‍👧 Social & Environmental">
          <SliderField label="Parental Pressure" id="parental_pressure_level" name="parental_pressure_level" value={form.parental_pressure_level} onChange={handleChange} hint="1 = None, 10 = Extreme" />
          <SliderField label="Peer Comparison Stress" id="peer_comparison_stress" name="peer_comparison_stress" value={form.peer_comparison_stress} onChange={handleChange} />
        </Section>

        {error && (
          <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">{error}</div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full sm:w-auto flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-semibold px-8 py-3 rounded-xl transition-colors"
        >
          <Send className="w-4 h-4" />
          {loading ? 'Running prediction…' : 'Run Prediction'}
        </button>
      </form>

      {/* Result panel */}
      {result && (
        <div className="space-y-4 border-t border-slate-100 pt-6">
          <h2 className="text-lg font-bold text-slate-900">Prediction Result</h2>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 flex flex-col items-center justify-center lg:col-span-2">
              <RiskGauge score={result?.risk_score ?? 0} level={result?.risk_level ?? 'Low'} size={220} />
              <div className="mt-3">
                <RiskBadge level={result?.risk_level ?? 'Low'} size="lg" showLabel />
              </div>
              <p className="text-xs text-slate-500 text-center mt-3 leading-relaxed">
                ML probability: {result?.ml_probability ? ((result.ml_probability * 100).toFixed(1)) + '%' : 'N/A'}
              </p>
            </div>

            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 lg:col-span-3">
              <ShapChart impacts={explanation?.top_factors || []} />
            </div>
          </div>

          {/* Recommendations */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
            <h3 className="font-semibold text-slate-800 mb-3 text-sm">💡 Counsellor Recommendations</h3>
            <ul className="space-y-2">
              {recs.length > 0 ? recs.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                  <span className="text-indigo-500 mt-0.5 shrink-0">→</span>
                  {r}
                </li>
              )) : (
                <li className="text-sm text-slate-500">No recommendations available for this risk level.</li>
              )}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
