import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import certifi

from app.config import settings

logger = logging.getLogger("app.database")


class DatabaseManager:
    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

    def connect(self) -> Database:
        if self._client is None:
            logger.info("Connecting to MongoDB Atlas at %s...", settings.mongodb_uri.split("@")[-1] if "@" in settings.mongodb_uri else settings.mongodb_uri)
            self._client = MongoClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
                retryWrites=True,
                tlsCAFile=certifi.where(),
            )
            self._db = self._client[settings.mongodb_database]
            self._init_indexes()
            logger.info("Connected to MongoDB database: %s", settings.mongodb_database)
        return self._db

    def close(self):
        if self._client is not None:
            logger.info("Closing MongoDB connection")
            self._client.close()
            self._client = None
            self._db = None

    @property
    def db(self) -> Database:
        if self._db is None:
            return self.connect()
        return self._db

    def ping(self) -> bool:
        try:
            client = self._client or MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            logger.warning("MongoDB ping failed: %s", e)
            return False

    def _init_indexes(self):
        try:
            db = self._db
            if db is None:
                return
            # Trips
            db["trips"].create_index("user_id")
            db["trips"].create_index("status")
            # Disruptions
            db["disruptions"].create_index("trip_id")
            db["disruptions"].create_index("flight_id")
            # Rebookings
            db["rebookings"].create_index("disruption_id", unique=True)
            db["rebookings"].create_index("trip_id")
            # Hotel Bookings
            db["hotel_bookings"].create_index("trip_id")
            # Timeline Events
            db["timeline_events"].create_index([("trip_id", 1), ("created_at", 1)])
            # Notifications
            db["notifications"].create_index([("trip_id", 1), ("created_at", -1)])
            db["notifications"].create_index("disruption_id")
        except Exception as e:
            logger.warning("Could not ensure indexes: %s", e)

    # Collection accessors
    @property
    def users(self) -> Collection:
        return self.db["users"]

    @property
    def trips(self) -> Collection:
        return self.db["trips"]

    @property
    def disruptions(self) -> Collection:
        return self.db["disruptions"]

    @property
    def rebookings(self) -> Collection:
        return self.db["rebookings"]

    @property
    def hotel_bookings(self) -> Collection:
        return self.db["hotel_bookings"]

    @property
    def timeline_events(self) -> Collection:
        return self.db["timeline_events"]

    @property
    def notifications(self) -> Collection:
        return self.db["notifications"]


db_manager = DatabaseManager()


def get_db() -> Database:
    return db_manager.db
