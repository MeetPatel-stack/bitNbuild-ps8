import logging
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from app.repositories.trips import trip_repo
from app.repositories.hotel_bookings import hotel_booking_repo
from app.repositories.users import user_repo
from app.repositories.rebookings import rebooking_repo
from app.services.timeline_service import timeline_service

logger = logging.getLogger("app.services.trips")


class TripService:
    def __init__(self):
        self.trip_repo = trip_repo
        self.hotel_repo = hotel_booking_repo
        self.user_repo = user_repo
        self.rebooking_repo = rebooking_repo
        self.timeline_service = timeline_service

    def create_trip(self, trip_dict: Dict[str, Any]) -> Dict[str, Any]:
        return self.trip_repo.create(trip_dict)

    def get_trip(self, trip_id: str) -> Dict[str, Any]:
        trip = self.trip_repo.get_by_id(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip with id '{trip_id}' not found")
        # Fetch associated hotel bookings
        hotels = self.hotel_repo.find_by_trip(trip_id)
        trip["hotels"] = hotels
        # Fetch traveler profile if user_id present
        if trip.get("user_id"):
            trip["traveler"] = self.user_repo.get_by_id(trip["user_id"])
        # Fetch associated rebooking resolutions
        trip["rebookings"] = self.rebooking_repo.find_by_trip(trip_id)
        return trip

    def get_timeline(self, trip_id: str) -> List[Dict[str, Any]]:
        # Check trip existence
        trip = self.trip_repo.get_by_id(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip with id '{trip_id}' not found")
        return self.timeline_service.get_trip_timeline(trip_id)


trip_service = TripService()
