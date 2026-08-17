import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import client, { setOnUnauthorized } from '@/lib/api'
import type { UserProfile, UserRegisterPayload } from '@/lib/types'

type AuthContextValue = {
  token: string | null
  user: UserProfile | null
  ready: boolean
  login: (email: string, password: string) => Promise<void>
  register: (payload: UserRegisterPayload) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function readStoredToken() {
  return localStorage.getItem('token')
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<UserProfile | null>(null)
  const [ready, setReady] = useState(false)

  const clearSession = useCallback(() => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }, [])

  const loadUser = useCallback(async () => {
    const response = await client.get<UserProfile>('/auth/me')
    setUser(response.data)
  }, [])

  const applyToken = useCallback(
    async (accessToken: string, profile?: UserProfile | null) => {
      localStorage.setItem('token', accessToken)
      setToken(accessToken)
      if (profile) {
        setUser(profile)
        return
      }
      await loadUser()
    },
    [loadUser],
  )

  useEffect(() => {
    setOnUnauthorized(() => {
      clearSession()
      window.location.assign('/login')
    })
    return () => setOnUnauthorized(null)
  }, [clearSession])

  useEffect(() => {
    const stored = readStoredToken()
    setToken(stored)
    if (!stored) {
      setReady(true)
      return
    }
    client
      .get<UserProfile>('/auth/me')
      .then((response) => setUser(response.data))
      .catch(() => {
        /* 401 interceptor clears the session */
      })
      .finally(() => setReady(true))
  }, [])

  const login = async (email: string, password: string) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)

    const response = await client.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    const { access_token, user: profile } = response.data as {
      access_token?: unknown
      user?: UserProfile
    }
    if (typeof access_token !== 'string' || !access_token) {
      throw new Error('Resposta de login inválida.')
    }
    await applyToken(access_token, profile)
  }

  const register = async (payload: UserRegisterPayload) => {
    const response = await client.post('/auth/register', payload)
    const { access_token, user: profile } = response.data as {
      access_token?: unknown
      user?: UserProfile
    }
    if (typeof access_token !== 'string' || !access_token) {
      throw new Error('Resposta de cadastro inválida.')
    }
    await applyToken(access_token, profile)
  }

  const logout = () => {
    clearSession()
  }

  const refreshUser = async () => {
    await loadUser()
  }

  return (
    <AuthContext.Provider
      value={{ token, user, ready, login, register, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider')
  }
  return context
}
