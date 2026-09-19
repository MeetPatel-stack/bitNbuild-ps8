from datetime import datetime, timezone, timedelta
import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_process_events_endpoint():
    client.post("/api/demo/seed")

    event_payload = {
        "trip_id": "demo-trip-amd-lhr",
        "event_type": "FLIGHTS_SEARCHED",
        "title": "Alternative Flight Options Found",
        "description": "Found 3 alternative flight routes via Mumbai and Doha",
        "severity": "INFO",
        "payload": {"alternatives_count": 3},
    }

    res = client.post("/api/internal/process-events", json=event_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["event_type"] == "FLIGHTS_SEARCHED"
    assert data["trip_id"] == "demo-trip-amd-lhr"
    assert data["payload"]["alternatives_count"] == 3


def test_rebookings_endpoint_and_idempotency():
    client.post("/api/demo/seed")
    unique_disruption_id = f"disrupt-test-{uuid.uuid4().hex[:6]}"
    now = datetime.now(timezone.utc)

    rebooking_payload = {
        "disruption_id": unique_disruption_id,
        "trip_id": "demo-trip-amd-lhr",
        "original_flight_id": "flight-amd-del-01",
        "airline": "Air India",
        "booking_reference": "AI-REBOOK-991",
        "cost_difference": 0.0,
        "new_flights": [
            {
                "flight_id": f"new-flight-{uuid.uuid4().hex[:6]}",
                "airline": "Air India",
                "flight_number": "AI-802",
                "origin": "AMD",
                "destination": "DEL",
                "departure_time": (now + timedelta(hours=3)).isoformat(),
                "arrival_time": (now + timedelta(hours=4, minutes=45)).isoformat(),
                "status": "SCHEDULED",
                "seat": "14B",
            }
        ],
    }

    # 1. First request -> created
    res1 = client.post("/api/internal/rebookings", json=rebooking_payload)
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["is_new"] is True
    assert data1["rebooking"]["disruption_id"] == unique_disruption_id

    # 2. Second request with same disruption_id -> idempotent (is_new is False)
    res2 = client.post("/api/internal/rebookings", json=rebooking_payload)
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["is_new"] is False
    assert data2["rebooking"]["id"] == data1["rebooking"]["id"]


def test_hotel_updates_endpoint_and_idempotency():
    client.post("/api/demo/seed")
    idempotency_key = f"idem-hotel-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    new_check_in = (now + timedelta(days=3)).isoformat()

    hotel_payload = {
        "trip_id": "demo-trip-amd-lhr",
        "new_check_in": new_check_in,
        "status": "MODIFIED",
        "notes": "Flight delayed, check-in pushed back 24 hours",
        "idempotency_key": idempotency_key,
    }

    # First update
    res1 = client.post("/api/internal/hotel-updates", json=hotel_payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["modified"] is True
    assert data1["hotel"]["city"] == "London"

    # Second update with same idempotency key -> idempotent (modified is False)
    res2 = client.post("/api/internal/hotel-updates", json=hotel_payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["modified"] is False


def test_notifications_endpoint_and_idempotency():
    client.post("/api/demo/seed")
    idempotency_key = f"idem-notif-{uuid.uuid4().hex[:8]}"

    notif_payload = {
        "trip_id": "demo-trip-amd-lhr",
        "channel": "SMS",
        "recipient": "+91-98765-43210",
        "title": "Flight Cancelled - Rebooking in Progress",
        "message": "Your flight AI-401 has been cancelled. Our concierge is rebooking you automatically.",
        "idempotency_key": idempotency_key,
    }

    # First notification
    res1 = client.post("/api/internal/notifications", json=notif_payload)
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["is_new"] is True

    # Second notification with same idempotency_key -> duplicate ignored
    res2 = client.post("/api/internal/notifications", json=notif_payload)
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["is_new"] is False
    assert data2["notification"]["id"] == data1["notification"]["id"]
