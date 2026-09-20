import apiClient from './axios'

/**
 * Fetch list of all trips from MongoDB.
 */
export const fetchTrips = async () => {
  return apiClient.get('/api/trips')
}

/**
 * Fetch single trip with associated flights, hotels, traveler profile, and rebookings.
 */
export const fetchTrip = async (tripId) => {
  if (!tripId) throw new Error('Trip ID is required')
  return apiClient.get(`/api/trips/${encodeURIComponent(tripId)}`)
}

/**
 * Fetch chronological timeline of events for a trip.
 */
export const fetchTripTimeline = async (tripId) => {
  if (!tripId) throw new Error('Trip ID is required')
  return apiClient.get(`/api/trips/${encodeURIComponent(tripId)}/timeline`)
}

/**
 * Create a new trip itinerary.
 */
export const createTrip = async (tripData) => {
  return apiClient.post('/api/trips', tripData)
}

export default {
  fetchTrips,
  fetchTrip,
  fetchTripTimeline,
  createTrip,
}
