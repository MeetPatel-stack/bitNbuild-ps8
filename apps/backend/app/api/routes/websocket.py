import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket import ws_manager

logger = logging.getLogger("app.api.websocket")

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/trips/{trip_id}")
async def websocket_trip_endpoint(websocket: WebSocket, trip_id: str):
    """
    Live WebSocket stream for a trip.
    Connected clients receive real-time timeline events as the disruption concierge operates.
    """
    await ws_manager.connect(websocket, trip_id)
    try:
        # Send initial handshake message
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "trip_id": trip_id,
            "message": f"Subscribed to live timeline events for trip '{trip_id}'",
        })

        # Keep connection open and handle incoming client messages (e.g. ping/heartbeat)
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, trip_id)
    except Exception as e:
        logger.warning("WebSocket error for trip %s: %s", trip_id, e)
        ws_manager.disconnect(websocket, trip_id)
