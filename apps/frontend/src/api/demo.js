import apiClient from './axios'

/**
 * Trigger demo data reset/seed in backend MongoDB.
 * Resets the demo trip (AMD -> DEL -> LHR), hotel stay, demo user, and clears previous simulation events.
 */
export const seedDemoData = async () => {
  return apiClient.post('/api/demo/seed')
}

/**
 * Fetch the current state of the demo trip (AMD -> DEL -> LHR).
 */
export const fetchDemoTrip = async () => {
  return apiClient.get('/api/demo/trip')
}

export default {
  seedDemoData,
  fetchDemoTrip,
}
