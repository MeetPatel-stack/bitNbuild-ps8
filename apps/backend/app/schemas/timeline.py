from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.common import MongoBaseModel, utc_now


class TimelineEventType(str, Enum):
    DISRUPTION_DETECTED = "DISRUPTION_DETECTED"
    IMPACT_ANALYZED = "IMPACT_ANALYZED"
    FLIGHTS_SEARCHED = "FLIGHTS_SEARCHED"
    POLICY_CHECKED = "POLICY_CHECKED"
    REBOOKING_STARTED = "REBOOKING_STARTED"
    REBOOKING_CONFIRMED = "REBOOKING_CONFIRMED"
    HOTEL_UPDATE_STARTED = "HOTEL_UPDATE_STARTED"
    HOTEL_UPDATE_CONFIRMED = "HOTEL_UPDATE_CONFIRMED"
    NOTIFICATION_SENT = "NOTIFICATION_SENT"
    PROCESS_COMPLETED = "PROCESS_COMPLETED"
    PROCESS_FAILED = "PROCESS_FAILED"


class TimelineEventBase(BaseModel):
    trip_id: str
    disruption_id: Optional[str] = None
    event_type: TimelineEventType
    title: str
    description: str
    severity: str = "INFO"  # INFO, WARNING, CRITICAL, SUCCESS
    payload: Dict[str, Any] = Field(default_factory=dict)


class TimelineEventCreateRequest(BaseModel):
    trip_id: str
    disruption_id: Optional[str] = None
    event_type: TimelineEventType
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = "INFO"
    payload: Optional[Dict[str, Any]] = None


class TimelineEvent(TimelineEventBase, MongoBaseModel):
    id: str
    created_at: datetime = Field(default_factory=utc_now)
