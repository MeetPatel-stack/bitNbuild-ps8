from fastapi import APIRouter, status
from app.schemas.disruption import DisruptionSimulationRequest, DisruptionSimulationResponse
from app.services.disruption_service import disruption_service

router = APIRouter(prefix="/api", tags=["Disruptions"])


@router.post(
    "/simulations/flight-cancellation",
    response_model=DisruptionSimulationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def simulate_flight_cancellation(request: DisruptionSimulationRequest):
    """
    Trigger a flight cancellation simulation:
    - Validates trip and selected flight segment
    - Marks flight as CANCELLED in database
    - Creates disruption document
    - Emits initial DISRUPTION_DETECTED timeline event
    - Broadcasts event via WebSocket to live clients
    - Dispatches job to autonomous worker service
    """
    result = await disruption_service.simulate_flight_cancellation(
        trip_id=request.trip_id,
        flight_id=request.flight_id,
        reason=request.reason,
    )
    return result


@router.get("/disruptions/{disruption_id}")
def get_disruption(disruption_id: str):
    """
    Retrieve disruption details by disruption ID.
    """
    return disruption_service.get_disruption(disruption_id)
