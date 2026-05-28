import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import {
  LayoutDashboard, Brain, MessageSquare, LogOut, GraduationCap, Menu, X, Sparkles, Moon, Sun
} from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

const NAV_STUDENT = [
  { to: '/student/dashboard', label: 'Dashboard', Icon: LayoutDashboard, end: true },
  { to: '/student/predict', label: 'Predict', Icon: Brain },
  { to: '/student/chat', label: 'AI Counselor', Icon: MessageSquare },
]

export default function StudentLayout() {
  const { user, role, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isDemoMode, setIsDemoMode] = useState(false)

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

  const getInitials = (name) => {
    if (!name) return 'S'
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950 overflow-hidden font-sans transition-colors duration-200">
      {/* Demo Mode Banner */}
      {isDemoMode && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-amber-400 text-amber-900 px-4 py-2 text-sm font-medium flex items-center justify-center gap-2">
          <Sparkles className="w-4 h-4" />
          <span>You are viewing demo data — not real students</span>
          <button
            onClick={() => setIsDemoMode(false)}
            className="ml-4 px-2 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded text-xs transition-colors duration-200"
          >
            Exit Demo
          </button>
        </div>
      )}

      {/* Mobile menu button */}
      <button
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 transition-colors duration-200"
      >
        {isSidebarOpen ? <X className="w-5 h-5 text-gray-900 dark:text-gray-100" /> : <Menu className="w-5 h-5 text-gray-900 dark:text-gray-100" />}
      </button>

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed lg:static inset-y-0 left-0 z-40 w-64 bg-white dark:bg-gray-900 flex flex-col border-r border-gray-200 dark:border-gray-800 transition-transform duration-300 transition-colors duration-200',
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Purple accent border */}
        <div className="h-1 bg-gradient-to-r from-indigo-600 to-purple-600" />

        {/* Logo */}
        <div className="px-5 py-5 border-b border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center shrink-0 shadow-lg shadow-indigo-500/20">
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <div className="min-w-0">
              <p className="text-gray-900 dark:text-gray-100 font-bold text-base leading-tight truncate">JEE Predictor</p>
              <p className="text-gray-500 dark:text-gray-400 text-xs capitalize">Student Portal</p>
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
              onClick={() => setIsSidebarOpen(false)}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 relative',
                  isActive
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/20'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                )
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
              {({ isActive }) => isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-r-full" />
              )}
            </NavLink>
          ))}
          
          {/* Demo Mode Toggle */}
          <button
            onClick={() => setIsDemoMode(!isDemoMode)}
            className={clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 w-full',
              isDemoMode
                ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
            )}
          >
            <Sparkles className="w-4 h-4 shrink-0" />
            {isDemoMode ? 'Demo Mode On' : 'Demo Mode'}
          </button>

          {/* Dark Mode Toggle */}
          <button
            onClick={toggleTheme}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 w-full"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 shrink-0" /> : <Moon className="w-4 h-4 shrink-0" />}
            {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
          </button>
        </nav>

        {/* User profile card */}
        <div className="px-3 py-4 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-3 px-3 py-2 mb-2">
            <div className="w-9 h-9 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-full flex items-center justify-center shrink-0 shadow-lg shadow-indigo-500/20">
              <span className="text-white text-xs font-medium">
                {getInitials(user?.full_name)}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-gray-900 dark:text-gray-100 text-sm font-medium truncate">{user?.full_name || 'Student'}</p>
              <p className="text-gray-500 dark:text-gray-400 text-xs capitalize">Student</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200"
          >
            <LogOut className="w-4 h-4 shrink-0" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <Outlet context={{ isDemoMode }} />
        </div>
      </main>
    </div>
  )
}
