from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import MongoBaseModel, utc_now


class FlightStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"
    REBOOKED = "REBOOKED"
    COMPLETED = "COMPLETED"


class TripStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    ACTIVE = "ACTIVE"
    DISRUPTED = "DISRUPTED"
    REBOOKING_IN_PROGRESS = "REBOOKING_IN_PROGRESS"
    RESOLVED = "RESOLVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class FlightSegment(BaseModel):
    flight_id: str = Field(description="Unique identifier for flight segment within trip")
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    status: FlightStatus = FlightStatus.SCHEDULED
    seat: Optional[str] = None
    gate: Optional[str] = None
    terminal: Optional[str] = None
    class_of_service: Optional[str] = "Economy"


class TripBase(BaseModel):
    user_id: str = "demo-user-1"
    title: str = "Ahmedabad to London Trip"
    origin: str = "AMD"
    destination: str = "LHR"
    status: TripStatus = TripStatus.CONFIRMED
    flights: List[FlightSegment] = Field(default_factory=list)
    hotel_booking_ids: List[str] = Field(default_factory=list)


class TripCreate(TripBase):
    id: Optional[str] = None


class Trip(TripBase, MongoBaseModel):
    id: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
