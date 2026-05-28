import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useDemo } from '../contexts/DemoContext'
import { useTheme } from '../contexts/ThemeContext'
import {
  LayoutDashboard, Users, BellRing, BarChart3,
  LogOut, GraduationCap, ClipboardList, Menu, X,
  Sparkles, Moon, Sun
} from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

const NAV_ADMIN = [
  { to: '/admin',              label: 'Overview',  Icon: LayoutDashboard, end: true },
  { to: '/admin/students',     label: 'Students',  Icon: Users },
  { to: '/admin/alerts',       label: 'Alerts',    Icon: BellRing },
  { to: '/admin/analytics',    label: 'Analytics', Icon: BarChart3 },
]

const NAV_COUNSELOR = [
  { to: '/counselor',          label: 'My Students', Icon: Users, end: true },
  { to: '/counselor/alerts',   label: 'Alerts',      Icon: BellRing },
  { to: '/counselor/chat',     label: 'Chat',        Icon: ClipboardList },
]

const NAV_TEACHER = [
  { to: '/teacher',            label: 'My Students', Icon: Users, end: true },
]

const NAV_FACULTY = [
  { to: '/faculty',            label: 'My Students', Icon: Users, end: true },
  { to: '/faculty/alerts',     label: 'Alerts',      Icon: BellRing },
  { to: '/faculty/predict',    label: 'Predict',     Icon: ClipboardList },
]

export default function DashboardLayout() {
  const { user, role, logout } = useAuth()
  const { isDemoMode, toggleDemoMode } = useDemo()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  
  const navItems = (() => {
    switch (role) {
      case 'admin': return NAV_ADMIN
      case 'counselor': return NAV_COUNSELOR
      case 'teacher': return NAV_TEACHER
      case 'faculty': return NAV_FACULTY
      default: return NAV_FACULTY
    }
  })()
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const getInitials = (name) => {
    if (!name) return 'U'
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }

  return (
    <div className={`flex h-screen overflow-hidden font-sans transition-colors duration-200 ${theme === 'dark' ? 'bg-gray-950' : 'bg-[#F8F9FC]'}`}>
      {/* Demo Mode Banner */}
      {isDemoMode && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-yellow-400 text-yellow-900 px-4 py-2 text-sm font-medium text-center">
          ⚠️ You are viewing demo data — not real students
        </div>
      )}

      {/* Mobile menu button */}
      <button
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        className={`lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg shadow-lg border transition-all duration-200 ${isDemoMode ? 'mt-8' : ''} ${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200'}`}
      >
        {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed lg:static inset-y-0 left-0 z-40 w-60 flex flex-col border-r transition-transform duration-300 transition-colors duration-200',
          theme === 'dark' ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200',
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Purple accent border */}
        <div className="h-1 bg-[#6B5CE7]" />

        {/* Logo */}
        <div className={`px-5 py-5 border-b transition-colors duration-200 ${theme === 'dark' ? 'border-gray-800' : 'border-gray-100'}`}>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#6B5CE7] rounded-lg flex items-center justify-center shrink-0">
              <GraduationCap className="w-4 h-4 text-white" />
            </div>
            <div className="min-w-0">
              <p className={`font-bold text-sm leading-tight truncate transition-colors duration-200 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>JEE Predictor</p>
              <p className={`text-xs capitalize transition-colors duration-200 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{role}</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, label, Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={() => setIsSidebarOpen(false)}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-[#6B5CE7] text-white'
                    : theme === 'dark'
                    ? 'text-gray-300 hover:bg-gray-800'
                    : 'text-gray-600 hover:bg-gray-100'
                )
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User profile card */}
        <div className={`px-3 py-4 border-t transition-colors duration-200 ${theme === 'dark' ? 'border-gray-800' : 'border-gray-100'}`}>
          {/* Dark Mode Toggle */}
          <button
            onClick={toggleTheme}
            className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 mb-2 ${
              theme === 'dark' ? 'bg-gray-800 text-gray-200 hover:bg-gray-700' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 shrink-0" /> : <Moon className="w-4 h-4 shrink-0" />}
            {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
          </button>

          {/* Demo Mode Toggle (Admin only) */}
          {role === 'admin' && (
            <button
              onClick={() => toggleDemoMode(!isDemoMode)}
              className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 mb-2 ${
                isDemoMode ? 'bg-yellow-50 text-yellow-700 border border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400 dark:border-yellow-800' : theme === 'dark' ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Sparkles className={`w-4 h-4 shrink-0 ${isDemoMode ? 'text-yellow-600 dark:text-yellow-400' : ''}`} />
              {isDemoMode ? 'Demo Mode ON' : 'Demo Mode'}
            </button>
          )}

          <div className="flex items-center gap-3 px-3 py-2 mb-2">
            <div className="w-9 h-9 bg-[#6B5CE7] rounded-full flex items-center justify-center shrink-0">
              <span className="text-white text-xs font-medium">
                {getInitials(user?.full_name)}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <p className={`text-sm font-medium truncate transition-colors duration-200 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{user?.full_name || user?.email}</p>
              <p className={`text-xs capitalize transition-colors duration-200 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{role}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${theme === 'dark' ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-600 hover:bg-gray-100'}`}
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
          <Outlet />
        </div>
      </main>
    </div>
  )
}
