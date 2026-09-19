from typing import Optional, Dict, Any, List
from bson import ObjectId
from app.database import db_manager
from app.repositories.base import BaseRepository
from app.schemas.common import serialize_doc, utc_now


class TripRepository(BaseRepository):
    def __init__(self):
        super().__init__(db_manager.trips)

    def create(self, trip_dict: Dict[str, Any]) -> Dict[str, Any]:
        doc = dict(trip_dict)
        now = utc_now()
        doc.setdefault("created_at", now)
        doc["updated_at"] = now
        
        # If an explicit string ID was provided, store it or let Mongo generate
        if "id" in doc and doc["id"]:
            custom_id = doc.pop("id")
            doc["_id"] = custom_id
            self.collection.replace_one({"_id": custom_id}, doc, upsert=True)
            saved = self.collection.find_one({"_id": custom_id})
        else:
            res = self.collection.insert_one(doc)
            saved = self.collection.find_one({"_id": res.inserted_id})
        return serialize_doc(saved)

    def get_by_id(self, trip_id: str) -> Optional[Dict[str, Any]]:
        return self.find_by_id(trip_id)

    def update(self, trip_id: str, update_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        oid = self.to_object_id(trip_id)
        query = {"$or": [{"_id": oid}, {"_id": trip_id}, {"id": trip_id}]} if oid else {"$or": [{"_id": trip_id}, {"id": trip_id}]}
        update_dict["updated_at"] = utc_now()
        self.collection.update_one(query, {"$set": update_dict})
        updated = self.collection.find_one(query)
        return serialize_doc(updated) if updated else None

    def update_flight_status(self, trip_id: str, flight_id: str, new_status: str) -> bool:
        oid = self.to_object_id(trip_id)
        query = {
            "$and": [
                {"$or": [{"_id": oid}, {"_id": trip_id}, {"id": trip_id}]} if oid else {"$or": [{"_id": trip_id}, {"id": trip_id}]},
                {"flights.flight_id": flight_id},
            ]
        }
        res = self.collection.update_one(
            query,
            {
                "$set": {
                    "flights.$.status": new_status,
                    "status": "DISRUPTED",
                    "updated_at": utc_now(),
                }
            },
        )
        return res.modified_count > 0

    def apply_rebooking(self, trip_id: str, original_flight_id: str, new_flights: List[Dict[str, Any]]) -> bool:
        trip = self.get_by_id(trip_id)
        if not trip:
            return False

        flights = trip.get("flights", [])
        updated_flights = []
        replaced = False

        for f in flights:
            if f.get("flight_id") == original_flight_id:
                # Mark original as REBOOKED
                f_copy = dict(f)
                f_copy["status"] = "REBOOKED"
                updated_flights.append(f_copy)
                # Append new flights
                for nf in new_flights:
                    updated_flights.append(nf)
                replaced = True
            else:
                updated_flights.append(f)

        if not replaced:
            updated_flights.extend(new_flights)

        oid = self.to_object_id(trip_id)
        query = {"$or": [{"_id": oid}, {"_id": trip_id}, {"id": trip_id}]} if oid else {"$or": [{"_id": trip_id}, {"id": trip_id}]}
        self.collection.update_one(
            query,
            {
                "$set": {
                    "flights": updated_flights,
                    "status": "RESOLVED",
                    "updated_at": utc_now(),
                }
            },
        )
        return True

    def list_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        cursor = self.collection.find().sort("created_at", -1).limit(limit)
        return [serialize_doc(doc) for doc in cursor]


trip_repo = TripRepository()
