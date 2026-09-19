from typing import Optional, Dict, Any, Tuple, List
from app.database import db_manager
from app.repositories.base import BaseRepository
from app.schemas.common import serialize_doc, utc_now


class RebookingRepository(BaseRepository):
    def __init__(self):
        super().__init__(db_manager.rebookings)

    def create_or_get(self, rebooking_dict: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Idempotent insertion:
        If a rebooking exists with the same disruption_id (or idempotency_key), returns existing.
        Returns: (doc, created: bool)
        """
        disruption_id = rebooking_dict.get("disruption_id")
        idempotency_key = rebooking_dict.get("idempotency_key")

        # Check existing by disruption_id
        if disruption_id:
            existing = self.collection.find_one({"disruption_id": disruption_id})
            if existing:
                return serialize_doc(existing), False

        # Check existing by idempotency_key
        if idempotency_key:
            existing = self.collection.find_one({"idempotency_key": idempotency_key})
            if existing:
                return serialize_doc(existing), False

        doc = dict(rebooking_dict)
        doc.setdefault("created_at", utc_now())
        
        if "id" in doc and doc["id"]:
            custom_id = doc.pop("id")
            doc["_id"] = custom_id
            self.collection.replace_one({"_id": custom_id}, doc, upsert=True)
            saved = self.collection.find_one({"_id": custom_id})
        else:
            res = self.collection.insert_one(doc)
            saved = self.collection.find_one({"_id": res.inserted_id})
            
        return serialize_doc(saved), True

    def get_by_disruption(self, disruption_id: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"disruption_id": disruption_id})
        return serialize_doc(doc) if doc else None

    def get_by_id(self, rebooking_id: str) -> Optional[Dict[str, Any]]:
        return self.find_by_id(rebooking_id)

    def find_by_trip(self, trip_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"trip_id": trip_id}).sort("created_at", -1)
        return [serialize_doc(doc) for doc in cursor]


rebooking_repo = RebookingRepository()
