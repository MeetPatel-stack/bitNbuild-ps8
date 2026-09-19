import logging
from typing import Dict, Any, Optional, List
from app.repositories.timeline import timeline_repo
from app.websocket import ws_manager
from app.schemas.timeline import TimelineEventType

logger = logging.getLogger("app.services.timeline")

DEFAULT_TITLES = {
    TimelineEventType.DISRUPTION_DETECTED: "Flight Disruption Detected",
    TimelineEventType.IMPACT_ANALYZED: "Trip Impact Analyzed",
    TimelineEventType.FLIGHTS_SEARCHED: "Alternative Flights Discovered",
    TimelineEventType.POLICY_CHECKED: "Airline Waiver Policy Verified",
    TimelineEventType.REBOOKING_STARTED: "Autonomous Rebooking Initiated",
    TimelineEventType.REBOOKING_CONFIRMED: "New Flights Confirmed & Ticketed",
    TimelineEventType.HOTEL_UPDATE_STARTED: "Hotel Stay Adjustment Initiated",
    TimelineEventType.HOTEL_UPDATE_CONFIRMED: "Hotel Stay Adjusted & Confirmed",
    TimelineEventType.NOTIFICATION_SENT: "Traveler Notification Sent",
    TimelineEventType.PROCESS_COMPLETED: "Autonomous Disruption Resolution Completed",
    TimelineEventType.PROCESS_FAILED: "Disruption Resolution Encountered Issue",
}


class TimelineService:
    def __init__(self):
        self.repo = timeline_repo

    async def record_event(
        self,
        trip_id: str,
        event_type: TimelineEventType,
        title: Optional[str] = None,
        description: Optional[str] = None,
        severity: str = "INFO",
        disruption_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates and persists a timeline event, then broadcasts it via WebSocket to active clients.
        """
        event_title = title or DEFAULT_TITLES.get(event_type, event_type.value)
        event_desc = description or f"Event {event_type.value} occurred for trip {trip_id}"
        
        event_doc = {
            "trip_id": trip_id,
            "disruption_id": disruption_id,
            "event_type": event_type.value if hasattr(event_type, "value") else str(event_type),
            "title": event_title,
            "description": event_desc,
            "severity": severity,
            "payload": payload or {},
        }

        saved_event = self.repo.create(event_doc)
        logger.info("Recorded timeline event [%s] for trip %s", event_type, trip_id)

        # Broadcast event asynchronously to all connected WebSockets for this trip
        await ws_manager.broadcast_to_trip(trip_id, {
            "type": "TIMELINE_EVENT",
            "event": saved_event,
        })

        return saved_event

    def get_trip_timeline(self, trip_id: str) -> List[Dict[str, Any]]:
        return self.repo.find_by_trip(trip_id)


timeline_service = TimelineService()
