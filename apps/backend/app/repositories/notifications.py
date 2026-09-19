from typing import Optional, Dict, Any, List, Tuple
from app.database import db_manager
from app.repositories.base import BaseRepository
from app.schemas.common import serialize_doc, utc_now


class NotificationRepository(BaseRepository):
    def __init__(self):
        super().__init__(db_manager.notifications)

    def create_or_get(self, notification_dict: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Idempotent notification creation:
        If idempotency_key is present and already exists, returns (existing, False).
        Otherwise creates new document and returns (new_doc, True).
        """
        idempotency_key = notification_dict.get("idempotency_key")
        if idempotency_key:
            existing = self.collection.find_one({"idempotency_key": idempotency_key})
            if existing:
                return serialize_doc(existing), False

        doc = dict(notification_dict)
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

    def find_by_trip(self, trip_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"trip_id": trip_id}).sort("created_at", -1)
        return [serialize_doc(doc) for doc in cursor]

    def get_by_id(self, notif_id: str) -> Optional[Dict[str, Any]]:
        return self.find_by_id(notif_id)


notification_repo = NotificationRepository()
