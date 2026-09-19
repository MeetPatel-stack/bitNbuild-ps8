from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class HotelBooking(BaseModel):
    id: str
    trip_id: str
    hotel_name: str
    city: str
    check_in: datetime
    check_out: datetime
    room_type: str = "Standard Deluxe"
    booking_reference: str
    status: str = "CONFIRMED"


class HotelImpactResult(BaseModel):
    requires_modification: bool
    hotel_booking_id: Optional[str] = None
    original_check_in: Optional[datetime] = None
    new_check_in: Optional[datetime] = None
    delay_hours: float = 0.0
    reason: str = "No modification required"
