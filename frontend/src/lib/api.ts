import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
})

export function apiErrorMessage(err: unknown, fallback: string) {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }
  }
  return fallback
}

export function isUnauthorized(err: unknown) {
  return axios.isAxiosError(err) && err.response?.status === 401
}

client.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

export default client
