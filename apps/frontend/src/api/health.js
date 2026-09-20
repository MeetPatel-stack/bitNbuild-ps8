import apiClient from './axios'

/**
 * Check health of backend service and MongoDB Atlas connectivity.
 */
export const checkHealth = async () => {
  return apiClient.get('/api/health')
}

export default {
  checkHealth,
}
