from typing import Optional, Dict, Any, List, Tuple
from bson import ObjectId
from app.database import db_manager
from app.repositories.base import BaseRepository
from app.schemas.common import serialize_doc, utc_now


class HotelBookingRepository(BaseRepository):
    def __init__(self):
        super().__init__(db_manager.hotel_bookings)

    def create(self, hotel_dict: Dict[str, Any]) -> Dict[str, Any]:
        doc = dict(hotel_dict)
        now = utc_now()
        doc.setdefault("created_at", now)
        doc["updated_at"] = now

        if "id" in doc and doc["id"]:
            custom_id = doc.pop("id")
            doc["_id"] = custom_id
            self.collection.replace_one({"_id": custom_id}, doc, upsert=True)
            saved = self.collection.find_one({"_id": custom_id})
        else:
            res = self.collection.insert_one(doc)
            saved = self.collection.find_one({"_id": res.inserted_id})
        return serialize_doc(saved)

    def get_by_id(self, booking_id: str) -> Optional[Dict[str, Any]]:
        return self.find_by_id(booking_id)

    def find_by_trip(self, trip_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"trip_id": trip_id}).sort("created_at", 1)
        return [serialize_doc(doc) for doc in cursor]

    def update_hotel_booking(
        self,
        trip_id: str,
        hotel_booking_id: Optional[str] = None,
        new_check_in: Optional[Any] = None,
        new_check_out: Optional[Any] = None,
        status: Optional[str] = None,
        notes: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Updates the hotel booking for the trip.
        If idempotency_key was already processed on this booking, return (doc, False).
        Returns: (updated_doc, modified: bool)
        """
        # Find booking for trip
        query: Dict[str, Any] = {"trip_id": trip_id}
        if hotel_booking_id:
            oid = self.to_object_id(hotel_booking_id)
            query["$or"] = [{"_id": oid}, {"_id": hotel_booking_id}, {"id": hotel_booking_id}] if oid else [{"_id": hotel_booking_id}, {"id": hotel_booking_id}]

        existing = self.collection.find_one(query)
        if not existing:
            # Try to find any hotel booking for this trip
            existing = self.collection.find_one({"trip_id": trip_id})

        if not existing:
            return None, False

        # Idempotency check: if already has this idempotency_key
        if idempotency_key and existing.get("last_idempotency_key") == idempotency_key:
            return serialize_doc(existing), False

        updates: Dict[str, Any] = {
            "updated_at": utc_now(),
        }
        if new_check_in:
            updates["check_in"] = new_check_in
        if new_check_out:
            updates["check_out"] = new_check_out
        if status:
            updates["status"] = status
        else:
            updates["status"] = "MODIFIED"
        if notes:
            updates["notes"] = notes
        if idempotency_key:
            updates["last_idempotency_key"] = idempotency_key

        self.collection.update_one({"_id": existing["_id"]}, {"$set": updates})
        updated = self.collection.find_one({"_id": existing["_id"]})
        return serialize_doc(updated), True


hotel_booking_repo = HotelBookingRepository()
