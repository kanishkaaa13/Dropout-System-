import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  LayoutDashboard, Brain, MessageSquare, LogOut, GraduationCap, User
} from 'lucide-react'
import clsx from 'clsx'

const NAV_STUDENT = [
  { to: '/student/dashboard', label: 'Dashboard', Icon: LayoutDashboard, end: true },
  { to: '/student/predict', label: 'Predict', Icon: Brain },
  { to: '/student/chat', label: 'AI Counselor', Icon: MessageSquare },
]

export default function StudentLayout() {
  const { user, role, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login', { replace: true })
    } catch (error) {
      console.error('Logout error:', error)
      // Force logout even if API fails
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      navigate('/login', { replace: true })
    }
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 bg-slate-900 flex flex-col border-r border-slate-800">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-indigo-600 rounded-lg flex items-center justify-center shrink-0">
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <div className="min-w-0">
              <p className="text-white font-bold text-base leading-tight truncate">JEE Predictor</p>
              <p className="text-slate-400 text-xs capitalize">Student Portal</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {NAV_STUDENT.map(({ to, label, Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                )
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User Profile Footer */}
        <div className="px-3 py-4 border-t border-slate-800">
          <div className="px-3 py-2 mb-1">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-slate-300" />
              </div>
              <div className="min-w-0">
                <p className="text-white text-sm font-medium truncate">
                  {user?.full_name || 'Student'}
                </p>
                <p className="text-slate-400 text-xs truncate">Student</p>
              </div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <LogOut className="w-4 h-4 shrink-0" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
