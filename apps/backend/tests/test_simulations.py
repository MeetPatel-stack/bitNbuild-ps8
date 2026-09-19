from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_simulation_flight_cancellation_validation():
    # Ensure demo trip is seeded
    client.post("/api/demo/seed")

    # 1. Invalid trip
    res = client.post(
        "/api/simulations/flight-cancellation",
        json={"trip_id": "invalid-trip-id", "flight_id": "flight-amd-del-01"},
    )
    assert res.status_code == 404

    # 2. Invalid flight in valid trip
    res = client.post(
        "/api/simulations/flight-cancellation",
        json={"trip_id": "demo-trip-amd-lhr", "flight_id": "non-existent-flight-id"},
    )
    assert res.status_code == 400


def test_simulation_flight_cancellation_success_and_safe_worker_handling():
    # Ensure demo trip is seeded
    client.post("/api/demo/seed")

    sim_payload = {
        "trip_id": "demo-trip-amd-lhr",
        "flight_id": "flight-amd-del-01",
        "reason": "Severe fog and reduced visibility at Ahmedabad airport",
    }

    res = client.post("/api/simulations/flight-cancellation", json=sim_payload)
    assert res.status_code == 201
    data = res.json()
    assert "disruption_id" in data
    disruption_id = data["disruption_id"]
    assert data["trip_id"] == "demo-trip-amd-lhr"
    assert data["flight_id"] == "flight-amd-del-01"
    # When worker is offline, safe failure handling returns worker_dispatched=False but request succeeds
    assert "worker_dispatched" in data

    # Verify disruption record was created in database
    get_dis_res = client.get(f"/api/disruptions/{disruption_id}")
    assert get_dis_res.status_code == 200
    disruption = get_dis_res.json()
    assert disruption["id"] == disruption_id
    assert disruption["trip_id"] == "demo-trip-amd-lhr"
    assert disruption["flight_id"] == "flight-amd-del-01"

    # Verify flight status was updated to CANCELLED in trip
    trip_res = client.get("/api/trips/demo-trip-amd-lhr")
    assert trip_res.status_code == 200
    trip = trip_res.json()
    cancelled_flight = next((f for f in trip["flights"] if f["flight_id"] == "flight-amd-del-01"), None)
    assert cancelled_flight is not None
    assert cancelled_flight["status"] == "CANCELLED"
    assert trip["status"] == "DISRUPTED"

    # Verify timeline has DISRUPTION_DETECTED event
    timeline_res = client.get("/api/trips/demo-trip-amd-lhr/timeline")
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    assert len(timeline) >= 1
    event_types = [e["event_type"] for e in timeline]
    assert "DISRUPTION_DETECTED" in event_types
