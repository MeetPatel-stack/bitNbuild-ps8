import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("app.agents.connection_analyzer")


def parse_datetime(val: Any) -> datetime:
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, str):
        # Handle ISO strings with Z or offsets
        clean_val = val.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_val)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    raise ValueError(f"Cannot parse datetime: {val}")


class ConnectionAnalyzer:
    @staticmethod
    def analyze_impact(
        flights: List[Dict[str, Any]],
        disrupted_flight_id: str,
        min_connection_minutes: int = 60,
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Deterministically analyzes the chain of flights.
        If a flight is cancelled, all downstream connected segments are affected.
        Also validates that connection times between consecutive segments meet min_connection_minutes.

        Returns: (affected_segments, impact_summary)
        """
        if not flights:
            return [], "No flights in itinerary to analyze."

        affected: List[Dict[str, Any]] = []
        is_disrupted = False
        primary_disrupted_flight = None

        for idx, flight in enumerate(flights):
            fid = flight.get("flight_id")
            fnum = flight.get("flight_number", fid)
            origin = flight.get("origin")
            dest = flight.get("destination")
            status = flight.get("status", "SCHEDULED")

            # Check if this is the cancelled flight
            if fid == disrupted_flight_id or status == "CANCELLED":
                is_disrupted = True
                primary_disrupted_flight = flight
                affected.append({
                    **flight,
                    "impact_type": "PRIMARY_CANCELLATION",
                    "reason": f"Flight {fnum} ({origin}->{dest}) cancelled.",
                })
                continue

            # If an upstream flight was already cancelled/disrupted, all downstream legs are broken
            if is_disrupted:
                affected.append({
                    **flight,
                    "impact_type": "MISSED_CONNECTION",
                    "reason": f"Downstream connection broken due to upstream cancellation of {primary_disrupted_flight.get('flight_number', 'prior leg')}.",
                })
                continue

            # Check connection timing feasibility with previous flight if applicable
            if idx > 0:
                prev_flight = flights[idx - 1]
                try:
                    prev_arr = parse_datetime(prev_flight.get("arrival_time"))
                    curr_dep = parse_datetime(flight.get("departure_time"))
                    diff_minutes = (curr_dep - prev_arr).total_seconds() / 60.0

                    if diff_minutes < min_connection_minutes:
                        is_disrupted = True
                        affected.append({
                            **flight,
                            "impact_type": "ILLEGAL_CONNECTION_TIME",
                            "reason": f"Layover time ({diff_minutes:.0f} mins) is below the minimum threshold of {min_connection_minutes} mins.",
                        })
                except Exception as e:
                    logger.warning("Could not calculate layover timing: %s", e)

        # Generate summary
        if affected:
            primary_name = primary_disrupted_flight.get("flight_number") if primary_disrupted_flight else disrupted_flight_id
            impacted_names = [f.get("flight_number", f.get("flight_id")) for f in affected]
            summary = (
                f"Disruption detected on {primary_name}. Total {len(affected)} segment(s) impacted: "
                f"{', '.join(impacted_names)}. Passenger cannot complete the original journey."
            )
        else:
            summary = "No flights impacted by disruption."

        logger.info("Connection analysis completed: %s", summary)
        return affected, summary


connection_analyzer = ConnectionAnalyzer()
