import React, { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'

interface Teacher {
  id: number
  email: string
  full_name?: string
}

interface AuthContextType {
  token: string | null
  teacher: Teacher | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  register: (email: string, password: string, fullName: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('token')
  )
  const [teacher, setTeacher] = useState<Teacher | null>(null)

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      api.get('/auth/me').then(res => setTeacher(res.data)).catch(() => logout())
    }
  }, [token])

  const login = async (email: string, password: string) => {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)
    const res = await api.post('/auth/login', formData)
    const newToken = res.data.access_token
    localStorage.setItem('token', newToken)
    api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
    setToken(newToken)
    const meRes = await api.get('/auth/me')
    setTeacher(meRes.data)
  }

  const logout = () => {
    localStorage.removeItem('token')
    delete api.defaults.headers.common['Authorization']
    setToken(null)
    setTeacher(null)
  }

  const register = async (email: string, password: string, fullName: string) => {
    await api.post('/auth/register', { email, password, full_name: fullName })
    await login(email, password)
  }

  return (
    <AuthContext.Provider value={{ token, teacher, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
