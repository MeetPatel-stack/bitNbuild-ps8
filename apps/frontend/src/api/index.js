export { default as apiClient, API_BASE_URL, getWebSocketUrl } from './axios'
export * from './trips'
export * from './disruptions'
export * from './demo'
export * from './health'

import trips from './trips'
import disruptions from './disruptions'
import demo from './demo'
import health from './health'
import auth from './auth'
import apiClient, { API_BASE_URL } from './axios'

const api = {
  client: apiClient,
  trips,
  disruptions,
  demo,
  health,
  auth,
  API_BASE_URL,
}

export default api
