from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class FlightSegment(BaseModel):
    flight_id: str
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    status: str = "SCHEDULED"
    seat: Optional[str] = None
    gate: Optional[str] = None
    terminal: Optional[str] = None
    class_of_service: str = "Economy"


class FlightOption(BaseModel):
    option_id: str
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    stops: int = 0
    fare: float = 0.0
    extra_fare: float = 0.0
    cabin: str = "Economy"
    connecting_flights: List[FlightSegment] = Field(default_factory=list)
    available_seats: int = 9
    carrier_policy_compliant: bool = True
