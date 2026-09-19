from typing import Optional, Dict, Any
from app.database import db_manager
from app.repositories.base import BaseRepository
from app.schemas.common import serialize_doc, utc_now


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(db_manager.users)

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.find_by_id(user_id)

    def create_or_update(self, user_dict: Dict[str, Any]) -> Dict[str, Any]:
        user_id = user_dict.get("id") or "demo-user-1"
        user_dict["updated_at"] = utc_now()
        if "created_at" not in user_dict:
            user_dict["created_at"] = utc_now()
        
        self.collection.update_one(
            {"$or": [{"_id": user_id}, {"id": user_id}]},
            {"$set": user_dict},
            upsert=True,
        )
        doc = self.collection.find_one({"$or": [{"_id": user_id}, {"id": user_id}]})
        return serialize_doc(doc)


user_repo = UserRepository()
