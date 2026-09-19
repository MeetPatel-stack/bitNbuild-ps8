from fastapi import APIRouter
from app.database import db_manager
from app.config import settings

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
def health_check():
    db_connected = db_manager.ping()
    status = "healthy" if db_connected else "degraded"
    return {
        "status": status,
        "database": "connected" if db_connected else "disconnected",
        "database_name": settings.mongodb_database,
        "worker_url": settings.worker_url,
    }
