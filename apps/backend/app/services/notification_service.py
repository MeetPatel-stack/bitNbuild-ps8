import logging
from typing import Dict, Any, Tuple
from fastapi import HTTPException
from app.repositories.notifications import notification_repo
from app.repositories.trips import trip_repo
from app.services.timeline_service import timeline_service
from app.schemas.timeline import TimelineEventType

logger = logging.getLogger("app.services.notifications")


class NotificationService:
    def __init__(self):
        self.notif_repo = notification_repo
        self.trip_repo = trip_repo
        self.timeline_service = timeline_service

    async def record_notification(self, notif_data: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Persists notification history idempotently.
        """
        trip_id = notif_data.get("trip_id")
        disruption_id = notif_data.get("disruption_id")
        channel = notif_data.get("channel", "SMS")
        title = notif_data.get("title")
        message = notif_data.get("message")
        recipient = notif_data.get("recipient")

        # Validate trip
        trip = self.trip_repo.get_by_id(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip '{trip_id}' not found")

        saved_notif, created = self.notif_repo.create_or_get(notif_data)

        if not created:
            logger.info("Idempotent notification: duplicate detected for trip %s", trip_id)
            return saved_notif, False

        # Record timeline event NOTIFICATION_SENT & broadcast
        await self.timeline_service.record_event(
            trip_id=trip_id,
            disruption_id=disruption_id,
            event_type=TimelineEventType.NOTIFICATION_SENT,
            title=f"Notification Dispatched via {channel}",
            description=f"Sent to {recipient}: {title} - {message[:80]}...",
            severity="INFO",
            payload={
                "notification_id": saved_notif.get("id"),
                "channel": channel,
                "recipient": recipient,
                "title": title,
                "status": saved_notif.get("status"),
            },
        )

        return saved_notif, True


notification_service = NotificationService()
