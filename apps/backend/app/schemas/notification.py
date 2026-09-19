from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.common import MongoBaseModel, utc_now


class NotificationBase(BaseModel):
    user_id: str = "demo-user-1"
    trip_id: str
    disruption_id: Optional[str] = None
    channel: str = "SMS"  # SMS, EMAIL, PUSH, WHATSAPP
    recipient: str = "+1-555-0199"
    title: str
    message: str
    status: str = "SENT"  # QUEUED, SENT, DELIVERED, FAILED
    idempotency_key: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationCreateRequest(NotificationBase):
    pass


class Notification(NotificationBase, MongoBaseModel):
    id: str
    created_at: datetime = Field(default_factory=utc_now)
