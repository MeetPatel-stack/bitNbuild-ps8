import logging
from typing import Literal
from langgraph.graph import StateGraph, START, END
from app.schemas.state import DisruptionWorkflowState
from app.graph.nodes import (
    load_itinerary,
    analyze_disruption,
    find_affected_segments,
    search_flights,
    apply_policy,
    select_option,
    check_hotel_impact,
    execute_rebooking,
    execute_hotel_update,
    send_notification,
    complete,
    require_human_approval,
)

logger = logging.getLogger("app.graph.workflow")


def route_after_policy(state: DisruptionWorkflowState) -> Literal["select_option", "require_human_approval"]:
    """
    Conditional routing after policy evaluation.
    If no compliant alternatives are found, route to human approval.
    Otherwise proceed to autonomous option selection.
    """
    if state.get("requires_approval") or not state.get("valid_options"):
        return "require_human_approval"
    return "select_option"


def route_after_itinerary(state: DisruptionWorkflowState) -> Literal["analyze_disruption", "require_human_approval"]:
    if state.get("status") == "FAILED":
        return "require_human_approval"
    return "analyze_disruption"


def create_disruption_graph() -> StateGraph:
    graph = StateGraph(DisruptionWorkflowState)

    # Add all workflow nodes
    graph.add_node("load_itinerary", load_itinerary)
    graph.add_node("analyze_disruption", analyze_disruption)
    graph.add_node("find_affected_segments", find_affected_segments)
    graph.add_node("search_flights", search_flights)
    graph.add_node("apply_policy", apply_policy)
    graph.add_node("select_option", select_option)
    graph.add_node("check_hotel_impact", check_hotel_impact)
    graph.add_node("execute_rebooking", execute_rebooking)
    graph.add_node("execute_hotel_update", execute_hotel_update)
    graph.add_node("send_notification", send_notification)
    graph.add_node("complete", complete)
    graph.add_node("require_human_approval", require_human_approval)

    # Edge definitions
    graph.add_edge(START, "load_itinerary")
    graph.add_conditional_edges("load_itinerary", route_after_itinerary)
    graph.add_edge("analyze_disruption", "find_affected_segments")
    graph.add_edge("find_affected_segments", "search_flights")
    graph.add_edge("search_flights", "apply_policy")
    graph.add_conditional_edges("apply_policy", route_after_policy)
    graph.add_edge("select_option", "check_hotel_impact")
    graph.add_edge("check_hotel_impact", "execute_rebooking")
    graph.add_edge("execute_rebooking", "execute_hotel_update")
    graph.add_edge("execute_hotel_update", "send_notification")
    graph.add_edge("send_notification", "complete")
    graph.add_edge("complete", END)
    graph.add_edge("require_human_approval", END)

    return graph


workflow_graph = create_disruption_graph()
disruption_workflow = workflow_graph.compile()
