import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.schemas.state import DisruptionWorkflowState
from app.schemas.flight import FlightOption
from app.schemas.policy import DisruptionPolicy
from app.agents.connection_analyzer import connection_analyzer, parse_datetime
from app.agents.llm_explainer import llm_explainer
from app.integrations.flight_search import mock_flight_search_provider
from app.integrations.hotel_provider import mock_hotel_provider
from app.integrations.notification import mock_notification_provider
from app.policies.policy_engine import policy_engine
from app.policies.scoring_engine import scoring_engine
from app.services.backend_client import backend_client
from app.config import settings

logger = logging.getLogger("app.graph.nodes")


async def load_itinerary(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    trip_id = state["trip_id"]
    logger.info("Node [load_itinerary]: Fetching itinerary for trip %s", trip_id)
    try:
        itinerary = await backend_client.get_trip(trip_id)
        disrupted_id = state.get("disrupted_flight_id")
        
        # If not provided, find the first cancelled flight in trip
        if not disrupted_id:
            flights = itinerary.get("flights", [])
            for f in flights:
                if f.get("status") == "CANCELLED":
                    disrupted_id = f.get("flight_id")
                    break
            if not disrupted_id and flights:
                disrupted_id = flights[0].get("flight_id")

        return {
            **state,
            "itinerary": itinerary,
            "disrupted_flight_id": disrupted_id,
            "status": "ITINERARY_LOADED",
        }
    except Exception as e:
        logger.error("Failed to load itinerary: %s", e)
        return {
            **state,
            "errors": state.get("errors", []) + [f"Failed to load itinerary: {e}"],
            "status": "FAILED",
        }


async def analyze_disruption(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    logger.info("Node [analyze_disruption]: Assessing primary flight failure")
    itinerary = state.get("itinerary", {})
    disrupted_id = state.get("disrupted_flight_id")

    flights = itinerary.get("flights", [])
    disrupted_flight = next((f for f in flights if f.get("flight_id") == disrupted_id), None)
    
    summary = f"Disrupted flight: {disrupted_flight.get('flight_number', disrupted_id) if disrupted_flight else 'Unknown'}"
    logger.info(summary)

    return {
        **state,
        "status": "DISRUPTION_ANALYZED",
    }


async def find_affected_segments(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    logger.info("Node [find_affected_segments]: Running deterministic connection analysis")
    trip_id = state["trip_id"]
    disruption_id = state["disruption_id"]
    itinerary = state.get("itinerary", {})
    disrupted_id = state.get("disrupted_flight_id", "")
    flights = itinerary.get("flights", [])

    affected, summary = connection_analyzer.analyze_impact(
        flights=flights,
        disrupted_flight_id=disrupted_id,
        min_connection_minutes=settings.min_layover_minutes,
    )

    # Emit IMPACT_ANALYZED timeline event to backend
    try:
        await backend_client.send_process_event(
            trip_id=trip_id,
            disruption_id=disruption_id,
            event_type="IMPACT_ANALYZED",
            title="Trip Connection Impact Analyzed",
            description=summary,
            severity="WARNING" if affected else "INFO",
            payload={"affected_count": len(affected), "affected_segments": affected},
        )
    except Exception as e:
        logger.warning("Could not emit IMPACT_ANALYZED event: %s", e)

    return {
        **state,
        "affected_segments": affected,
        "connection_impact_description": summary,
        "status": "IMPACT_ANALYZED",
    }


async def search_flights(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    logger.info("Node [search_flights]: Querying alternative flight options")
    trip_id = state["trip_id"]
    disruption_id = state["disruption_id"]
    itinerary = state.get("itinerary", {})
    origin = itinerary.get("origin", "AMD")
    destination = itinerary.get("destination", "LHR")

    earliest_dep = datetime.now(timezone.utc)

    # Search through mock flight provider
    options: List[FlightOption] = await mock_flight_search_provider.search_alternatives(
        origin=origin,
        destination=destination,
        earliest_departure=earliest_dep,
        cabin_class=settings.cabin_class,
    )

    options_dict = [opt.model_dump(mode="json") for opt in options]

    # Emit FLIGHTS_SEARCHED event
    try:
        await backend_client.send_process_event(
            trip_id=trip_id,
            disruption_id=disruption_id,
            event_type="FLIGHTS_SEARCHED",
            title="Alternative Flights Discovered",
            description=f"Discovered {len(options)} alternative route(s) from {origin} to {destination}.",
            severity="INFO",
            payload={"options_count": len(options), "options": options_dict},
        )
    except Exception as e:
        logger.warning("Could not emit FLIGHTS_SEARCHED event: %s", e)

    return {
        **state,
        "flight_options": options_dict,
        "status": "FLIGHTS_SEARCHED",
    }


async def apply_policy(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    logger.info("Node [apply_policy]: Filtering options against deterministic policy")
    trip_id = state["trip_id"]
    disruption_id = state["disruption_id"]
    options_raw = state.get("flight_options", [])

    # Convert back to FlightOption objects for validation
    candidates = [FlightOption(**opt) for opt in options_raw]

    policy = DisruptionPolicy(
        max_extra_fare=settings.max_extra_fare,
        max_stops=settings.max_stops,
        cabin_required=settings.cabin_class,
        min_layover_minutes=settings.min_layover_minutes,
        max_layover_minutes=settings.max_layover_minutes,
    )

    valid_opts, eval_result = policy_engine.filter_options(candidates, policy)
    valid_opts_dict = [opt.model_dump(mode="json") for opt in valid_opts]
    eval_result_dict = eval_result.model_dump(mode="json")

    # Emit POLICY_CHECKED event
    try:
        await backend_client.send_process_event(
            trip_id=trip_id,
            disruption_id=disruption_id,
            event_type="POLICY_CHECKED",
            title="Disruption Policy Verified",
            description=eval_result.summary,
            severity="INFO" if valid_opts else "WARNING",
            payload=eval_result_dict,
        )
    except Exception as e:
        logger.warning("Could not emit POLICY_CHECKED event: %s", e)

    if not valid_opts:
        logger.warning("No flight options satisfy the policy. Human approval required.")
        return {
            **state,
            "valid_options": [],
            "policy_result": eval_result_dict,
            "requires_approval": True,
            "approval_reason": "No candidate flights satisfy the autonomous waiver budget or stops limit.",
            "status": "REQUIRES_APPROVAL",
        }

    return {
        **state,
        "valid_options": valid_opts_dict,
        "policy_result": eval_result_dict,
        "requires_approval": False,
        "status": "POLICY_CHECKED",
    }


async def select_option(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    logger.info("Node [select_option]: Deterministically scoring and choosing optimal flight")
    valid_raw = state.get("valid_options", [])
    valid_opts = [FlightOption(**opt) for opt in valid_raw]

    best_opt, reason, scored = scoring_engine.select_best_option(
        valid_options=valid_opts,
        max_policy_extra_fare=settings.max_extra_fare,
    )

    if not best_opt:
        return {
            **state,
            "status": "FAILED",
            "errors": state.get("errors", []) + ["No valid option could be selected."],
        }

    return {
        **state,
        "selected_option": best_opt.model_dump(mode="json"),
        "selection_reason": reason,
        "status": "OPTION_SELECTED",
    }


async def check_hotel_impact(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    logger.info("Node [check_hotel_impact]: Checking whether new flight timing impacts hotel booking")
    trip_id = state["trip_id"]
    disruption_id = state["disruption_id"]
    itinerary = state.get("itinerary", {})
    selected_opt = state.get("selected_option", {})

    hotels = itinerary.get("hotels", [])
    if not hotels:
        return {
            **state,
            "hotel_result": {"requires_modification": False, "reason": "No hotel booking on file."},
            "status": "HOTEL_IMPACT_CHECKED",
        }

    hotel = hotels[0]
    hotel_id = hotel.get("id")
    check_in_str = hotel.get("check_in")
    original_check_in = parse_datetime(check_in_str)

    new_arr_str = selected_opt.get("arrival")
    new_arrival = parse_datetime(new_arr_str)

    # If new arrival is after or close to original check-in window, modify check-in
    requires_mod = False
    new_check_in = original_check_in

    if new_arrival > original_check_in:
        requires_mod = True
        new_check_in = new_arrival + timedelta(hours=2)
    elif (original_check_in - new_arrival).total_seconds() < 7200:
        # Arriving less than 2 hours before check-in or later
        requires_mod = True
        new_check_in = new_arrival + timedelta(hours=2)

    hotel_impact = {
        "requires_modification": requires_mod,
        "hotel_booking_id": hotel_id,
        "hotel_name": hotel.get("hotel_name"),
        "original_check_in": str(original_check_in),
        "new_check_in": str(new_check_in) if requires_mod else str(original_check_in),
        "reason": "Flight arrival shifted; check-in adjusted" if requires_mod else "Original check-in timing is compatible",
    }

    if requires_mod:
        try:
            await backend_client.send_process_event(
                trip_id=trip_id,
                disruption_id=disruption_id,
                event_type="HOTEL_UPDATE_STARTED",
                title="Hotel Stay Synchronization Initiated",
                description=f"Adjusting check-in at {hotel.get('hotel_name')} to match new flight arrival time.",
                severity="INFO",
                payload=hotel_impact,
            )
        except Exception as e:
            logger.warning("Could not emit HOTEL_UPDATE_STARTED event: %s", e)

    return {
        **state,
        "hotel_result": hotel_impact,
        "status": "HOTEL_IMPACT_CHECKED",
    }


async def execute_rebooking(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    logger.info("Node [execute_rebooking]: Dispatching rebooking to backend")
    trip_id = state["trip_id"]
    disruption_id = state["disruption_id"]
    disrupted_flight_id = state.get("disrupted_flight_id") or "flight-amd-del-01"
    selected_opt = state.get("selected_option", {})

    # Emit REBOOKING_STARTED event
    try:
        await backend_client.send_process_event(
            trip_id=trip_id,
            disruption_id=disruption_id,
            event_type="REBOOKING_STARTED",
            title="Autonomous Rebooking Initiated",
            description=f"Executing rebooking on {selected_opt.get('airline')} {selected_opt.get('flight_number')}.",
            severity="INFO",
            payload={"selected_option": selected_opt},
        )
    except Exception as e:
        logger.warning("Could not emit REBOOKING_STARTED event: %s", e)

    # Build new flights segments for rebooking
    connecting = selected_opt.get("connecting_flights", [])
    if not connecting:
        connecting = [
            {
                "flight_id": f"rebook-{selected_opt.get('option_id', 'new')}",
                "airline": selected_opt.get("airline", "Air India"),
                "flight_number": selected_opt.get("flight_number", "AI-999"),
                "origin": selected_opt.get("origin", "AMD"),
                "destination": selected_opt.get("destination", "LHR"),
                "departure_time": selected_opt.get("departure"),
                "arrival_time": selected_opt.get("arrival"),
                "status": "SCHEDULED",
                "seat": "14A",
            }
        ]

    rebooking_payload = {
        "disruption_id": disruption_id,
        "trip_id": trip_id,
        "original_flight_id": disrupted_flight_id,
        "airline": selected_opt.get("airline", "Air India"),
        "booking_reference": f"AUTO-{disruption_id[:8].upper()}",
        "cost_difference": selected_opt.get("extra_fare", 0.0),
        "new_flights": connecting,
        "policy_compliance_notes": state.get("selection_reason"),
        "idempotency_key": f"rebook-{disruption_id}",
    }

    try:
        rebooking_resp = await backend_client.create_rebooking(rebooking_payload)
        logger.info("Rebooking confirmed via backend: %s", rebooking_resp)
        return {
            **state,
            "rebooking_result": rebooking_resp,
            "status": "REBOOKED",
        }
    except Exception as e:
        logger.error("Failed to execute rebooking: %s", e)
        return {
            **state,
            "errors": state.get("errors", []) + [f"Rebooking failed: {e}"],
            "status": "FAILED",
        }


async def execute_hotel_update(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    logger.info("Node [execute_hotel_update]: Submitting hotel stay synchronization")
    trip_id = state["trip_id"]
    disruption_id = state["disruption_id"]
    hotel_res = state.get("hotel_result", {})

    if not hotel_res.get("requires_modification"):
        logger.info("Hotel update not required. Skipping modification.")
        return {**state, "status": "HOTEL_COMPLETED"}

    hotel_payload = {
        "trip_id": trip_id,
        "hotel_booking_id": hotel_res.get("hotel_booking_id"),
        "new_check_in": hotel_res.get("new_check_in"),
        "status": "MODIFIED",
        "notes": f"Autonomous adjustment triggered by flight rebooking for disruption {disruption_id}",
        "idempotency_key": f"hotel-{disruption_id}",
    }

    try:
        hotel_resp = await backend_client.update_hotel(hotel_payload)
        logger.info("Hotel update confirmed via backend: %s", hotel_resp)
        return {
            **state,
            "hotel_result": hotel_resp,
            "status": "HOTEL_COMPLETED",
        }
    except Exception as e:
        logger.warning("Hotel update failed non-critically: %s", e)
        return {
            **state,
            "errors": state.get("errors", []) + [f"Hotel update warning: {e}"],
            "status": "HOTEL_COMPLETED",
        }


async def send_notification(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    logger.info("Node [send_notification]: Formatting and dispatching traveler notification")
    trip_id = state["trip_id"]
    disruption_id = state["disruption_id"]
    itinerary = state.get("itinerary", {})
    selected_opt = state.get("selected_option", {})
    hotel_res = state.get("hotel_result", {})

    # Generate message
    msg_body = await llm_explainer.generate_passenger_notification(
        traveler_name="Priya",
        disrupted_flight_num="AI-401",
        selected_option=selected_opt,
        hotel_updated=hotel_res.get("requires_modification", False),
    )

    # 1. Send via mock external provider
    dispatch_res = await mock_notification_provider.send_message(
        recipient="+91-98765-43210",
        title="Flight Cancelled - Rebooked Automatically",
        message=msg_body,
        channel="SMS",
    )

    # 2. Persist to backend
    notif_payload = {
        "user_id": itinerary.get("user_id", "demo-user-1"),
        "trip_id": trip_id,
        "disruption_id": disruption_id,
        "channel": "SMS",
        "recipient": "+91-98765-43210",
        "title": "Flight Cancelled - Rebooked Automatically",
        "message": msg_body,
        "status": "SENT",
        "idempotency_key": f"notif-{disruption_id}",
    }

    try:
        persisted = await backend_client.record_notification(notif_payload)
        logger.info("Notification persisted via backend: %s", persisted)
        return {
            **state,
            "notification_result": {**dispatch_res, "persisted": persisted},
            "status": "NOTIFIED",
        }
    except Exception as e:
        logger.warning("Notification persistence warning: %s", e)
        return {
            **state,
            "notification_result": dispatch_res,
            "status": "NOTIFIED",
        }


async def complete(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    logger.info("Node [complete]: Finalizing autonomous resolution")
    trip_id = state["trip_id"]
    disruption_id = state["disruption_id"]
    selected_opt = state.get("selected_option", {})
    hotel_res = state.get("hotel_result", {})

    explanation = await llm_explainer.generate_explanation(
        disruption_summary=state.get("connection_impact_description", "Flight cancellation"),
        selected_option=selected_opt,
        hotel_impact=hotel_res,
    )

    # Emit PROCESS_COMPLETED event
    try:
        await backend_client.send_process_event(
            trip_id=trip_id,
            disruption_id=disruption_id,
            event_type="PROCESS_COMPLETED",
            title="Autonomous Disruption Resolution Completed",
            description=explanation,
            severity="SUCCESS",
            payload={
                "disruption_id": disruption_id,
                "selected_option": selected_opt,
                "explanation": explanation,
            },
        )
    except Exception as e:
        logger.warning("Could not emit PROCESS_COMPLETED event: %s", e)

    return {
        **state,
        "explanation": explanation,
        "status": "COMPLETED",
    }


async def require_human_approval(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    logger.warning("Node [require_human_approval]: Autonomous policy threshold exceeded. Routing to human agent.")
    trip_id = state["trip_id"]
    disruption_id = state["disruption_id"]
    reason = state.get("approval_reason", "Candidate flights exceed autonomous waiver policy.")

    # Emit PROCESS_FAILED or alert event
    try:
        await backend_client.send_process_event(
            trip_id=trip_id,
            disruption_id=disruption_id,
            event_type="PROCESS_FAILED",
            title="Human Concierge Review Required",
            description=reason,
            severity="WARNING",
            payload={"requires_approval": True, "reason": reason},
        )
    except Exception as e:
        logger.warning("Could not emit failure event: %s", e)

    return {
        **state,
        "status": "REQUIRES_APPROVAL",
        "explanation": f"Workflow halted: {reason}",
    }
