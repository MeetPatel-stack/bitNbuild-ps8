import apiClient from './axios'

const register = async (name, email, password) => {
  return apiClient.post('/api/auth/register', { name, email, password })
}

const login = async (email, password) => {
  return apiClient.post('/api/auth/login', { email, password })
}

export default {
  register,
  login,
}

