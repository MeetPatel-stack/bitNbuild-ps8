from datetime import datetime, timezone, timedelta
import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_seed_and_get_trip():
    # Trigger seed
    seed_res = client.post("/api/demo/seed")
    assert seed_res.status_code == 200

    # Retrieve demo trip
    trip_res = client.get("/api/trips/demo-trip-amd-lhr")
    assert trip_res.status_code == 200
    trip = trip_res.json()
    assert trip["id"] == "demo-trip-amd-lhr"
    assert trip["origin"] == "AMD"
    assert trip["destination"] == "LHR"
    assert len(trip["flights"]) == 2
    assert "hotels" in trip
    assert len(trip["hotels"]) >= 1
    assert trip["hotels"][0]["city"] == "London"


def test_create_and_retrieve_custom_trip():
    now = datetime.now(timezone.utc)
    unique_flight_id = f"flight-{uuid.uuid4().hex[:6]}"
    trip_payload = {
        "user_id": "test-user-custom",
        "title": "Mumbai to Singapore Business Trip",
        "origin": "BOM",
        "destination": "SIN",
        "status": "CONFIRMED",
        "flights": [
            {
                "flight_id": unique_flight_id,
                "airline": "Singapore Airlines",
                "flight_number": "SQ-421",
                "origin": "BOM",
                "destination": "SIN",
                "departure_time": (now + timedelta(days=5)).isoformat(),
                "arrival_time": (now + timedelta(days=5, hours=5)).isoformat(),
                "status": "SCHEDULED",
                "seat": "14A",
            }
        ],
    }

    create_res = client.post("/api/trips", json=trip_payload)
    assert create_res.status_code == 201
    created = create_res.json()
    trip_id = created["id"]

    get_res = client.get(f"/api/trips/{trip_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["id"] == trip_id
    assert retrieved["title"] == "Mumbai to Singapore Business Trip"
    assert len(retrieved["flights"]) == 1


def test_get_nonexistent_trip():
    res = client.get("/api/trips/non-existent-trip-999")
    assert res.status_code == 404
