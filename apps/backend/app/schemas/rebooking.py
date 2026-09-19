from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.common import MongoBaseModel, utc_now
from app.schemas.trip import FlightSegment


class RebookingBase(BaseModel):
    disruption_id: str
    trip_id: str
    original_flight_id: str
    new_flights: List[FlightSegment] = Field(default_factory=list)
    status: str = "CONFIRMED"
    airline: Optional[str] = None
    booking_reference: Optional[str] = None
    cost_difference: float = 0.0
    policy_compliance_notes: Optional[str] = "Within airline travel disruption waiver policy"
    idempotency_key: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RebookingCreateRequest(RebookingBase):
    pass


class Rebooking(RebookingBase, MongoBaseModel):
    id: str
    created_at: datetime = Field(default_factory=utc_now)
