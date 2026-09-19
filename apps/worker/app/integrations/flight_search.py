import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from app.schemas.flight import FlightOption, FlightSegment

logger = logging.getLogger("app.integrations.flight_search")


class FlightSearchProvider(ABC):
    @abstractmethod
    async def search_alternatives(
        self,
        origin: str,
        destination: str,
        earliest_departure: datetime,
        cabin_class: str = "Economy",
        passenger_count: int = 1,
    ) -> List[FlightOption]:
        """Search available alternative flight itineraries."""
        pass


class MockFlightSearchProvider(FlightSearchProvider):
    async def search_alternatives(
        self,
        origin: str,
        destination: str,
        earliest_departure: datetime,
        cabin_class: str = "Economy",
        passenger_count: int = 1,
    ) -> List[FlightOption]:
        """
        Generates realistic alternative itineraries.
        Produces multiple candidates with varying fares, stops, and cabins
        so policy filtering and scoring can be thoroughly tested.
        """
        logger.info(
            "Searching alternatives from %s to %s starting after %s (cabin: %s)",
            origin,
            destination,
            earliest_departure.isoformat(),
            cabin_class,
        )

        base_time = earliest_departure if earliest_departure.tzinfo else earliest_departure.replace(tzinfo=timezone.utc)

        # Candidate 1: Optimal Policy-Compliant Alternative (Air India via DEL, 1 stop, 0 extra fare)
        leg1_dep = base_time + timedelta(hours=2, minutes=30)
        leg1_arr = leg1_dep + timedelta(hours=1, minutes=45)
        leg2_dep = leg1_arr + timedelta(hours=2, minutes=15)
        leg2_arr = leg2_dep + timedelta(hours=9, minutes=10)

        opt1 = FlightOption(
            option_id="OPT-AI-REPLACE-403",
            airline="Air India",
            flight_number="AI-403 / AI-161",
            origin=origin,
            destination=destination,
            departure=leg1_dep,
            arrival=leg2_arr,
            stops=1,
            fare=32000.0,
            extra_fare=0.0,  # Zero extra cost under airline disruption waiver
            cabin="Economy",
            available_seats=7,
            carrier_policy_compliant=True,
            connecting_flights=[
                FlightSegment(
                    flight_id="ai-403-amd-del",
                    airline="Air India",
                    flight_number="AI-403",
                    origin=origin,
                    destination="DEL",
                    departure_time=leg1_dep,
                    arrival_time=leg1_arr,
                    seat="14C",
                    gate="4A",
                    terminal="T1",
                ),
                FlightSegment(
                    flight_id="ai-161-del-lhr",
                    airline="Air India",
                    flight_number="AI-161",
                    origin="DEL",
                    destination=destination,
                    departure_time=leg2_dep,
                    arrival_time=leg2_arr,
                    seat="22D",
                    gate="19",
                    terminal="T3",
                ),
            ],
        )

        # Candidate 2: Exceeds Extra Fare Policy (Emirates via DXB, extra fare ₹12,000 > ₹5,000 max)
        ek_leg1_dep = base_time + timedelta(hours=3)
        ek_leg1_arr = ek_leg1_dep + timedelta(hours=3, minutes=30)
        ek_leg2_dep = ek_leg1_arr + timedelta(hours=3)
        ek_leg2_arr = ek_leg2_dep + timedelta(hours=7, minutes=45)

        opt2 = FlightOption(
            option_id="OPT-EK-OVER-BUDGET",
            airline="Emirates",
            flight_number="EK-539 / EK-001",
            origin=origin,
            destination=destination,
            departure=ek_leg1_dep,
            arrival=ek_leg2_arr,
            stops=1,
            fare=45000.0,
            extra_fare=13000.0,  # Exceeds max_extra_fare limit of 5000
            cabin="Economy",
            available_seats=4,
            carrier_policy_compliant=False,
            connecting_flights=[
                FlightSegment(
                    flight_id="ek-539-amd-dxb",
                    airline="Emirates",
                    flight_number="EK-539",
                    origin=origin,
                    destination="DXB",
                    departure_time=ek_leg1_dep,
                    arrival_time=ek_leg1_arr,
                ),
                FlightSegment(
                    flight_id="ek-001-dxb-lhr",
                    airline="Emirates",
                    flight_number="EK-001",
                    origin="DXB",
                    destination=destination,
                    departure_time=ek_leg2_dep,
                    arrival_time=ek_leg2_arr,
                ),
            ],
        )

        # Candidate 3: Exceeds Max Stops Policy (2 stops: AMD -> BOM -> DOH -> LHR)
        stop2_dep = base_time + timedelta(hours=4)
        stop2_arr = stop2_dep + timedelta(hours=18)

        opt3 = FlightOption(
            option_id="OPT-TWO-STOPS",
            airline="Qatar Airways",
            flight_number="6E-101 / QR-557 / QR-003",
            origin=origin,
            destination=destination,
            departure=stop2_dep,
            arrival=stop2_arr,
            stops=2,  # Exceeds max_stops limit of 1
            fare=31000.0,
            extra_fare=1000.0,
            cabin="Economy",
            available_seats=3,
            carrier_policy_compliant=True,
            connecting_flights=[],
        )

        # Candidate 4: Cabin Mismatch (Business class when economy requested)
        biz_dep = base_time + timedelta(hours=5)
        biz_arr = biz_dep + timedelta(hours=11)

        opt4 = FlightOption(
            option_id="OPT-BIZ-CLASS",
            airline="British Airways",
            flight_number="BA-142",
            origin=origin,
            destination=destination,
            departure=biz_dep,
            arrival=biz_arr,
            stops=1,
            fare=98000.0,
            extra_fare=60000.0,
            cabin="Business",  # Incompatible cabin class
            available_seats=2,
            carrier_policy_compliant=False,
            connecting_flights=[],
        )

        return [opt1, opt2, opt3, opt4]


mock_flight_search_provider = MockFlightSearchProvider()
