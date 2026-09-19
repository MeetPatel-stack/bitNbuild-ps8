from typing import Any, Optional
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from app.schemas.common import serialize_doc


class BaseRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    @staticmethod
    def to_object_id(id_str: str) -> Optional[ObjectId]:
        try:
            return ObjectId(id_str)
        except (InvalidId, TypeError):
            return None

    def find_by_id(self, id_str: str) -> Optional[dict[str, Any]]:
        oid = self.to_object_id(id_str)
        query = {"$or": [{"_id": oid}, {"_id": id_str}, {"id": id_str}]} if oid else {"$or": [{"_id": id_str}, {"id": id_str}]}
        doc = self.collection.find_one(query)
        return serialize_doc(doc) if doc else None

    def delete_by_id(self, id_str: str) -> bool:
        oid = self.to_object_id(id_str)
        query = {"$or": [{"_id": oid}, {"_id": id_str}, {"id": id_str}]} if oid else {"$or": [{"_id": id_str}, {"id": id_str}]}
        res = self.collection.delete_one(query)
        return res.deleted_count > 0
