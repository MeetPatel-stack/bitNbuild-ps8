# Autonomous Travel-Disruption Concierge — Backend API

FastAPI backend and MongoDB Atlas persistence layer powering the Autonomous Travel-Disruption Concierge. This service manages travel itineraries, detects disruptions, streams real-time updates via WebSockets, provides internal ingestion endpoints for the autonomous agent worker, and enforces idempotency on rebookings and notifications.

---

## 🛠 Tech Stack

- **Python**: 3.12+
- **Framework**: FastAPI
- **Database**: MongoDB Atlas via PyMongo (No ORM, native BSON/queries)
- **Validation & Settings**: Pydantic v2 & Pydantic-Settings
- **HTTP Client**: HTTPX (Asynchronous worker dispatch)
- **Real-time**: WebSockets (FastAPI / Starlette)
- **Testing**: Pytest & FastAPI TestClient

---

## 📁 Project Structure

```
apps/backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── health.py        # GET /api/health
│   │       ├── trips.py         # POST /api/trips, GET /api/trips/{id}, GET /api/trips/{id}/timeline
│   │       ├── disruptions.py   # POST /api/simulations/flight-cancellation, GET /api/disruptions/{id}
│   │       ├── internal.py      # POST /api/internal/process-events, rebookings, hotel-updates, notifications
│   │       ├── websocket.py     # WS /ws/trips/{trip_id}
│   │       └── demo.py          # POST /api/demo/seed, GET /api/demo/trip
│   ├── repositories/
│   │   ├── users.py             # User persistence
│   │   ├── trips.py             # Trips & flight segment persistence
│   │   ├── disruptions.py       # Disruption tracking
│   │   ├── rebookings.py        # Rebookings with disruption idempotency
│   │   ├── hotel_bookings.py    # Hotel stays with modification idempotency
│   │   ├── timeline.py          # Chronological timeline events
│   │   └── notifications.py     # Notification history with idempotency
│   ├── schemas/                 # Pydantic v2 schemas for all models & requests
│   ├── services/
│   │   ├── worker_client.py     # Resilient worker dispatcher (safe failure handling)
│   │   ├── timeline_service.py  # Event persistence & live WebSocket broadcasting
│   │   ├── disruption_service.py# Flight cancellation simulation & lifecycle
│   │   ├── trip_service.py      # Trip query & management
│   │   ├── rebooking_service.py # Autonomous rebooking storage & trip sync
│   │   ├── hotel_service.py     # Hotel stay adjustments
│   │   ├── notification_service.py # Traveler notification delivery records
│   │   └── seed_service.py      # Ahmedabad -> Delhi -> London demo trip seeder
│   ├── config.py                # Environment configuration
│   ├── database.py              # PyMongo client & collection accessors
│   └── websocket.py             # Active WebSocket connection manager
├── tests/                       # Automated pytest test suites
├── .env.example                 # Sample configuration
├── requirements.txt             # Dependencies
├── main.py                      # Application entrypoint & lifespan
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites

Ensure Python 3.12+ is installed.

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Update the variables as needed:
```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?appName=travel_concierge
MONGODB_DATABASE=travel_concierge
WORKER_URL=http://localhost:8001
HOST=0.0.0.0
PORT=8000
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

Start the FastAPI server:

```bash
cd apps/backend
python main.py
```

Or using Uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Running Automated Tests

Run the test suite with:

```bash
cd apps/backend
pytest -v
```

All tests run against MongoDB Atlas and verify health, trip operations, cancellation simulations, worker failure tolerance, idempotency checks, and WebSocket real-time connections.

---

## 📡 API Reference

### Core & Health
- `GET /api/health`: Health status and MongoDB Atlas connection verification.
- `POST /api/demo/seed`: Seeds the demo trip (Ahmedabad -> Delhi -> London) with flights, hotel, and traveler.
- `GET /api/demo/trip`: Fetches the current state of the demo trip.

### Trips
- `POST /api/trips`: Create a new travel itinerary.
- `GET /api/trips`: List all itineraries.
- `GET /api/trips/{trip_id}`: Retrieve trip itinerary with flight segments and hotel bookings.
- `GET /api/trips/{trip_id}/timeline`: Retrieve the chronological timeline of events for the trip.

### Disruptions & Simulation
- `POST /api/simulations/flight-cancellation`:
  Simulates a flight cancellation:
  - Validates trip and flight segment.
  - Updates flight status to `CANCELLED` and trip to `DISRUPTED`.
  - Creates disruption record.
  - Broadcasts `DISRUPTION_DETECTED` timeline event via WebSocket.
  - Dispatches job to autonomous worker (`POST {WORKER_URL}/internal/process-disruption`).
  - Gracefully handles worker unavailability without corrupting state.
- `GET /api/disruptions/{disruption_id}`: Retrieve disruption record.

### Worker Internal APIs
- `POST /api/internal/process-events`: Append timeline event and broadcast via WebSocket.
- `POST /api/internal/rebookings`: Store completed rebooking against disruption (idempotent: prevents duplicate rebookings).
- `POST /api/internal/hotel-updates`: Update hotel stay dates/details (idempotent).
- `POST /api/internal/notifications`: Persist traveler notifications (idempotent).

### WebSocket Stream
- `WS /ws/trips/{trip_id}`: Live bidirectional stream. Receives real-time broadcasts whenever timeline events occur.
