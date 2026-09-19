import logging
from typing import Dict, Any, Set
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.schemas.api import ProcessDisruptionRequest, ProcessDisruptionResponse
from app.graph.workflow import disruption_workflow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("worker.main")

app = FastAPI(
    title="Autonomous Travel-Disruption Concierge — Worker",
    description="Autonomous LangGraph decision engine processing flight disruptions, policy evaluations, and rebookings.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for tracking processed disruptions (Idempotency guarantee)
processed_disruptions: Dict[str, Dict[str, Any]] = {}
active_disruptions: Set[str] = set()


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "autonomous-worker",
        "backend_url": settings.backend_url,
        "max_extra_fare": settings.max_extra_fare,
        "max_stops": settings.max_stops,
    }


@app.post(
    "/internal/process-disruption",
    response_model=ProcessDisruptionResponse,
    status_code=status.HTTP_200_OK,
)
async def process_disruption(request: ProcessDisruptionRequest):
    """
    Ingests a disruption event from backend, invokes the LangGraph workflow,
    and runs the autonomous resolution pipeline.
    Protects against duplicate processing via idempotency checks.
    """
    trip_id = request.trip_id
    disruption_id = request.disruption_id
    idempotency_key = f"{trip_id}:{disruption_id}"

    # Idempotency check: If already processed, return stored result
    if idempotency_key in processed_disruptions:
        logger.info("Idempotent request: Disruption %s already processed. Returning cached result.", disruption_id)
        cached = processed_disruptions[idempotency_key]
        return cached

    # Prevent concurrent execution of same disruption
    if idempotency_key in active_disruptions:
        logger.warning("Disruption %s is currently being processed by another worker task.", disruption_id)
        return ProcessDisruptionResponse(
            trip_id=trip_id,
            disruption_id=disruption_id,
            status="IN_PROGRESS",
            success=True,
            explanation="Disruption workflow is actively executing.",
        )

    active_disruptions.add(idempotency_key)

    try:
        logger.info("Starting autonomous LangGraph workflow for trip %s, disruption %s", trip_id, disruption_id)
        
        initial_state = {
            "trip_id": trip_id,
            "disruption_id": disruption_id,
            "errors": [],
            "status": "INITIALIZED",
            "requires_approval": False,
        }

        # Run compiled LangGraph state machine
        final_state = await disruption_workflow.ainvoke(initial_state)

        logger.info("Workflow completed with status: %s", final_state.get("status"))

        response = ProcessDisruptionResponse(
            trip_id=trip_id,
            disruption_id=disruption_id,
            status=final_state.get("status", "COMPLETED"),
            success=final_state.get("status") in ["COMPLETED", "REBOOKED", "NOTIFIED"],
            requires_approval=final_state.get("requires_approval", False),
            approval_reason=final_state.get("approval_reason"),
            selected_option=final_state.get("selected_option"),
            rebooking_result=final_state.get("rebooking_result"),
            hotel_result=final_state.get("hotel_result"),
            notification_result=final_state.get("notification_result"),
            explanation=final_state.get("explanation"),
            errors=final_state.get("errors", []),
        )

        # Cache for idempotency
        processed_disruptions[idempotency_key] = response
        return response

    except Exception as e:
        logger.error("Unhandled exception during workflow execution: %s", e, exc_info=True)
        return ProcessDisruptionResponse(
            trip_id=trip_id,
            disruption_id=disruption_id,
            status="FAILED",
            success=False,
            explanation=f"Autonomous workflow encountered unrecoverable error: {e}",
            errors=[str(e)],
        )
    finally:
        active_disruptions.discard(idempotency_key)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
