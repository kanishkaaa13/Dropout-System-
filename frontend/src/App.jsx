import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { DemoProvider } from './contexts/DemoContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { RequireAuth } from './components/RequireAuth'
import DashboardLayout from './layouts/DashboardLayout'
import StudentLayout from './layouts/StudentLayout'

import Login            from './pages/auth/Login'
import AdminOverview    from './pages/admin/AdminOverview'
import AdminAlerts      from './pages/admin/AdminAlerts'
import AdminAnalytics   from './pages/admin/AdminAnalytics'
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
    <ThemeProvider>
      <DemoProvider>
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
                  <Route path="/admin/alerts"        element={<AdminAlerts />} />
                  <Route path="/admin/analytics"     element={<AdminAnalytics />} />
                  <Route path="/admin/chat"          element={<AdminChat />} />
                  <Route path="/students/:id"        element={<StudentDetail />} />
                  <Route path="/students/:id/survey" element={<WeeklySurvey />} />
                </Route>
              </Route>

              {/* Counselor */}
              <Route element={<RequireAuth allowedRoles={['counselor']} />}>
                <Route element={<DashboardLayout />}>
                  <Route path="/counselor"           element={<StudentList />} />
                  <Route path="/counselor/alerts"    element={<AdminAlerts />} />
                  <Route path="/counselor/chat"      element={<AdminChat />} />
                  <Route path="/counselor/students/:id" element={<StudentDetail />} />
                </Route>
              </Route>

              {/* Teacher */}
              <Route element={<RequireAuth allowedRoles={['teacher']} />}>
                <Route element={<DashboardLayout />}>
                  <Route path="/teacher"             element={<StudentList facultyOnly />} />
                  <Route path="/teacher/students/:id" element={<StudentDetail />} />
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
      </DemoProvider>
    </ThemeProvider>
  )
}
