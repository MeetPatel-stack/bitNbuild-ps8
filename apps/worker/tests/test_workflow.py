import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
from app.graph.workflow import disruption_workflow
from app.services.backend_client import backend_client


@pytest.mark.anyio
async def test_full_autonomous_workflow_happy_path():
    """
    Test full happy path:
    flight cancelled
    -> affected connection identified
    -> alternatives searched
    -> policy filtered
    -> best valid alternative selected
    -> rebooking executed
    -> hotel impact checked
    -> hotel updated
    -> notification sent
    -> process completed
    """
    now = datetime.now(timezone.utc)
    mock_trip = {
        "id": "demo-trip-amd-lhr",
        "user_id": "demo-user-1",
        "origin": "AMD",
        "destination": "LHR",
        "status": "DISRUPTED",
        "flights": [
            {
                "flight_id": "flight-amd-del-01",
                "airline": "Air India",
                "flight_number": "AI-401",
                "origin": "AMD",
                "destination": "DEL",
                "departure_time": (now + timedelta(hours=1)).isoformat(),
                "arrival_time": (now + timedelta(hours=2, minutes=45)).isoformat(),
                "status": "CANCELLED",
            },
            {
                "flight_id": "flight-del-lhr-02",
                "airline": "Air India",
                "flight_number": "AI-161",
                "origin": "DEL",
                "destination": "LHR",
                "departure_time": (now + timedelta(hours=5)).isoformat(),
                "arrival_time": (now + timedelta(hours=14)).isoformat(),
                "status": "SCHEDULED",
            },
        ],
        "hotels": [
            {
                "id": "hotel-london-langham",
                "hotel_name": "The Langham, London",
                "city": "London",
                "check_in": (now + timedelta(hours=15)).isoformat(),
                "check_out": (now + timedelta(days=3)).isoformat(),
            }
        ],
    }

    with patch.object(backend_client, "get_trip", AsyncMock(return_value=mock_trip)), \
         patch.object(backend_client, "send_process_event", AsyncMock(return_value={"status": "ok"})), \
         patch.object(backend_client, "create_rebooking", AsyncMock(return_value={"rebooking_id": "reb-101", "status": "CONFIRMED"})), \
         patch.object(backend_client, "update_hotel", AsyncMock(return_value={"hotel_id": "hotel-london-langham", "status": "MODIFIED"})), \
         patch.object(backend_client, "record_notification", AsyncMock(return_value={"notification_id": "notif-101", "status": "SENT"})):

        initial_state = {
            "trip_id": "demo-trip-amd-lhr",
            "disruption_id": "disrupt-test-123",
            "disrupted_flight_id": "flight-amd-del-01",
            "errors": [],
            "status": "INITIALIZED",
            "requires_approval": False,
        }

        final_state = await disruption_workflow.ainvoke(initial_state)

        assert final_state["status"] == "COMPLETED"
        assert len(final_state["affected_segments"]) == 2
        assert len(final_state["valid_options"]) >= 1
        assert final_state["selected_option"] is not None
        assert final_state["rebooking_result"] is not None
        assert final_state["hotel_result"] is not None
        assert final_state["notification_result"] is not None
        assert final_state["requires_approval"] is False
        assert "Air India" in final_state["explanation"]


@pytest.mark.anyio
async def test_workflow_requires_human_approval_when_no_valid_options():
    """
    Test human approval state:
    When all alternatives exceed the maximum extra fare / stops policy,
    the workflow must route to require_human_approval and MUST NOT execute rebooking.
    """
    now = datetime.now(timezone.utc)
    mock_trip = {
        "id": "trip-approval-needed",
        "user_id": "demo-user-1",
        "origin": "AMD",
        "destination": "LHR",
        "status": "DISRUPTED",
        "flights": [
            {
                "flight_id": "flight-1",
                "flight_number": "AI-401",
                "origin": "AMD",
                "destination": "DEL",
                "status": "CANCELLED",
            }
        ],
        "hotels": [],
    }

    # Set mock search provider to return only 1 super-expensive option (> max_extra_fare)
    from app.schemas.flight import FlightOption
    from app.integrations.flight_search import mock_flight_search_provider

    super_expensive_opt = FlightOption(
        option_id="opt-unaffordable",
        airline="Charter Airlines",
        flight_number="CH-001",
        origin="AMD",
        destination="LHR",
        departure=now + timedelta(hours=2),
        arrival=now + timedelta(hours=12),
        stops=1,
        fare=200000.0,
        extra_fare=90000.0,  # Exceeds max 5000
        cabin="Economy",
    )

    with patch.object(backend_client, "get_trip", AsyncMock(return_value=mock_trip)), \
         patch.object(backend_client, "send_process_event", AsyncMock(return_value={"status": "ok"})), \
         patch.object(mock_flight_search_provider, "search_alternatives", AsyncMock(return_value=[super_expensive_opt])), \
         patch.object(backend_client, "create_rebooking", AsyncMock()) as mock_rebook:

        initial_state = {
            "trip_id": "trip-approval-needed",
            "disruption_id": "disrupt-expensive-999",
            "disrupted_flight_id": "flight-1",
            "errors": [],
            "status": "INITIALIZED",
            "requires_approval": False,
        }

        final_state = await disruption_workflow.ainvoke(initial_state)

        # Asserts: Routed to require_human_approval
        assert final_state["status"] == "REQUIRES_APPROVAL"
        assert final_state["requires_approval"] is True
        assert final_state.get("selected_option") is None
        # Verify rebooking was NOT executed
        mock_rebook.assert_not_called()
