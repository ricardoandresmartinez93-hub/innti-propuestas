import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import api from '../services/api'

export interface AuthUser {
  id: number
  email: string
  full_name: string
  role: 'admin' | 'creator' | 'approver_1' | 'approver_2' | 'viewer'
}

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const logout = () => {
    localStorage.removeItem('innti_token')
    setToken(null)
    setUser(null)
  }

  const decodeToken = (token: string) => {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
      return JSON.parse(jsonPayload)
    } catch (e) {
      return null
    }
  }

  const restoreSession = async (savedToken: string) => {
    const payload = decodeToken(savedToken)
    if (!payload || (payload.exp && payload.exp * 1000 < Date.now())) {
      logout()
      setIsLoading(false)
      return
    }

    try {
      setToken(savedToken)
      // En el JWT sub es email, user_id es id
      const response = await api.get(`/users/${payload.user_id}`, {
        headers: { Authorization: `Bearer ${savedToken}` }
      })
      setUser(response.data)
    } catch (error) {
      setUser({
        id: payload.user_id,
        email: payload.sub,
        full_name: payload.sub,
        role: payload.role
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    const savedToken = localStorage.getItem('innti_token')
    if (savedToken) {
      restoreSession(savedToken)
    } else {
      setIsLoading(false)
    }
  }, [])

  const login = async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password })
    const { access_token } = response.data
    localStorage.setItem('innti_token', access_token)
    await restoreSession(access_token)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
