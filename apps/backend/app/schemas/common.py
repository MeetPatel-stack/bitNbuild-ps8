from datetime import datetime, timezone
from typing import Any
from bson import ObjectId
from pydantic import BaseModel, ConfigDict


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def serialize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    """Helper to convert MongoDB BSON doc to JSON-serializable dictionary."""
    if not doc:
        return doc
    res = dict(doc)
    if "_id" in res:
        res["id"] = str(res.pop("_id"))
    for k, v in res.items():
        if isinstance(v, ObjectId):
            res[k] = str(v)
        elif isinstance(v, datetime):
            res[k] = v.isoformat()
        elif isinstance(v, list):
            res[k] = [
                serialize_doc(item) if isinstance(item, dict) else (str(item) if isinstance(item, ObjectId) else item)
                for item in v
            ]
        elif isinstance(v, dict):
            res[k] = serialize_doc(v)
    return res


class MongoBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
