from fastapi import APIRouter
from app.services.seed_service import seed_demo_data, DEMO_TRIP_ID
from app.services.trip_service import trip_service

router = APIRouter(prefix="/api/demo", tags=["Demo Seed"])


@router.post("/seed")
def trigger_seed_demo():
    """
    Seed the demo trip: Ahmedabad (AMD) -> Delhi (DEL) -> London (LHR)
    with two connected flight segments, demo user, and one London hotel booking.
    """
    result = seed_demo_data(force=True)
    return result


@router.get("/trip")
def get_demo_trip():
    """
    Retrieve the current state of the demo trip (AMD -> DEL -> LHR).
    """
    return trip_service.get_trip(DEMO_TRIP_ID)
