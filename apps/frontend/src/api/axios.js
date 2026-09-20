import axios from 'axios'

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000'

/**
 * Centralized Axios client for Wayfinder frontend communication with the backend.
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// Request interceptor: add timestamp or log in dev if needed
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => Promise.reject(error),
)

// Response interceptor: format error messages nicely
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorDetail =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected network error occurred'

    const enhancedError = new Error(
      typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail),
    )
    enhancedError.status = error.response?.status
    enhancedError.originalError = error
    return Promise.reject(enhancedError)
  },
)

/**
 * Derive WebSocket endpoint URL dynamically from HTTP base URL.
 * e.g. http://localhost:8000 -> ws://localhost:8000/ws/trips/123
 */
export const getWebSocketUrl = (path = '') => {
  const normalizedBase = API_BASE_URL.replace(/\/+$/, '')
  const wsBase = normalizedBase.replace(/^http/, 'ws')
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${wsBase}${cleanPath}`
}

export default apiClient
