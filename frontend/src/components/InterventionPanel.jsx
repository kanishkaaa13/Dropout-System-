import { useState, useEffect } from 'react'
import { useInterventions } from '../hooks/useInterventions'
import { Sparkles, CheckCircle, Clock, MessageSquare, BookOpen, Heart, AlertCircle } from 'lucide-react'

export default function InterventionPanel({ studentId, riskFactors, riskScore, riskLevel }) {
  const {
    interventions,
    currentIntervention,
    loading,
    error,
    fetchInterventions,
    generateIntervention,
    completeIntervention,
  } = useInterventions(studentId)

  const [activeTab, setActiveTab] = useState('current') // 'current' or 'history'

  useEffect(() => {
    if (studentId) {
      fetchInterventions()
    }
  }, [studentId, fetchInterventions])

  const handleGenerate = async () => {
    try {
      await generateIntervention(riskFactors, riskScore, riskLevel)
    } catch (err) {
      console.error('Failed to generate intervention:', err)
    }
  }

  const handleComplete = async (interventionId) => {
    try {
      await completeIntervention(interventionId)
    } catch (err) {
      console.error('Failed to complete intervention:', err)
    }
  }

  const getActionIcon = (type) => {
    switch (type) {
      case 'counseling': return <MessageSquare className="w-5 h-5" />
      case 'academic': return <BookOpen className="w-5 h-5" />
      case 'wellness': return <Heart className="w-5 h-5" />
      default: return <AlertCircle className="w-5 h-5" />
    }
  }

  const getActionColor = (type) => {
    switch (type) {
      case 'counseling': return 'bg-blue-50 border-blue-200 text-blue-700'
      case 'academic': return 'bg-purple-50 border-purple-200 text-purple-700'
      case 'wellness': return 'bg-green-50 border-green-200 text-green-700'
      default: return 'bg-gray-50 border-gray-200 text-gray-700'
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-700 border-red-200'
      case 'medium': return 'bg-amber-100 text-amber-700 border-amber-200'
      case 'low': return 'bg-green-100 text-green-700 border-green-200'
      default: return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const latestIntervention = interventions.length > 0 ? interventions[0] : null

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">AI Intervention Plan</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('current')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'current'
                ? 'bg-[#6B5CE7] text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Current
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'history'
                ? 'bg-[#6B5CE7] text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            History ({interventions.length})
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 mb-4">
          <AlertCircle className="w-5 h-5" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {activeTab === 'current' ? (
        <div className="space-y-4">
          {!latestIntervention && !currentIntervention ? (
            <div className="text-center py-8">
              <Sparkles className="w-12 h-12 mx-auto text-gray-300 mb-3" />
              <p className="text-gray-500 text-sm mb-4">No intervention plan yet</p>
              <button
                onClick={handleGenerate}
                disabled={loading}
                className="bg-[#6B5CE7] hover:bg-[#5A4BD1] disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2 mx-auto"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Generate AI Plan
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {(currentIntervention || latestIntervention) && (
                <>
                  {/* Priority Badge */}
                  <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border ${getPriorityColor((currentIntervention || latestIntervention).priority)}`}>
                    <span className="text-xs font-medium capitalize">
                      {(currentIntervention || latestIntervention).priority} Priority
                    </span>
                  </div>

                  {/* Summary */}
                  <p className="text-sm text-gray-700">
                    {(currentIntervention || latestIntervention).summary}
                  </p>

                  {/* Action Items */}
                  <div className="space-y-3">
                    <p className="text-sm font-medium text-gray-900">Action Items</p>
                    {(currentIntervention || latestIntervention).actions.map((action, index) => (
                      <div
                        key={index}
                        className={`p-4 rounded-lg border ${getActionColor(action.type)}`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-lg bg-white bg-opacity-50`}>
                            {getActionIcon(action.type)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <h4 className="text-sm font-semibold">{action.title}</h4>
                              <span className="text-xs px-2 py-1 bg-white bg-opacity-50 rounded-full">
                                {action.timeline}
                              </span>
                            </div>
                            <p className="text-xs opacity-80">{action.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Parent Message */}
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center gap-2 mb-2">
                      <MessageSquare className="w-4 h-4 text-gray-500" />
                      <p className="text-sm font-medium text-gray-900">Parent Message</p>
                    </div>
                    <p className="text-sm text-gray-600 italic">
                      "{(currentIntervention || latestIntervention).parent_message}"
                    </p>
                  </div>

                  {/* Mark Complete Button */}
                  {latestIntervention && latestIntervention.status !== 'completed' && (
                    <button
                      onClick={() => handleComplete(latestIntervention.id)}
                      disabled={loading}
                      className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                      {loading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          Updating...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-4 h-4" />
                          Mark as Complete
                        </>
                      )}
                    </button>
                  )}

                  {latestIntervention && latestIntervention.status === 'completed' && (
                    <div className="flex items-center justify-center gap-2 text-green-600 text-sm">
                      <CheckCircle className="w-4 h-4" />
                      <span>Completed on {new Date(latestIntervention.completed_at).toLocaleDateString()}</span>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {interventions.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">No intervention history</p>
          ) : (
            interventions.map((intervention) => (
              <div
                key={intervention.id}
                className="p-4 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className={`inline-flex items-center gap-2 px-2 py-1 rounded-full border ${getPriorityColor(intervention.priority)}`}>
                    <span className="text-xs font-medium capitalize">{intervention.priority}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {intervention.status === 'completed' ? (
                      <span className="text-xs text-green-600 flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" />
                        Completed
                      </span>
                    ) : (
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {intervention.status}
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-sm text-gray-700 mb-1">{intervention.summary}</p>
                <p className="text-xs text-gray-400">
                  {new Date(intervention.created_at).toLocaleDateString()}
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
