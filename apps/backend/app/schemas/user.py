from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.common import MongoBaseModel, utc_now


class UserBase(BaseModel):
    name: str = "Demo Traveler"
    email: str = "traveler@example.com"
    hashed_password: Optional[str] = None
    phone: Optional[str] = "+1-555-0199"
    loyalty_tier: Optional[str] = "Gold"
    preferences: Dict[str, Any] = Field(
        default_factory=lambda: {
            "seat": "aisle",
            "meal": "vegetarian",
            "airline_loyalty": "Star Alliance",
            "max_layover_hours": 4,
        }
    )


class UserCreate(UserBase):
    id: Optional[str] = None


class User(UserBase, MongoBaseModel):
    id: str
    created_at: datetime = Field(default_factory=utc_now)
