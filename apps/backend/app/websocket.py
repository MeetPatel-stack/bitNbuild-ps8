import json
import logging
from typing import Dict, List
from fastapi import WebSocket
from app.schemas.common import serialize_doc

logger = logging.getLogger("app.websocket")


class ConnectionManager:
    def __init__(self):
        # Maps trip_id -> list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, trip_id: str):
        await websocket.accept()
        if trip_id not in self.active_connections:
            self.active_connections[trip_id] = []
        self.active_connections[trip_id].append(websocket)
        logger.info("WebSocket client connected to trip %s (total: %d)", trip_id, len(self.active_connections[trip_id]))

    def disconnect(self, websocket: WebSocket, trip_id: str):
        if trip_id in self.active_connections:
            if websocket in self.active_connections[trip_id]:
                self.active_connections[trip_id].remove(websocket)
            if not self.active_connections[trip_id]:
                del self.active_connections[trip_id]
        logger.info("WebSocket client disconnected from trip %s", trip_id)

    async def broadcast_to_trip(self, trip_id: str, data: dict):
        connections = self.active_connections.get(trip_id, [])
        if not connections:
            return

        serialized = serialize_doc(data)
        stale_connections = []

        for conn in list(connections):
            try:
                await conn.send_json(serialized)
            except Exception as e:
                logger.warning("Error sending WebSocket message to trip %s client: %s", trip_id, e)
                stale_connections.append(conn)

        for stale in stale_connections:
            self.disconnect(stale, trip_id)


ws_manager = ConnectionManager()
