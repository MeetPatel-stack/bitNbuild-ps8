from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_websocket_connection_and_handshake():
    trip_id = "demo-trip-amd-lhr"
    with client.websocket_connect(f"/ws/trips/{trip_id}") as websocket:
        # Check initial connection handshake
        data = websocket.receive_json()
        assert data["type"] == "CONNECTION_ESTABLISHED"
        assert data["trip_id"] == trip_id

        # Send ping, receive pong
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert response == "pong"
