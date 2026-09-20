import apiClient from './axios'

/**
 * Trigger flight cancellation simulation.
 * Backend updates flight status to CANCELLED, records disruption document,
 * emits DISRUPTION_DETECTED to timeline, broadcasts via WebSocket, and dispatches to worker.
 *
 * @param {Object} params
 * @param {string} params.tripId
 * @param {string} params.flightId
 * @param {string} [params.reason]
 */
export const simulateFlightCancellation = async ({ tripId, flightId, reason }) => {
  return apiClient.post('/api/simulations/flight-cancellation', {
    trip_id: tripId,
    flight_id: flightId,
    reason: reason || 'Flight cancelled by airline due to operational constraints',
  })
}

/**
 * Fetch disruption details by ID.
 */
export const fetchDisruption = async (disruptionId) => {
  if (!disruptionId) throw new Error('Disruption ID is required')
  return apiClient.get(`/api/disruptions/${encodeURIComponent(disruptionId)}`)
}

export default {
  simulateFlightCancellation,
  fetchDisruption,
}
