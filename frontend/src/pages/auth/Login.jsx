import { useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import clsx from 'clsx'
import { Eye, EyeOff, LogIn } from 'lucide-react'

export default function Login() {
  const { login, isAuthenticated, role } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail]     = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw]   = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  // If already logged in, redirect
  if (isAuthenticated) {
    const redirectPath = role === 'admin' ? '/admin' : role === 'student' ? '/student/dashboard' : '/faculty'
    return <Navigate to={redirectPath} replace />
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const me = await login(email, password)
      const redirectPath = me.role === 'admin' ? '/admin' : me.role === 'student' ? '/student/dashboard' : '/faculty'
      navigate(redirectPath, { replace: true })
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map(d => d.msg || JSON.stringify(d)).join(', ')
            : 'Invalid credentials'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8">
        {/* Logo + title */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-600 rounded-2xl mb-4 shadow-lg shadow-indigo-500/30">
            <span className="text-2xl">🎯</span>
          </div>
          <h1 className="text-2xl font-bold text-white font-display">JEE Dropout Prediction</h1>
          <p className="text-slate-400 text-sm mt-1.5">Sign in to your faculty dashboard</p>
        </div>

        {/* Card */}
        <div className="bg-slate-900 rounded-2xl border border-slate-800 p-8 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <label htmlFor="email" className="text-sm font-medium text-slate-300">Email address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="admin@demojee.com"
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-3 text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="password" className="text-sm font-medium text-slate-300">Password</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-3 pr-11 text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((s) => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="rounded-xl bg-red-950 border border-red-800 text-red-300 text-sm px-4 py-3">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white font-semibold py-3 rounded-xl transition-colors"
            >
              <LogIn className="w-4 h-4" />
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-800">
            <p className="text-xs text-slate-500 text-center font-medium mb-3">Demo credentials</p>
            <div className="space-y-1.5 text-xs text-slate-400 text-center">
              <p>admin@demojee.com / Admin@1234</p>
              <p>faculty1@demojee.com / Faculty@1234</p>
              <p>student1@demojee.com / Student@1234</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
