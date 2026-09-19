import logging
from typing import Tuple, Optional
import httpx
from app.config import settings

logger = logging.getLogger("app.services.worker_client")


class WorkerClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.worker_url).rstrip("/")

    async def dispatch_disruption(self, trip_id: str, disruption_id: str) -> Tuple[bool, Optional[str]]:
        """
        Dispatches a disruption job to the worker service:
        POST {WORKER_URL}/internal/process-disruption
        Payload: { "trip_id": "...", "disruption_id": "..." }

        Returns: (success: bool, message: Optional[str])
        """
        target_url = f"{self.base_url}/internal/process-disruption"
        payload = {
            "trip_id": trip_id,
            "disruption_id": disruption_id,
        }

        logger.info("Dispatching disruption to worker at %s: %s", target_url, payload)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(target_url, json=payload)
                if response.is_success:
                    logger.info("Worker dispatch succeeded for disruption %s", disruption_id)
                    return True, "Dispatched successfully"
                else:
                    err_msg = f"Worker responded with status {response.status_code}: {response.text}"
                    logger.warning("Worker dispatch non-2xx response: %s", err_msg)
                    return False, err_msg
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            err_msg = f"Worker unavailable at {target_url} (Connection failed: {e})"
            logger.warning("Safe failure handling: %s", err_msg)
            return False, err_msg
        except httpx.RequestError as e:
            err_msg = f"Worker request error to {target_url}: {e}"
            logger.warning("Safe failure handling: %s", err_msg)
            return False, err_msg
        except Exception as e:
            err_msg = f"Unexpected error dispatching to worker: {e}"
            logger.error("Safe failure handling: %s", err_msg)
            return False, err_msg


worker_client = WorkerClient()
