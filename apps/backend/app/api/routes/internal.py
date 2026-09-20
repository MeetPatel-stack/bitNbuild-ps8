from fastapi import APIRouter, status
from app.schemas.timeline import TimelineEventCreateRequest
from app.schemas.rebooking import RebookingCreateRequest
from app.schemas.hotel import HotelBookingUpdateRequest
from app.schemas.notification import NotificationCreateRequest
from app.services.timeline_service import timeline_service
from app.services.rebooking_service import rebooking_service
from app.services.hotel_service import hotel_service
from app.services.notification_service import notification_service

router = APIRouter(prefix="/api/internal", tags=["Worker Internal Ingestion"])


@router.post("/process-events", status_code=status.HTTP_201_CREATED)
async def process_event(request: TimelineEventCreateRequest):
    """
    Append timeline event emitted by the autonomous worker.
    Persists event to database and broadcasts live via WebSocket to clients.
    """
    event = await timeline_service.record_event(
        trip_id=request.trip_id,
        event_type=request.event_type,
        title=request.title,
        description=request.description,
        severity=request.severity or "INFO",
        disruption_id=request.disruption_id,
        payload=request.payload or {},
    )
    return event


@router.post("/rebookings", status_code=status.HTTP_201_CREATED)
async def create_rebooking(request: RebookingCreateRequest):
    """
    Store completed rebooking against disruption and trip.
    Guarantees idempotency: duplicate requests for the same disruption_id return existing rebooking.
    """
    rebooking_dict = request.model_dump(exclude_unset=True)
    rebooking, created = await rebooking_service.store_rebooking(rebooking_dict)
    return {
        "rebooking": rebooking,
        "is_new": created,
        "message": "Rebooking successfully recorded" if created else "Rebooking already exists (idempotent)",
    }


@router.post("/hotel-updates")
async def update_hotel(request: HotelBookingUpdateRequest):
    """
    Update hotel booking associated with trip.
    Guarantees idempotency using optional idempotency_key.
    """
    update_dict = request.model_dump(exclude_unset=True)
    hotel, modified = await hotel_service.update_hotel_booking(update_dict)
    return {
        "hotel": hotel,
        "modified": modified,
        "message": "Hotel stay updated successfully" if modified else "Hotel update already applied (idempotent)",
    }


@router.post("/notifications", status_code=status.HTTP_201_CREATED)
async def record_notification(request: NotificationCreateRequest):
    """
    Persist notification history for traveler communication.
    Guarantees idempotency using idempotency_key.
    """
    notif_dict = request.model_dump(exclude_unset=True)
    notification, created = await notification_service.record_notification(notif_dict)
    return {
        "notification": notification,
        "is_new": created,
        "message": "Notification recorded successfully" if created else "Notification already recorded (idempotent)",
    }


@router.get("/trips/{trip_id}")
async def internal_get_trip(trip_id: str):
    """
    Internal endpoint for worker to fetch trip details without user authentication.
    """
    from app.services.trip_service import trip_service
    return trip_service.get_trip(trip_id)
