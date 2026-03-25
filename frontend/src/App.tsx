import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import Layout from './components/Layout'

// Teacher pages
import Dashboard from './pages/teacher/Dashboard'
import Videos from './pages/teacher/Videos'
import VideoDetail from './pages/teacher/VideoDetail'
import Sessions from './pages/teacher/Sessions'
import TeacherPlayer from './pages/teacher/TeacherPlayer'
import Results from './pages/teacher/Results'
import Recommendations from './pages/teacher/Recommendations'
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'

// Student pages
import StudentJoin from './pages/student/StudentJoin'
import StudentLive from './pages/student/StudentLive'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Auth routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Student routes (no auth required) */}
          <Route path="/join" element={<StudentJoin />} />
          <Route path="/live/:sessionId/:studentId" element={<StudentLive />} />

          {/* Teacher routes (auth required) */}
          <Route path="/" element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }>
            <Route index element={<Dashboard />} />
            <Route path="videos" element={<Videos />} />
            <Route path="videos/:videoId" element={<VideoDetail />} />
            <Route path="sessions" element={<Sessions />} />
            <Route path="sessions/:sessionId/player" element={<TeacherPlayer />} />
            <Route path="sessions/:sessionId/results" element={<Results />} />
            <Route path="sessions/:sessionId/recommendations" element={<Recommendations />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
