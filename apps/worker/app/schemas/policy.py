from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DisruptionPolicy(BaseModel):
    max_extra_fare: float = 5000.0
    max_stops: int = 1
    cabin_required: str = "Economy"
    latest_arrival: Optional[datetime] = None
    min_layover_minutes: int = 60
    max_layover_minutes: int = 360


class OptionEvaluation(BaseModel):
    option_id: str
    is_valid: bool
    rejection_reasons: List[str] = Field(default_factory=list)
    score: float = 0.0
    scoring_breakdown: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResult(BaseModel):
    policy: DisruptionPolicy
    total_options_evaluated: int
    valid_options_count: int
    evaluations: List[OptionEvaluation]
    summary: str
