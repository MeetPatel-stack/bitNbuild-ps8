from typing import List, Dict, Any
from fastapi import APIRouter, status, Depends, HTTPException
from app.schemas.trip import TripCreate
from app.services.trip_service import trip_service
from app.repositories.trips import trip_repo
from app.api.dependencies import get_current_user_id

router = APIRouter(prefix="/api/trips", tags=["Trips"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_trip(trip_input: TripCreate, user_id: str = Depends(get_current_user_id)):
    """
    Create a new travel itinerary with flight segments and optional hotel bookings.
    """
    trip_dict = trip_input.model_dump(exclude_unset=True)
    trip_dict["user_id"] = user_id
    created = trip_service.create_trip(trip_dict)
    return created


@router.get("", response_model=List[Dict[str, Any]])
def list_trips(user_id: str = Depends(get_current_user_id)):
    """
    List all trips for the authenticated user.
    """
    return trip_repo.find_by_user(user_id)


@router.get("/{trip_id}")
def get_trip(trip_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Retrieve trip details, flight segments, and associated hotel bookings.
    """
    trip = trip_service.get_trip(trip_id)
    if trip.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this trip")
    return trip


@router.get("/{trip_id}/timeline")
def get_trip_timeline(trip_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Retrieve chronological timeline of disruption events and rebooking progress for this trip.
    """
    trip = trip_service.get_trip(trip_id)
    if trip.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this trip")
    return trip_service.get_timeline(trip_id)
