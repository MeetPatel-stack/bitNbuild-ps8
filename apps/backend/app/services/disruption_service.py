import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.repositories.trips import trip_repo
from app.repositories.disruptions import disruption_repo
from app.services.timeline_service import timeline_service
from app.services.worker_client import worker_client
from app.schemas.timeline import TimelineEventType
from app.schemas.disruption import DisruptionStatus, DisruptionType

logger = logging.getLogger("app.services.disruptions")


class DisruptionService:
    def __init__(self):
        self.trip_repo = trip_repo
        self.disruption_repo = disruption_repo
        self.timeline_service = timeline_service
        self.worker_client = worker_client

    async def simulate_flight_cancellation(
        self,
        trip_id: str,
        flight_id: str,
        reason: Optional[str] = "Flight cancelled by airline due to operational constraints",
    ) -> Dict[str, Any]:
        """
        Simulates a flight cancellation:
        1. Validates trip exists
        2. Validates flight exists within trip
        3. Marks flight as CANCELLED and trip as DISRUPTED
        4. Creates disruption record
        5. Emits DISRUPTION_DETECTED timeline event and broadcasts via WebSocket
        6. Dispatches to worker with safe failure handling
        """
        trip = self.trip_repo.get_by_id(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip with id '{trip_id}' not found")

        flights = trip.get("flights", [])
        flight = next((f for f in flights if f.get("flight_id") == flight_id), None)
        if not flight:
            raise HTTPException(
                status_code=400,
                detail=f"Flight '{flight_id}' not found in trip '{trip_id}'. Available flights: {[f.get('flight_id') for f in flights]}",
            )

        # 3. Mark flight as CANCELLED in database
        self.trip_repo.update_flight_status(trip_id, flight_id, "CANCELLED")

        # 4. Create disruption document
        disruption_doc = {
            "trip_id": trip_id,
            "flight_id": flight_id,
            "disruption_type": DisruptionType.FLIGHT_CANCELLATION.value,
            "reason": reason,
            "status": DisruptionStatus.DETECTED.value,
            "impact_summary": f"Flight {flight.get('flight_number', flight_id)} from {flight.get('origin')} to {flight.get('destination')} cancelled.",
            "worker_dispatch_status": "PENDING",
            "metadata": {
                "airline": flight.get("airline"),
                "flight_number": flight.get("flight_number"),
                "original_departure": str(flight.get("departure_time")),
            },
        }
        saved_disruption = self.disruption_repo.create(disruption_doc)
        disruption_id = saved_disruption["id"]

        # 5. Create initial timeline event (DISRUPTION_DETECTED) and broadcast via WebSocket
        event = await self.timeline_service.record_event(
            trip_id=trip_id,
            disruption_id=disruption_id,
            event_type=TimelineEventType.DISRUPTION_DETECTED,
            title="Flight Disruption Detected",
            description=f"Flight {flight.get('flight_number', flight_id)} ({flight.get('origin')} -> {flight.get('destination')}) cancelled: {reason}",
            severity="CRITICAL",
            payload={
                "disruption_id": disruption_id,
                "flight_id": flight_id,
                "airline": flight.get("airline"),
                "flight_number": flight.get("flight_number"),
                "origin": flight.get("origin"),
                "destination": flight.get("destination"),
            },
        )

        # 6. Dispatch to worker with safe failure handling
        worker_ok, worker_msg = await self.worker_client.dispatch_disruption(
            trip_id=trip_id,
            disruption_id=disruption_id,
        )

        dispatch_status = "DISPATCHED" if worker_ok else "FAILED"
        self.disruption_repo.update_status(
            disruption_id=disruption_id,
            worker_dispatch_status=dispatch_status,
            error=None if worker_ok else worker_msg,
        )

        return {
            "disruption_id": disruption_id,
            "trip_id": trip_id,
            "flight_id": flight_id,
            "status": DisruptionStatus.DETECTED,
            "message": "Flight cancellation recorded successfully" + (" and worker dispatched." if worker_ok else f", but worker dispatch was not reachable ({worker_msg}). Disruption remains recorded."),
            "worker_dispatched": worker_ok,
            "worker_dispatch_status": dispatch_status,
            "timeline_event_id": event.get("id"),
        }

    def get_disruption(self, disruption_id: str) -> Optional[Dict[str, Any]]:
        disruption = self.disruption_repo.get_by_id(disruption_id)
        if not disruption:
            raise HTTPException(status_code=404, detail=f"Disruption '{disruption_id}' not found")
        return disruption


disruption_service = DisruptionService()
