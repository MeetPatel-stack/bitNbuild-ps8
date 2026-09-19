import logging
from typing import Dict, Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger("app.services.backend_client")


class BackendClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.backend_url).rstrip("/")

    async def get_trip(self, trip_id: str) -> Dict[str, Any]:
        """Fetch trip itinerary details from backend."""
        url = f"{self.base_url}/api/trips/{trip_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    async def send_process_event(
        self,
        trip_id: str,
        event_type: str,
        title: str,
        description: str,
        severity: str = "INFO",
        disruption_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append timeline event to backend."""
        url = f"{self.base_url}/api/internal/process-events"
        body = {
            "trip_id": trip_id,
            "disruption_id": disruption_id,
            "event_type": event_type,
            "title": title,
            "description": description,
            "severity": severity,
            "payload": payload or {},
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            return resp.json()

    async def create_rebooking(self, rebooking_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit rebooking to backend."""
        url = f"{self.base_url}/api/internal/rebookings"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=rebooking_payload)
            resp.raise_for_status()
            return resp.json()

    async def update_hotel(self, hotel_update_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit hotel modification to backend."""
        url = f"{self.base_url}/api/internal/hotel-updates"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=hotel_update_payload)
            resp.raise_for_status()
            return resp.json()

    async def record_notification(self, notif_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit notification log to backend."""
        url = f"{self.base_url}/api/internal/notifications"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=notif_payload)
            resp.raise_for_status()
            return resp.json()


backend_client = BackendClient()
