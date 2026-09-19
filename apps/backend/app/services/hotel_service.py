import logging
from typing import Dict, Any, Tuple
from fastapi import HTTPException
from app.repositories.hotel_bookings import hotel_booking_repo
from app.repositories.trips import trip_repo
from app.services.timeline_service import timeline_service
from app.schemas.timeline import TimelineEventType

logger = logging.getLogger("app.services.hotel")


class HotelService:
    def __init__(self):
        self.hotel_repo = hotel_booking_repo
        self.trip_repo = trip_repo
        self.timeline_service = timeline_service

    async def update_hotel_booking(self, update_data: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Updates hotel booking associated with trip idempotently.
        """
        trip_id = update_data.get("trip_id")
        hotel_booking_id = update_data.get("hotel_booking_id")
        new_check_in = update_data.get("new_check_in")
        new_check_out = update_data.get("new_check_out")
        status = update_data.get("status")
        notes = update_data.get("notes")
        idempotency_key = update_data.get("idempotency_key")

        # Validate trip
        trip = self.trip_repo.get_by_id(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip '{trip_id}' not found")

        updated_booking, modified = self.hotel_repo.update_hotel_booking(
            trip_id=trip_id,
            hotel_booking_id=hotel_booking_id,
            new_check_in=new_check_in,
            new_check_out=new_check_out,
            status=status.value if hasattr(status, "value") else status,
            notes=notes,
            idempotency_key=idempotency_key,
        )

        if not updated_booking:
            raise HTTPException(status_code=404, detail=f"No hotel booking found for trip '{trip_id}'")

        if not modified:
            logger.info("Idempotent hotel update: key %s already applied", idempotency_key)
            return updated_booking, False

        # Record timeline event HOTEL_UPDATE_CONFIRMED & broadcast
        await self.timeline_service.record_event(
            trip_id=trip_id,
            event_type=TimelineEventType.HOTEL_UPDATE_CONFIRMED,
            title="Hotel Stay Adjusted & Confirmed",
            description=f"Adjusted stay at {updated_booking.get('hotel_name')}. New check-in: {new_check_in or updated_booking.get('check_in')}",
            severity="SUCCESS",
            payload={
                "hotel_booking_id": updated_booking.get("id"),
                "hotel_name": updated_booking.get("hotel_name"),
                "city": updated_booking.get("city"),
                "new_check_in": str(new_check_in) if new_check_in else str(updated_booking.get("check_in")),
                "new_check_out": str(new_check_out) if new_check_out else str(updated_booking.get("check_out")),
                "booking_reference": updated_booking.get("booking_reference"),
                "notes": notes,
            },
        )

        return updated_booking, True


hotel_service = HotelService()
