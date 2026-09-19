import logging
from typing import List, Tuple, Optional, Dict, Any
from app.schemas.flight import FlightOption
from app.agents.connection_analyzer import parse_datetime

logger = logging.getLogger("app.policies.scoring_engine")


class ScoringEngine:
    """
    Deterministic scoring engine that ranks valid options.
    Factors considered:
    1. Arrival time (earlier is better)
    2. Extra fare (lower is better, 0 extra fare receives maximum score)
    3. Number of stops (non-stop > 1 stop > multi-stop)
    4. Availability / buffer
    """

    def score_option(
        self,
        option: FlightOption,
        earliest_arrival_timestamp: float,
        latest_arrival_timestamp: float,
        max_policy_extra_fare: float = 5000.0,
    ) -> Tuple[float, Dict[str, Any]]:
        opt_arr_ts = parse_datetime(option.arrival).timestamp()

        # 1. Arrival Time Score (0 to 40 pts)
        time_span = max(latest_arrival_timestamp - earliest_arrival_timestamp, 1.0)
        arrival_ratio = (opt_arr_ts - earliest_arrival_timestamp) / time_span
        arrival_score = 40.0 * (1.0 - min(max(arrival_ratio, 0.0), 1.0))

        # 2. Extra Fare Score (0 to 35 pts)
        fare_ratio = option.extra_fare / max(max_policy_extra_fare, 1.0)
        fare_score = 35.0 * (1.0 - min(max(fare_ratio, 0.0), 1.0))

        # 3. Stops Score (0 to 15 pts)
        if option.stops == 0:
            stops_score = 15.0
        elif option.stops == 1:
            stops_score = 10.0
        else:
            stops_score = 5.0

        # 4. Seat Availability / Reliability (0 to 10 pts)
        avail_score = min(option.available_seats * 1.5, 10.0)

        total_score = arrival_score + fare_score + stops_score + avail_score

        breakdown = {
            "total_score": round(total_score, 2),
            "arrival_score": round(arrival_score, 2),
            "fare_score": round(fare_score, 2),
            "stops_score": round(stops_score, 2),
            "availability_score": round(avail_score, 2),
        }

        return total_score, breakdown

    def select_best_option(
        self,
        valid_options: List[FlightOption],
        max_policy_extra_fare: float = 5000.0,
    ) -> Tuple[Optional[FlightOption], Optional[str], List[Dict[str, Any]]]:
        if not valid_options:
            return None, "No valid options available to score.", []

        timestamps = [parse_datetime(o.arrival).timestamp() for o in valid_options]
        earliest_ts = min(timestamps)
        latest_ts = max(timestamps)

        scored_candidates: List[Dict[str, Any]] = []

        for opt in valid_options:
            score, breakdown = self.score_option(
                opt,
                earliest_arrival_timestamp=earliest_ts,
                latest_arrival_timestamp=latest_ts,
                max_policy_extra_fare=max_policy_extra_fare,
            )
            scored_candidates.append({
                "option": opt,
                "score": score,
                "breakdown": breakdown,
            })

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        winner = scored_candidates[0]["option"]
        winner_score = scored_candidates[0]["score"]
        breakdown = scored_candidates[0]["breakdown"]

        reason = (
            f"Selected {winner.airline} {winner.flight_number} (Score: {winner_score:.1f}/100). "
            f"Rationale: Extra fare ₹{winner.extra_fare:.0f}, {winner.stops} stop(s), "
            f"arrives at {winner.arrival.strftime('%Y-%m-%d %H:%M')}. Optimal balance of arrival punctuality and waiver cost."
        )

        logger.info("Scoring selection completed: %s", reason)
        return winner, reason, scored_candidates


scoring_engine = ScoringEngine()
