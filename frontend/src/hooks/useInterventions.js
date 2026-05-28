import { useState, useCallback } from 'react'
import api from '../api/axiosConfig'

export const useInterventions = (studentId) => {
  const [interventions, setInterventions] = useState([])
  const [currentIntervention, setCurrentIntervention] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchInterventions = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get(`/interventions/students/${studentId}`)
      setInterventions(response.data.interventions)
    } catch (err) {
      setError('Failed to fetch interventions')
      console.error('Error fetching interventions:', err)
    } finally {
      setLoading(false)
    }
  }, [studentId])

  const generateIntervention = useCallback(async (riskFactors, riskScore, riskLevel) => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.post(`/interventions/students/${studentId}/generate`, {
        risk_factors: riskFactors,
        risk_score: riskScore,
        risk_level: riskLevel,
      })
      setCurrentIntervention(response.data)
      await fetchInterventions() // Refresh the list
      return response.data
    } catch (err) {
      setError('Failed to generate intervention')
      console.error('Error generating intervention:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [studentId, fetchInterventions])

  const completeIntervention = useCallback(async (interventionId) => {
    try {
      setLoading(true)
      setError(null)
      await api.patch(`/interventions/${interventionId}/complete`)
      await fetchInterventions() // Refresh the list
    } catch (err) {
      setError('Failed to complete intervention')
      console.error('Error completing intervention:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [fetchInterventions])

  return {
    interventions,
    currentIntervention,
    loading,
    error,
    fetchInterventions,
    generateIntervention,
    completeIntervention,
  }
}
