import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import api from '../api/axiosConfig'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]               = useState(null)
  const [role, setRole]               = useState(null)
  const [isAuthenticated, setIsAuth]  = useState(false)
  const [loading, setLoading]         = useState(true)

  // ── Verify token on mount ────────────────────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) { setLoading(false); return }

    api.get('/auth/me')
      .then(({ data }) => {
        setUser(data)
        setRole(data.role)
        setIsAuth(true)
      })
      .catch(() => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      })
      .finally(() => setLoading(false))
  }, [])

  // ── login ────────────────────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    const { data } = await api.post('/auth/login', {
      email: email,
      password: password
    })

    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)

    // Fetch user profile
    const { data: me } = await api.get('/auth/me')
    setUser(me)
    setRole(me.role)
    setIsAuth(true)
    return me
  }, [])

  // ── logout ───────────────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        await api.post('/auth/logout', { refresh_token: refreshToken })
      }
    } catch (err) {
      console.error('Logout API Error Details:', err)
      console.error('Error response:', err.response)
      console.error('Error message:', err.message)
      // If we get a 422 or any other error, still proceed with client-side cleanup
      if (err.response?.status === 422) {
        console.log('Logout validation error, proceeding with client-side cleanup')
      }
    } finally {
      // Always perform client-side cleanup regardless of API response
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setUser(null)
      setRole(null)
      setIsAuth(false)
    }
  }, [])

  return (
    <AuthContext.Provider value={{ user, role, isAuthenticated, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
