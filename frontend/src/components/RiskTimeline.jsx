import { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceArea } from 'recharts'
import api from '../api/axiosConfig'
import { useTheme } from '../contexts/ThemeContext'
import { Calendar, AlertCircle } from 'lucide-react'

export default function RiskTimeline({ studentId }) {
  const { theme } = useTheme()
  const [timelineData, setTimelineData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [weeks, setWeeks] = useState(12)
  const [selectedEvent, setSelectedEvent] = useState(null)

  const fetchTimeline = async (weekCount) => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get(`/students/${studentId}/timeline`, {
        params: { weeks: weekCount }
      })
      setTimelineData(response.data.timeline)
    } catch (err) {
      setError('Failed to load timeline data')
      console.error('Error fetching timeline:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (studentId) {
      fetchTimeline(weeks)
    }
  }, [studentId, weeks])

  const handleWeekChange = (weekCount) => {
    setWeeks(weekCount)
    fetchTimeline(weekCount)
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className={`p-3 rounded-lg shadow-lg border ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <p className="font-semibold text-sm mb-2">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-xs" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
          {data.events && data.events.length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-300 dark:border-gray-600">
              <p className="text-xs font-semibold mb-1 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                Events:
              </p>
              {data.events.map((event, i) => (
                <p key={i} className="text-xs text-gray-600 dark:text-gray-400">
                  • {event}
                </p>
              ))}
            </div>
          )}
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <div className={`rounded-xl shadow-sm p-6 ${theme === 'dark' ? 'bg-gray-900' : 'bg-white'}`}>
        <div className="animate-pulse">
          <div className={`h-4 rounded w-1/3 mb-4 ${theme === 'dark' ? 'bg-gray-800' : 'bg-gray-200'}`}></div>
          <div className={`h-64 rounded ${theme === 'dark' ? 'bg-gray-800' : 'bg-gray-200'}`}></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`rounded-xl shadow-sm p-6 ${theme === 'dark' ? 'bg-gray-900' : 'bg-white'}`}>
        <p className="text-sm text-gray-500">{error}</p>
      </div>
    )
  }

  return (
    <div className={`rounded-xl shadow-sm p-6 transition-all duration-200 ${theme === 'dark' ? 'bg-gray-900' : 'bg-white'}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Calendar className={`w-5 h-5 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`} />
          <h3 className={`text-lg font-semibold transition-colors duration-200 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            Risk Timeline
          </h3>
        </div>
        
        {/* Week Selector */}
        <div className="flex gap-2">
          {[4, 8, 12].map((weekCount) => (
            <button
              key={weekCount}
              onClick={() => handleWeekChange(weekCount)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-all duration-200 ${
                weeks === weekCount
                  ? 'bg-[#6B5CE7] text-white'
                  : theme === 'dark'
                  ? 'text-gray-300 hover:bg-gray-800'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {weekCount} weeks
            </button>
          ))}
        </div>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={timelineData}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#e5e7eb'} />
            <XAxis 
              dataKey="week" 
              stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
              tick={{ fill: theme === 'dark' ? '#9ca3af' : '#6b7280', fontSize: 12 }}
            />
            <YAxis 
              yAxisId="left"
              stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
              tick={{ fill: theme === 'dark' ? '#9ca3af' : '#6b7280', fontSize: 12 }}
              label={{ value: 'Risk Score', angle: -90, position: 'insideLeft', fill: theme === 'dark' ? '#9ca3af' : '#6b7280' }}
            />
            <YAxis 
              yAxisId="right"
              orientation="right"
              stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
              tick={{ fill: theme === 'dark' ? '#9ca3af' : '#6b7280', fontSize: 12 }}
              label={{ value: 'Attendance %', angle: 90, position: 'insideRight', fill: theme === 'dark' ? '#9ca3af' : '#6b7280' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            
            {/* Danger Zone - Red background band above 0.7 risk */}
            <ReferenceArea y1={0.7} y2={1} yAxisId="left" fill="rgba(239, 68, 68, 0.1)" ifOverflow="visible" />
            
            {/* Risk Score Line */}
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="risk_score" 
              stroke="#ef4444" 
              strokeWidth={2}
              dot={{ fill: '#ef4444', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
              name="Risk Score"
            />
            
            {/* Attendance Bar */}
            <Bar 
              yAxisId="right"
              dataKey="attendance" 
              fill="#6366f1" 
              name="Attendance %"
              opacity={0.6}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Events Legend */}
      <div className="mt-4 flex items-center gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500 rounded-full"></div>
          <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Risk Score</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-indigo-500 rounded"></div>
          <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Attendance %</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500/10 rounded"></div>
          <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Danger Zone (&gt;70%)</span>
        </div>
      </div>
    </div>
  )
}
