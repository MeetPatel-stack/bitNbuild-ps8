from typing import List, Dict, Any
from fastapi import APIRouter, status
from app.schemas.trip import TripCreate
from app.services.trip_service import trip_service
from app.repositories.trips import trip_repo

router = APIRouter(prefix="/api/trips", tags=["Trips"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_trip(trip_input: TripCreate):
    """
    Create a new travel itinerary with flight segments and optional hotel bookings.
    """
    trip_dict = trip_input.model_dump(exclude_unset=True)
    created = trip_service.create_trip(trip_dict)
    return created


@router.get("", response_model=List[Dict[str, Any]])
def list_trips():
    """
    List all trips.
    """
    return trip_repo.list_all()


@router.get("/{trip_id}")
def get_trip(trip_id: str):
    """
    Retrieve trip details, flight segments, and associated hotel bookings.
    """
    return trip_service.get_trip(trip_id)


@router.get("/{trip_id}/timeline")
def get_trip_timeline(trip_id: str):
    """
    Retrieve chronological timeline of disruption events and rebooking progress for this trip.
    """
    return trip_service.get_timeline(trip_id)
