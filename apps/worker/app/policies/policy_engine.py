import logging
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional
from app.schemas.flight import FlightOption
from app.schemas.policy import DisruptionPolicy, OptionEvaluation, PolicyEvaluationResult
from app.agents.connection_analyzer import parse_datetime

logger = logging.getLogger("app.policies.policy_engine")


class PolicyEngine:
    """
    Deterministic Policy Engine.
    Filters candidate flight options strictly according to business and airline disruption rules.
    Invalid options are eliminated BEFORE option selection.
    """

    def evaluate_option(
        self,
        option: FlightOption,
        policy: DisruptionPolicy,
    ) -> OptionEvaluation:
        rejections: List[str] = []

        # 1. Extra fare check
        if option.extra_fare > policy.max_extra_fare:
            rejections.append(
                f"Extra fare ₹{option.extra_fare:.0f} exceeds maximum permitted policy of ₹{policy.max_extra_fare:.0f}"
            )

        # 2. Maximum stops check
        if option.stops > policy.max_stops:
            rejections.append(
                f"Total stops ({option.stops}) exceeds maximum allowed stops ({policy.max_stops})"
            )

        # 3. Cabin class check
        if policy.cabin_required and option.cabin.lower() != policy.cabin_required.lower():
            rejections.append(
                f"Cabin class '{option.cabin}' does not match required class '{policy.cabin_required}'"
            )

        # 4. Latest arrival time check
        if policy.latest_arrival:
            opt_arr = parse_datetime(option.arrival)
            policy_arr = parse_datetime(policy.latest_arrival)
            if opt_arr > policy_arr:
                rejections.append(
                    f"Arrival time {opt_arr.isoformat()} exceeds latest permitted arrival {policy_arr.isoformat()}"
                )

        # 5. Connection feasibility check
        if option.connecting_flights and len(option.connecting_flights) > 1:
            for i in range(len(option.connecting_flights) - 1):
                leg1 = option.connecting_flights[i]
                leg2 = option.connecting_flights[i + 1]
                try:
                    leg1_arr = parse_datetime(leg1.arrival_time)
                    leg2_dep = parse_datetime(leg2.departure_time)
                    layover_mins = (leg2_dep - leg1_arr).total_seconds() / 60.0

                    if layover_mins < policy.min_layover_minutes:
                        rejections.append(
                            f"Layover between {leg1.flight_number} and {leg2.flight_number} ({layover_mins:.0f} mins) is below minimum of {policy.min_layover_minutes} mins"
                        )
                    elif layover_mins > policy.max_layover_minutes:
                        rejections.append(
                            f"Layover ({layover_mins:.0f} mins) exceeds maximum allowed layover of {policy.max_layover_minutes} mins"
                        )
                except Exception as e:
                    logger.warning("Error verifying layover timing: %s", e)

        is_valid = len(rejections) == 0
        return OptionEvaluation(
            option_id=option.option_id,
            is_valid=is_valid,
            rejection_reasons=rejections,
        )

    def filter_options(
        self,
        options: List[FlightOption],
        policy: DisruptionPolicy,
    ) -> Tuple[List[FlightOption], PolicyEvaluationResult]:
        """
        Evaluates all candidate options and filters down to valid options.
        """
        valid_options: List[FlightOption] = []
        evaluations: List[OptionEvaluation] = []

        for opt in options:
            eval_res = self.evaluate_option(opt, policy)
            evaluations.append(eval_res)
            if eval_res.is_valid:
                valid_options.append(opt)

        summary = (
            f"Evaluated {len(options)} options against policy. "
            f"Found {len(valid_options)} valid compliant option(s). "
            f"Rejected {len(options) - len(valid_options)} option(s)."
        )
        logger.info(summary)

        result = PolicyEvaluationResult(
            policy=policy,
            total_options_evaluated=len(options),
            valid_options_count=len(valid_options),
            evaluations=evaluations,
            summary=summary,
        )
        return valid_options, result


policy_engine = PolicyEngine()
