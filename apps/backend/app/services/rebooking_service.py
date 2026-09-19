import logging
from typing import Dict, Any, Tuple
from fastapi import HTTPException
from app.repositories.rebookings import rebooking_repo
from app.repositories.trips import trip_repo
from app.repositories.disruptions import disruption_repo
from app.services.timeline_service import timeline_service
from app.schemas.timeline import TimelineEventType
from app.schemas.disruption import DisruptionStatus

logger = logging.getLogger("app.services.rebooking")


class RebookingService:
    def __init__(self):
        self.rebooking_repo = rebooking_repo
        self.trip_repo = trip_repo
        self.disruption_repo = disruption_repo
        self.timeline_service = timeline_service

    async def store_rebooking(self, rebooking_data: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Stores rebooking record idempotently.
        If rebooking for this disruption_id already exists, returns (existing, False).
        Otherwise creates rebooking, updates trip flights, updates disruption status,
        emits REBOOKING_CONFIRMED event and returns (new_doc, True).
        """
        trip_id = rebooking_data.get("trip_id")
        disruption_id = rebooking_data.get("disruption_id")
        original_flight_id = rebooking_data.get("original_flight_id")
        new_flights = rebooking_data.get("new_flights", [])

        # Validate trip
        trip = self.trip_repo.get_by_id(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip '{trip_id}' not found")

        # Idempotent storage
        saved_rebooking, created = self.rebooking_repo.create_or_get(rebooking_data)

        if not created:
            logger.info("Idempotent rebooking request: rebooking already exists for disruption %s", disruption_id)
            return saved_rebooking, False

        # Apply new flights to the trip
        if original_flight_id and new_flights:
            self.trip_repo.apply_rebooking(trip_id, original_flight_id, new_flights)

        # Update disruption status to RESOLVED
        if disruption_id:
            self.disruption_repo.update_status(disruption_id, status=DisruptionStatus.RESOLVED.value)

        # Record timeline event REBOOKING_CONFIRMED & broadcast
        flight_desc = ", ".join([f"{f.get('flight_number', 'Flight')} ({f.get('origin')}->{f.get('destination')})" for f in new_flights])
        await self.timeline_service.record_event(
            trip_id=trip_id,
            disruption_id=disruption_id,
            event_type=TimelineEventType.REBOOKING_CONFIRMED,
            title="Alternative Flights Confirmed",
            description=f"Successfully rebooked passenger on: {flight_desc or 'confirmed flights'}",
            severity="SUCCESS",
            payload={
                "rebooking_id": saved_rebooking.get("id"),
                "disruption_id": disruption_id,
                "original_flight_id": original_flight_id,
                "new_flights": new_flights,
                "booking_reference": rebooking_data.get("booking_reference"),
                "cost_difference": rebooking_data.get("cost_difference", 0.0),
            },
        )

        return saved_rebooking, True


rebooking_service = RebookingService()
