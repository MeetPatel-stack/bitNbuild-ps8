from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.common import MongoBaseModel, utc_now


class DisruptionType(str, Enum):
    FLIGHT_CANCELLATION = "FLIGHT_CANCELLATION"
    FLIGHT_DELAY = "FLIGHT_DELAY"
    MISSED_CONNECTION = "MISSED_CONNECTION"


class DisruptionStatus(str, Enum):
    DETECTED = "DETECTED"
    PROCESSING = "PROCESSING"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"


class DisruptionBase(BaseModel):
    trip_id: str
    flight_id: str
    disruption_type: DisruptionType = DisruptionType.FLIGHT_CANCELLATION
    reason: Optional[str] = "Flight cancelled by airline due to operational constraints"
    status: DisruptionStatus = DisruptionStatus.DETECTED
    impact_summary: Optional[str] = None
    worker_dispatch_status: str = "PENDING"  # PENDING, DISPATCHED, FAILED
    worker_dispatch_error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DisruptionCreate(DisruptionBase):
    id: Optional[str] = None


class Disruption(DisruptionBase, MongoBaseModel):
    id: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DisruptionSimulationRequest(BaseModel):
    trip_id: str
    flight_id: str
    reason: Optional[str] = "Severe convective weather alert at origin airport"


class DisruptionSimulationResponse(BaseModel):
    disruption_id: str
    trip_id: str
    flight_id: str
    status: DisruptionStatus
    message: str
    worker_dispatched: bool
    worker_dispatch_status: str
    timeline_event_id: Optional[str] = None
