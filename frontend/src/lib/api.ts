import axios from 'axios'

export const DEFAULT_TIMEOUT_MS = 20_000
export const ANALYSIS_UPLOAD_TIMEOUT_MS = 600_000

const client = axios.create({
  baseURL: '/api',
  timeout: DEFAULT_TIMEOUT_MS,
})

const PUBLIC_AUTH = ['/auth/login', '/auth/register']

function isPublicAuthUrl(url: string | undefined) {
  const path = url ?? ''
  return PUBLIC_AUTH.some((item) => path.includes(item))
}

let onUnauthorized: (() => void) | null = null

export function setOnUnauthorized(handler: (() => void) | null) {
  onUnauthorized = handler
}

function detailMessage(detail: unknown): string | null {
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item) {
          const msg = (item as { msg: unknown }).msg
          return typeof msg === 'string' ? msg : null
        }
        return null
      })
      .filter((item): item is string => Boolean(item))
    if (messages.length) {
      return messages.join(' ')
    }
  }
  return null
}

export function apiErrorMessage(err: unknown, fallback: string) {
  if (axios.isAxiosError(err)) {
    const fromDetail = detailMessage(err.response?.data?.detail)
    if (fromDetail) {
      return fromDetail
    }
    if (!err.response) {
      return 'Não foi possível conectar ao servidor. Confira se o backend está no ar.'
    }
  }
  if (err instanceof Error && err.message.trim()) {
    return err.message
  }
  return fallback
}

export function isUnauthorized(err: unknown) {
  return axios.isAxiosError(err) && err.response?.status === 401
}

client.interceptors.request.use((config) => {
  if (typeof window !== 'undefined' && !isPublicAuthUrl(config.url)) {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      if (!isPublicAuthUrl(error.config?.url)) {
        onUnauthorized?.()
      }
    }
    return Promise.reject(error)
  }
)

export default client
