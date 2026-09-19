from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.trips import router as trips_router
from app.api.routes.disruptions import router as disruptions_router
from app.api.routes.internal import router as internal_router
from app.api.routes.websocket import router as websocket_router
from app.api.routes.demo import router as demo_router

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router)
api_router.include_router(trips_router)
api_router.include_router(disruptions_router)
api_router.include_router(internal_router)
api_router.include_router(demo_router)
# WebSocket router is mounted at root or can be included directly
