import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from app.schemas.hotel import HotelImpactResult

logger = logging.getLogger("app.integrations.hotel")


class HotelProvider(ABC):
    @abstractmethod
    async def check_availability(
        self,
        hotel_id: str,
        check_in: datetime,
        check_out: datetime,
    ) -> bool:
        """Check room availability for target dates."""
        pass

    @abstractmethod
    async def modify_reservation(
        self,
        booking_id: str,
        new_check_in: datetime,
        new_check_out: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Modify existing hotel reservation dates."""
        pass

    @abstractmethod
    async def search_alternatives(
        self,
        city: str,
        check_in: datetime,
        check_out: datetime,
    ) -> List[Dict[str, Any]]:
        """Search alternative hotel accommodations if modification fails."""
        pass


class MockHotelProvider(HotelProvider):
    async def check_availability(
        self,
        hotel_id: str,
        check_in: datetime,
        check_out: datetime,
    ) -> bool:
        logger.info("Checking mock hotel availability for hotel %s: %s to %s", hotel_id, check_in, check_out)
        return True

    async def modify_reservation(
        self,
        booking_id: str,
        new_check_in: datetime,
        new_check_out: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        logger.info("Modifying mock reservation %s: new check-in %s", booking_id, new_check_in)
        return {
            "booking_id": booking_id,
            "status": "MODIFIED",
            "confirmed_check_in": new_check_in.isoformat(),
            "notes": notes or "Automated adjustment due to flight delay/rebooking",
            "modification_fee": 0.0,
        }

    async def search_alternatives(
        self,
        city: str,
        check_in: datetime,
        check_out: datetime,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "hotel_name": "Hilton London Tower Bridge",
                "city": city,
                "nightly_rate": 220.0,
                "rating": 4.6,
                "available": True,
            },
            {
                "hotel_name": "London Marriott Hotel Regents Park",
                "city": city,
                "nightly_rate": 195.0,
                "rating": 4.4,
                "available": True,
            },
        ]


mock_hotel_provider = MockHotelProvider()
