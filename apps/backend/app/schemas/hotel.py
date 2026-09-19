from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.common import MongoBaseModel, utc_now


class HotelStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    MODIFIED = "MODIFIED"
    CANCELLED = "CANCELLED"


class HotelBookingBase(BaseModel):
    trip_id: str
    hotel_name: str
    city: str
    check_in: datetime
    check_out: datetime
    room_type: str = "Standard Deluxe"
    booking_reference: str
    status: HotelStatus = HotelStatus.CONFIRMED
    address: Optional[str] = None
    contact_phone: Optional[str] = None


class HotelBookingCreate(HotelBookingBase):
    id: Optional[str] = None


class HotelBooking(HotelBookingBase, MongoBaseModel):
    id: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class HotelBookingUpdateRequest(BaseModel):
    trip_id: str
    hotel_booking_id: Optional[str] = None
    new_check_in: Optional[datetime] = None
    new_check_out: Optional[datetime] = None
    status: Optional[HotelStatus] = None
    notes: Optional[str] = None
    idempotency_key: Optional[str] = None
