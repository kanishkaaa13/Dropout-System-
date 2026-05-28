import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { RequireAuth } from './components/RequireAuth'
import DashboardLayout from './layouts/DashboardLayout'
import StudentLayout from './layouts/StudentLayout'

import Login            from './pages/auth/Login'
import AdminOverview    from './pages/admin/AdminOverview'
import StudentDetail    from './pages/admin/StudentDetail'
import StudentList      from './pages/admin/StudentList'
import AdminChat        from './pages/admin/AdminChat'
import PredictForm      from './pages/faculty/PredictForm'
import FacultyChat      from './pages/faculty/FacultyChat'
import WeeklySurvey     from './pages/student/WeeklySurvey'
import StudentDashboard from './pages/student/StudentDashboard'
import StudentPredict   from './pages/student/StudentPredict'
import StudentChat      from './pages/student/StudentChat'

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
              <Route path="/admin/chat"          element={<AdminChat />} />
              <Route path="/students/:id"        element={<StudentDetail />} />
              <Route path="/students/:id/survey" element={<WeeklySurvey />} />
            </Route>
          </Route>

          {/* Faculty */}
          <Route element={<RequireAuth allowedRoles={['faculty']} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/faculty"             element={<StudentList facultyOnly />} />
              <Route path="/faculty/predict"     element={<PredictForm />} />
              <Route path="/faculty/chat"        element={<FacultyChat />} />
              <Route path="/faculty/students/:id" element={<StudentDetail />} />
            </Route>
          </Route>

          {/* Student */}
          <Route element={<RequireAuth allowedRoles={['student']} />}>
            <Route element={<StudentLayout />}>
              <Route path="/student/dashboard"   element={<StudentDashboard />} />
              <Route path="/student/predict"     element={<StudentPredict />} />
              <Route path="/student/chat"        element={<StudentChat />} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
