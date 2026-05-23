import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { RequireAuth } from './components/RequireAuth'
import DashboardLayout from './layouts/DashboardLayout'

import Login          from './pages/auth/Login'
import AdminOverview  from './pages/admin/AdminOverview'
import StudentDetail  from './pages/admin/StudentDetail'
import StudentList    from './pages/admin/StudentList'
import PredictForm    from './pages/faculty/PredictForm'
import WeeklySurvey   from './pages/student/WeeklySurvey'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<Login />} />

          {/* Admin */}
          <Route element={<RequireAuth allowedRoles={['admin']} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/admin"               element={<AdminOverview />} />
              <Route path="/admin/students"      element={<StudentList />} />
              <Route path="/students/:id"        element={<StudentDetail />} />
              <Route path="/students/:id/survey" element={<WeeklySurvey />} />
            </Route>
          </Route>

          {/* Faculty */}
          <Route element={<RequireAuth allowedRoles={['faculty']} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/faculty"             element={<StudentList facultyOnly />} />
              <Route path="/faculty/predict"     element={<PredictForm />} />
              <Route path="/faculty/students/:id" element={<StudentDetail />} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
