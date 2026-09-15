import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './AuthContext'
import Layout from './components/Layout'

import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Papers from './pages/Papers'
import PaperDetail from './pages/PaperDetail'
import Compare from './pages/Compare'
import Ideas from './pages/Ideas'
import Collaborators from './pages/Collaborators'
import Projects from './pages/Projects'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <p className="text-center text-gray-400 mt-20">Loading…</p>
  if (!user) return <Navigate to="/login" replace />
  return children
}

function AppRoutes() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/papers" element={<ProtectedRoute><Papers /></ProtectedRoute>} />
        <Route path="/papers/:id" element={<ProtectedRoute><PaperDetail /></ProtectedRoute>} />
        <Route path="/compare" element={<ProtectedRoute><Compare /></ProtectedRoute>} />
        <Route path="/ideas" element={<ProtectedRoute><Ideas /></ProtectedRoute>} />
        <Route path="/collaborators" element={<ProtectedRoute><Collaborators /></ProtectedRoute>} />
        <Route path="/projects" element={<ProtectedRoute><Projects /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
