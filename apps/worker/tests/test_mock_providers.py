import pytest
from datetime import datetime, timezone, timedelta
from app.integrations.flight_search import mock_flight_search_provider
from app.integrations.hotel_provider import mock_hotel_provider
from app.integrations.notification import mock_notification_provider


@pytest.mark.anyio
async def test_mock_flight_search_provider():
    now = datetime.now(timezone.utc)
    results = await mock_flight_search_provider.search_alternatives(
        origin="AMD",
        destination="LHR",
        earliest_departure=now,
        cabin_class="Economy",
    )

    assert len(results) >= 3
    # Check required fields on each option
    for opt in results:
        assert opt.flight_number
        assert opt.origin == "AMD"
        assert opt.destination == "LHR"
        assert opt.departure
        assert opt.arrival
        assert opt.stops >= 0
        assert opt.fare > 0
        assert opt.cabin in ["Economy", "Business"]
        assert opt.airline


@pytest.mark.anyio
async def test_mock_hotel_provider():
    now = datetime.now(timezone.utc)
    # Check availability
    avail = await mock_hotel_provider.check_availability(
        hotel_id="hotel-london-langham",
        check_in=now + timedelta(days=2),
        check_out=now + timedelta(days=5),
    )
    assert avail is True

    # Modify reservation
    mod = await mock_hotel_provider.modify_reservation(
        booking_id="hotel-london-langham",
        new_check_in=now + timedelta(days=3),
        notes="Delayed flight arrival",
    )
    assert mod["status"] == "MODIFIED"
    assert mod["booking_id"] == "hotel-london-langham"


@pytest.mark.anyio
async def test_mock_notification_provider():
    res = await mock_notification_provider.send_message(
        recipient="+91-98765-43210",
        title="Flight Cancelled",
        message="Your flight has been rebooked.",
        channel="SMS",
    )
    assert res["delivered"] is True
    assert res["status"] == "DELIVERED"
    assert res["channel"] == "SMS"
