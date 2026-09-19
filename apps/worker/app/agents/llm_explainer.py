import logging
from typing import Optional, Dict, Any, List
import httpx
from app.config import settings

logger = logging.getLogger("app.agents.llm_explainer")


class LLMExplainer:
    """
    LLM Abstraction Layer.
    Assists with:
    - Summarizing disruptions
    - Explaining option selection reasoning to travelers
    - Formatting polite notification messages

    CRITICAL SAFETY BOUNDARY:
    The LLM does NOT bypass deterministic policy validation and does NOT call external APIs directly.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key

    async def generate_explanation(
        self,
        disruption_summary: str,
        selected_option: Dict[str, Any],
        hotel_impact: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generates a human-readable explanation of the autonomous action taken.
        If an external LLM API key is present, it attempts to query it;
        otherwise falls back to a deterministic, high-quality explanation generator.
        """
        if self.api_key:
            try:
                # Call OpenAI/Compatible API if configured
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are an autonomous airline concierge. Explain why this replacement flight was selected clearly and politely.",
                                },
                                {
                                    "role": "user",
                                    "content": f"Disruption: {disruption_summary}\nSelected: {selected_option}\nHotel: {hotel_impact}",
                                },
                            ],
                            "max_tokens": 150,
                        },
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"].strip()
                        return content
            except Exception as e:
                logger.warning("LLM API call failed, falling back to deterministic explanation: %s", e)

        # High quality deterministic explanation
        airline = selected_option.get("airline", "Airline")
        flight_num = selected_option.get("flight_number", "Replacement Flight")
        dep = selected_option.get("departure")
        stops = selected_option.get("stops", 0)
        extra_fare = selected_option.get("extra_fare", 0.0)

        explanation = (
            f"Autonomous Concierge Resolution: Rebooked on {airline} ({flight_num}) with {stops} stop(s). "
            f"Departure scheduled for {dep}. Under the carrier disruption policy, this rebooking was completed "
            f"with ₹{extra_fare:.0f} extra fare. "
        )

        if hotel_impact and hotel_impact.get("requires_modification"):
            explanation += f"Hotel check-in has been synchronized to accommodate the new arrival schedule."
        else:
            explanation += "Original hotel check-in remains fully aligned."

        return explanation

    async def generate_passenger_notification(
        self,
        traveler_name: str,
        disrupted_flight_num: str,
        selected_option: Dict[str, Any],
        hotel_updated: bool = False,
    ) -> str:
        """
        Generates a clear SMS / notification body for the traveler.
        """
        new_flight = selected_option.get("flight_number", "confirmed flight")
        dep = selected_option.get("departure")
        airline = selected_option.get("airline", "airline")

        hotel_note = " Your hotel check-in has also been adjusted." if hotel_updated else ""
        return (
            f"Hello {traveler_name}, flight {disrupted_flight_num} was cancelled. "
            f"Our autonomous concierge has rebooked you on {airline} {new_flight} departing at {dep} at no extra cost.{hotel_note} "
            f"Check your app for your updated boarding pass."
        )


llm_explainer = LLMExplainer()
