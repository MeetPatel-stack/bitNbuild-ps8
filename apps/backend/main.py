import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config import settings
from app.database import db_manager
from app.api.routes import api_router
from app.api.routes.websocket import router as websocket_router
from app.services.seed_service import seed_demo_data
from app.repositories.trips import trip_repo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB Atlas
    logger.info("Initializing application...")
    try:
        db_manager.connect()
        is_healthy = db_manager.ping()
        logger.info("MongoDB Atlas connectivity verified: %s", is_healthy)

        # Seed demo trip if not present
        existing_demo = trip_repo.get_by_id("demo-trip-amd-lhr")
        if not existing_demo:
            logger.info("Seeding initial demo trip (Ahmedabad -> Delhi -> London)...")
            seed_demo_data(force=False)
    except Exception as e:
        logger.error("Error during startup initialization: %s", e)

    yield

    # Shutdown: Cleanly close DB connection
    logger.info("Shutting down application...")
    db_manager.close()


app = FastAPI(
    title="Autonomous Travel-Disruption Concierge API",
    description="Backend API powering real-time travel disruption handling, autonomous rebooking, and live updates.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend development and authorized origins
allowed_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes and WebSocket routes
app.include_router(api_router)
app.include_router(websocket_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error processing %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred.", "path": request.url.path},
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
