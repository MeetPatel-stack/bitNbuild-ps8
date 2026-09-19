from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app, processed_disruptions
from app.graph.workflow import disruption_workflow

client = TestClient(app)


def test_worker_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "autonomous-worker"
    assert "max_extra_fare" in data


def test_process_disruption_idempotency():
    processed_disruptions.clear()
    trip_id = "test-idem-trip"
    disruption_id = "test-idem-disrupt-1"

    mock_final_state = {
        "trip_id": trip_id,
        "disruption_id": disruption_id,
        "status": "COMPLETED",
        "requires_approval": False,
        "selected_option": {"flight_number": "AI-403"},
        "rebooking_result": {"status": "CONFIRMED"},
        "hotel_result": {"status": "MODIFIED"},
        "notification_result": {"status": "DELIVERED"},
        "explanation": "Test explanation",
        "errors": [],
    }

    with patch.object(disruption_workflow, "ainvoke", AsyncMock(return_value=mock_final_state)) as mock_invoke:
        # First call
        res1 = client.post(
            "/internal/process-disruption",
            json={"trip_id": trip_id, "disruption_id": disruption_id},
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["status"] == "COMPLETED"
        assert mock_invoke.call_count == 1

        # Second call with same trip_id & disruption_id -> returns cached without re-invoking workflow
        res2 = client.post(
            "/internal/process-disruption",
            json={"trip_id": trip_id, "disruption_id": disruption_id},
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["status"] == "COMPLETED"
        assert data2["disruption_id"] == disruption_id
        # Call count should STILL be 1 (idempotent!)
        assert mock_invoke.call_count == 1
