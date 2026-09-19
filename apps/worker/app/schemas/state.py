from typing import TypedDict, Optional, List, Dict, Any


class DisruptionWorkflowState(TypedDict, total=False):
    # Core identifiers
    trip_id: str
    disruption_id: str
    disrupted_flight_id: Optional[str]

    # Context loaded from backend
    itinerary: Dict[str, Any]

    # Analysis results
    affected_segments: List[Dict[str, Any]]
    connection_impact_description: Optional[str]

    # Search and evaluation
    flight_options: List[Dict[str, Any]]
    valid_options: List[Dict[str, Any]]
    selected_option: Optional[Dict[str, Any]]
    selection_reason: Optional[str]

    # Evaluation and execution outputs
    policy_result: Optional[Dict[str, Any]]
    rebooking_result: Optional[Dict[str, Any]]
    hotel_result: Optional[Dict[str, Any]]
    notification_result: Optional[Dict[str, Any]]

    # Process controls & explanations
    status: str  # e.g., "INITIALIZED", "ANALYZED", "POLICY_REJECTED", "REBOOKED", "COMPLETED", "FAILED"
    requires_approval: bool
    approval_reason: Optional[str]
    explanation: Optional[str]
    errors: List[str]
