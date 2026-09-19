from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ProcessDisruptionRequest(BaseModel):
    trip_id: str
    disruption_id: str


class ProcessDisruptionResponse(BaseModel):
    trip_id: str
    disruption_id: str
    status: str
    success: bool
    requires_approval: bool = False
    approval_reason: Optional[str] = None
    selected_option: Optional[Dict[str, Any]] = None
    rebooking_result: Optional[Dict[str, Any]] = None
    hotel_result: Optional[Dict[str, Any]] = None
    notification_result: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
