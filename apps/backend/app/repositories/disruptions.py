from typing import Optional, Dict, Any, List
from app.database import db_manager
from app.repositories.base import BaseRepository
from app.schemas.common import serialize_doc, utc_now


class DisruptionRepository(BaseRepository):
    def __init__(self):
        super().__init__(db_manager.disruptions)

    def create(self, disruption_dict: Dict[str, Any]) -> Dict[str, Any]:
        doc = dict(disruption_dict)
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

    def get_by_id(self, disruption_id: str) -> Optional[Dict[str, Any]]:
        return self.find_by_id(disruption_id)

    def update_status(
        self,
        disruption_id: str,
        status: Optional[str] = None,
        worker_dispatch_status: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        oid = self.to_object_id(disruption_id)
        query = {"$or": [{"_id": oid}, {"_id": disruption_id}, {"id": disruption_id}]} if oid else {"$or": [{"_id": disruption_id}, {"id": disruption_id}]}
        
        updates: Dict[str, Any] = {"updated_at": utc_now()}
        if status:
            updates["status"] = status
        if worker_dispatch_status:
            updates["worker_dispatch_status"] = worker_dispatch_status
        if error is not None:
            updates["worker_dispatch_error"] = error

        self.collection.update_one(query, {"$set": updates})
        updated = self.collection.find_one(query)
        return serialize_doc(updated) if updated else None

    def find_by_trip(self, trip_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"trip_id": trip_id}).sort("created_at", -1)
        return [serialize_doc(doc) for doc in cursor]


disruption_repo = DisruptionRepository()
