import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  LayoutDashboard, Users, BellRing, BarChart3,
  LogOut, GraduationCap, ClipboardList
} from 'lucide-react'
import clsx from 'clsx'

const NAV_ADMIN = [
  { to: '/admin',              label: 'Overview',  Icon: LayoutDashboard, end: true },
  { to: '/admin/students',     label: 'Students',  Icon: Users },
  { to: '/admin/alerts',       label: 'Alerts',    Icon: BellRing },
  { to: '/admin/analytics',    label: 'Analytics', Icon: BarChart3 },
]

const NAV_FACULTY = [
  { to: '/faculty',            label: 'My Students', Icon: Users, end: true },
  { to: '/faculty/alerts',     label: 'Alerts',      Icon: BellRing },
  { to: '/faculty/predict',    label: 'Predict',     Icon: ClipboardList },
]

export default function DashboardLayout() {
  const { user, role, logout } = useAuth()
  const navigate = useNavigate()
  const navItems = role === 'admin' ? NAV_ADMIN : NAV_FACULTY

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 bg-slate-900 flex flex-col border-r border-slate-800">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shrink-0">
              <GraduationCap className="w-4 h-4 text-white" />
            </div>
            <div className="min-w-0">
              <p className="text-white font-bold text-sm leading-tight truncate">JEE Predictor</p>
              <p className="text-slate-400 text-xs capitalize">{role}</p>
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

        {/* User + logout */}
        <div className="px-3 py-4 border-t border-slate-800">
          <div className="px-3 py-2 mb-1">
            <p className="text-white text-sm font-medium truncate">{user?.full_name || user?.email}</p>
            <p className="text-slate-400 text-xs truncate">{user?.email}</p>
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
