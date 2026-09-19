from typing import Optional, Dict, Any, List
from app.database import db_manager
from app.repositories.base import BaseRepository
from app.schemas.common import serialize_doc, utc_now


class TimelineRepository(BaseRepository):
    def __init__(self):
        super().__init__(db_manager.timeline_events)

    def create(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        doc = dict(event_dict)
        doc.setdefault("created_at", utc_now())

        if "id" in doc and doc["id"]:
            custom_id = doc.pop("id")
            doc["_id"] = custom_id
            self.collection.replace_one({"_id": custom_id}, doc, upsert=True)
            saved = self.collection.find_one({"_id": custom_id})
        else:
            res = self.collection.insert_one(doc)
            saved = self.collection.find_one({"_id": res.inserted_id})
        return serialize_doc(saved)

    def find_by_trip(self, trip_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"trip_id": trip_id}).sort("created_at", 1)
        return [serialize_doc(doc) for doc in cursor]

    def get_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        return self.find_by_id(event_id)


timeline_repo = TimelineRepository()
