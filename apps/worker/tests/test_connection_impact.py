from datetime import datetime, timezone, timedelta
from app.agents.connection_analyzer import connection_analyzer


def test_primary_cancellation_and_downstream_broken_connection():
    """
    Test scenario:
    Ahmedabad (AMD) -> Delhi (DEL)
    Delhi (DEL) -> London (LHR)
    When AMD -> DEL is cancelled, DEL -> LHR must be marked as affected due to broken connection.
    """
    now = datetime.now(timezone.utc)
    flights = [
        {
            "flight_id": "flight-amd-del-01",
            "airline": "Air India",
            "flight_number": "AI-401",
            "origin": "AMD",
            "destination": "DEL",
            "departure_time": (now + timedelta(hours=2)).isoformat(),
            "arrival_time": (now + timedelta(hours=3, minutes=45)).isoformat(),
            "status": "CANCELLED",
        },
        {
            "flight_id": "flight-del-lhr-02",
            "airline": "Air India",
            "flight_number": "AI-161",
            "origin": "DEL",
            "destination": "LHR",
            "departure_time": (now + timedelta(hours=6)).isoformat(),
            "arrival_time": (now + timedelta(hours=15)).isoformat(),
            "status": "SCHEDULED",
        },
    ]

    affected, summary = connection_analyzer.analyze_impact(
        flights=flights,
        disrupted_flight_id="flight-amd-del-01",
        min_connection_minutes=60,
    )

    assert len(affected) == 2
    # First flight is primary cancellation
    assert affected[0]["flight_id"] == "flight-amd-del-01"
    assert affected[0]["impact_type"] == "PRIMARY_CANCELLATION"

    # Second flight is downstream broken connection
    assert affected[1]["flight_id"] == "flight-del-lhr-02"
    assert affected[1]["impact_type"] == "MISSED_CONNECTION"
    assert "AI-401" in summary


def test_illegal_connection_time_detection():
    """
    Test scenario:
    Leg 1 arrives at 10:00. Leg 2 departs at 10:30 (layover 30 mins, below min threshold 60 mins).
    Leg 2 must be detected as an illegal connection time.
    """
    now = datetime.now(timezone.utc)
    leg1_arr = now + timedelta(hours=2)
    leg2_dep = leg1_arr + timedelta(minutes=25)  # 25 min layover < 60 min required

    flights = [
        {
            "flight_id": "flight-1",
            "flight_number": "AI-101",
            "origin": "BOM",
            "destination": "DEL",
            "departure_time": (now + timedelta(hours=1)).isoformat(),
            "arrival_time": leg1_arr.isoformat(),
            "status": "SCHEDULED",
        },
        {
            "flight_id": "flight-2",
            "flight_number": "AI-102",
            "origin": "DEL",
            "destination": "JFK",
            "departure_time": leg2_dep.isoformat(),
            "arrival_time": (leg2_dep + timedelta(hours=14)).isoformat(),
            "status": "SCHEDULED",
        },
    ]

    affected, summary = connection_analyzer.analyze_impact(
        flights=flights,
        disrupted_flight_id="none",
        min_connection_minutes=60,
    )

    assert len(affected) == 1
    assert affected[0]["flight_id"] == "flight-2"
    assert affected[0]["impact_type"] == "ILLEGAL_CONNECTION_TIME"
