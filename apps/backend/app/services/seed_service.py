import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from app.repositories.users import user_repo
from app.repositories.trips import trip_repo
from app.repositories.hotel_bookings import hotel_booking_repo
from app.repositories.timeline import timeline_repo

logger = logging.getLogger("app.services.seed")

DEMO_USER_ID = "demo-user-1"
DEMO_TRIP_ID = "demo-trip-amd-lhr"
DEMO_HOTEL_ID = "hotel-london-langham"


def seed_demo_data(force: bool = False) -> Dict[str, Any]:
    """
    Seeds demo traveler, trip (AMD -> DEL -> LHR) with two connected flights and one London hotel booking.
    """
    # 1. Seed demo user
    user_doc = {
        "id": DEMO_USER_ID,
        "name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "phone": "+91-98765-43210",
        "loyalty_tier": "Gold",
        "preferences": {
            "seat": "aisle",
            "meal": "Asian Vegetarian",
            "airline_loyalty": "Star Alliance",
            "max_layover_hours": 4,
            "hotel_bed": "king",
        },
    }
    user = user_repo.create_or_update(user_doc)

    # 2. Seed hotel booking in London
    now = datetime.now(timezone.utc)
    check_in = now + timedelta(days=2, hours=4)
    check_out = check_in + timedelta(days=3)

    hotel_doc = {
        "id": DEMO_HOTEL_ID,
        "trip_id": DEMO_TRIP_ID,
        "hotel_name": "The Langham, London",
        "city": "London",
        "address": "1C Portland Place, Regent Street, London W1B 1JA, United Kingdom",
        "check_in": check_in,
        "check_out": check_out,
        "room_type": "Executive King Room",
        "booking_reference": "LNGHM-88492-UK",
        "status": "CONFIRMED",
        "contact_phone": "+44 20 7636 1000",
    }
    hotel = hotel_booking_repo.create(hotel_doc)

    # 3. Seed connected flight segments: AMD -> DEL and DEL -> LHR
    flight_1_dep = now + timedelta(days=1, hours=20)
    flight_1_arr = flight_1_dep + timedelta(hours=1, minutes=45)
    flight_2_dep = flight_1_arr + timedelta(hours=2, minutes=30)
    flight_2_arr = flight_2_dep + timedelta(hours=9, minutes=15)

    trip_doc = {
        "id": DEMO_TRIP_ID,
        "user_id": DEMO_USER_ID,
        "title": "Ahmedabad to London Journey",
        "origin": "AMD",
        "destination": "LHR",
        "status": "CONFIRMED",
        "flights": [
            {
                "flight_id": "flight-amd-del-01",
                "airline": "Air India",
                "flight_number": "AI-401",
                "origin": "AMD",
                "destination": "DEL",
                "departure_time": flight_1_dep,
                "arrival_time": flight_1_arr,
                "status": "SCHEDULED",
                "seat": "12C",
                "gate": "3B",
                "terminal": "T1",
                "class_of_service": "Economy",
            },
            {
                "flight_id": "flight-del-lhr-02",
                "airline": "Air India",
                "flight_number": "AI-161",
                "origin": "DEL",
                "destination": "LHR",
                "departure_time": flight_2_dep,
                "arrival_time": flight_2_arr,
                "status": "SCHEDULED",
                "seat": "24D",
                "gate": "18",
                "terminal": "T3",
                "class_of_service": "Economy",
            },
        ],
        "hotel_booking_ids": [DEMO_HOTEL_ID],
    }

    trip = trip_repo.create(trip_doc)

    logger.info("Demo data seeded: Trip %s, User %s, Hotel %s", DEMO_TRIP_ID, DEMO_USER_ID, DEMO_HOTEL_ID)

    return {
        "user": user,
        "trip": trip,
        "hotel": hotel,
        "message": "Demo trip (Ahmedabad -> Delhi -> London) successfully seeded.",
    }
