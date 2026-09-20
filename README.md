# Wayfinder — Autonomous Travel-Disruption Concierge

> **Real-time, intelligent flight disruption resolution powered by an autonomous agent state machine, FastAPI, MongoDB Atlas, and a reactive React frontend.**

---

## 🌟 Overview

**Wayfinder** is an autonomous travel concierge designed to take the friction and anxiety out of travel disruptions. When a flight leg is cancelled or delayed, Wayfinder immediately:
1. **Detects** the disruption and assesses downstream itinerary impact (broken connections, missed hotel check-ins).
2. **Searches** for viable alternative flights across partner networks.
3. **Applies Policy & Scoring** using corporate travel rules, layover tolerances, and passenger preferences.
4. **Autonomous Rebooking & Hotel Sync** locks in replacement flights and shifts hotel check-in dates with full idempotency.
5. **Real-Time Streaming** broadcasts live status updates to the traveler via WebSockets and SMS/WhatsApp notifications.

---

## 📐 System Architecture

```
                                 ┌─────────────────────────────────┐
                                 │       React 19 + Vite UI        │
                                 │     (Port 5173 - Axios + WS)    │
                                 └───────────────┬─────────────────┘
                                                 │
                             REST API (Axios)    │   WebSocket Events (/ws/trips/{id})
                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Core Backend (Port 8000)                       │
│                                                                                  │
│  • Trip & Segment Lifecycle       • Real-Time Timeline Events & WebSockets       │
│  • Disruption Simulation Router   • Idempotent Ingestion & Storage Endpoints     │
│  • MongoDB Atlas Persistence      • Resilient Worker Dispatch (Safe Failure)     │
└───────────────────────┬──────────────────────────────────▲───────────────────────┘
                        │                                  │
    POST /process-disruption                               │ Internal Ingestion APIs:
    (Dispatches Trip & Disruption)                         │ • POST /api/internal/process-events
                        │                                  │ • POST /api/internal/rebookings
                        ▼                                  │ • POST /api/internal/hotel-updates
┌──────────────────────────────────────────────────────────┴───────────────────────┐
│                       Autonomous Agent Worker (Port 8001)                        │
│                                                                                  │
│     [START] ──► [load_itinerary] ──► [analyze_disruption]                        │
│                     │                                                            │
│                     ▼                                                            │
│         [find_affected_segments] ──► [search_flights]                            │
│                     │                                                            │
│                     ▼                                                            │
│         [apply_policy] ──► [select_option] ──► [check_hotel_impact]              │
│                     │                                                            │
│                     ▼                                                            │
│         [execute_rebooking] ──► [execute_hotel_update] ──► [send_notification]   │
│                     │                                                            │
│                     ▼                                                            │
│         [complete] ──► [END]                                                     │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
bitNbuild-ps8/
├── apps/
│   ├── frontend/            # React 19 + Vite Single Page Application
│   │   ├── src/
│   │   │   ├── api/         # Centralized Axios client & API service modules
│   │   │   │   ├── axios.js       # Base Axios instance & WebSocket URL resolver
│   │   │   │   ├── trips.js       # Trip itinerary queries & timeline
│   │   │   │   ├── disruptions.js # Flight cancellation trigger
│   │   │   │   ├── demo.js        # One-click journey reset & seed
│   │   │   │   ├── health.js      # System health checks
│   │   │   │   └── index.js       # Barrel export
│   │   │   ├── App.jsx      # Concierge views: Home, Trips, Activity, Online, Profile
│   │   │   ├── App.css      # Design system & responsive layout styles
│   │   │   └── main.jsx     # Frontend root entrypoint
│   │   ├── .env.example     # Frontend environment template
│   │   └── package.json     # Node.js dependencies
│   │
│   ├── backend/             # FastAPI Core Backend Service
│   │   ├── app/
│   │   │   ├── api/routes/  # REST & WebSocket route handlers
│   │   │   ├── repositories/# PyMongo Atlas persistence layer
│   │   │   ├── schemas/     # Pydantic v2 request & response models
│   │   │   ├── services/    # Business logic, timeline & worker dispatch
│   │   │   ├── config.py    # Settings (MongoDB URI, CORS, Worker URL)
│   │   │   ├── database.py  # MongoDB connection manager
│   │   │   └── websocket.py # WebSocket client session manager
│   │   ├── tests/           # Pytest test suites
│   │   ├── .env.example     # Backend environment template
│   │   ├── requirements.txt # Python dependencies
│   │   └── main.py          # FastAPI application entrypoint
│   │
│   └── worker/              # Autonomous LangGraph Agent Service
│       ├── app/
│       │   ├── agents/      # Connection analyzer & reasoning engine
│       │   ├── graph/       # LangGraph state machine & 12 workflow nodes
│       │   ├── integrations/# Mock providers for Flights, Hotels, SMS
│       │   ├── policies/    # Deterministic policy & scoring rules
│       │   ├── schemas/     # Typed agent state definitions
│       │   └── main.py      # Worker FastAPI entrypoint
│       ├── tests/           # Pytest test suite for worker nodes
│       ├── .env.example     # Worker environment template
│       └── requirements.txt # Python dependencies
│
└── README.md                # Main project documentation
```

---

## 🚀 Quickstart & Local Development

### 1. Prerequisites
- **Node.js**: v18+ (tested on v24)
- **Python**: v3.12+ (tested on v3.13)
- **MongoDB Atlas** or local MongoDB instance

---

### 2. Environment Configuration

#### A. Backend Configuration
Copy `.env.example` to `apps/backend/.env`:
```bash
cp apps/backend/.env.example apps/backend/.env
```
Ensure the variables are set:
```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?appName=travel_concierge
MONGODB_DATABASE=travel_concierge
WORKER_URL=http://localhost:8001
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000
```

#### B. Worker Configuration
Copy `.env.example` to `apps/worker/.env`:
```bash
cp apps/worker/.env.example apps/worker/.env
```
```env
BACKEND_URL=http://localhost:8000
HOST=0.0.0.0
PORT=8001
MAX_EXTRA_FARE=5000.0
MAX_STOPS=1
CABIN_CLASS=Economy
MIN_LAYOVER_MINUTES=60
MAX_LAYOVER_MINUTES=360
```

#### C. Frontend Configuration
Copy `.env.example` to `apps/frontend/.env`:
```bash
cp apps/frontend/.env.example apps/frontend/.env
```
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

### 3. Installation & Starting the Applications

Open three terminal tabs to run the full stack:

#### Terminal 1 — Backend API (Port 8000)
```bash
cd apps/backend
pip install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2 — Autonomous Worker (Port 8001)
```bash
cd apps/worker
pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### Terminal 3 — Frontend UI (Port 5173)
```bash
cd apps/frontend
npm install
npm run dev
```

Open your browser at **`http://localhost:5173`**.

---

## 🔄 Testing the End-to-End Autonomous Flow

1. Open `http://localhost:5173/#activity` in your browser.
2. Verify the status badge displays **"Live activity connected"** / **"Concierge Live"**.
3. View the demo itinerary: **Ahmedabad (AMD) → Delhi (DEL) → London (LHR)** for traveler **Priya Sharma** and stay at **The Langham, London**.
4. Click **"Simulate cancellation"**:
   - The frontend sends a `POST /api/simulations/flight-cancellation` request via Axios.
   - The backend marks the flight cancelled and dispatches the task to the worker on port 8001.
   - The LangGraph state machine analyzes the broken connection, queries flight alternatives, scores options, and submits rebooking documents.
   - Real-time events stream into the UI via WebSockets.
   - The **Final Resolution** card automatically updates to display the confirmed replacement flight with a **₹0 Waiver** fare.
5. Click **"Reset Journey"**:
   - Resets the demo itinerary back to scheduled state for repeatable testing.

---

## 📡 API Reference

### Backend Endpoints (`http://localhost:8000`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and MongoDB Atlas connectivity check |
| `GET` | `/api/trips` | List all travel itineraries |
| `POST`| `/api/trips` | Create a new trip with flights and hotel details |
| `GET` | `/api/trips/{trip_id}` | Retrieve trip, flight legs, hotels, traveler profile, and rebookings |
| `GET` | `/api/trips/{trip_id}/timeline` | Retrieve chronological timeline events |
| `POST`| `/api/simulations/flight-cancellation` | Simulate cancellation and dispatch autonomous worker |
| `GET` | `/api/disruptions/{disruption_id}` | Retrieve disruption document |
| `POST`| `/api/demo/seed` | Reset/seed demo journey (AMD → DEL → LHR) |
| `GET` | `/api/demo/trip` | Retrieve current state of the demo journey |
| `WS`  | `/ws/trips/{trip_id}` | Real-time WebSocket timeline stream |

### Worker Endpoints (`http://localhost:8001`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Worker health status and policy configuration |
| `POST`| `/internal/process-disruption` | Ingest disruption and execute LangGraph state machine |

---

## 🧪 Running Automated Tests

### Backend Test Suite
```bash
cd apps/backend
pytest -v
```

### Worker Test Suite
```bash
cd apps/worker
pytest -v
```

### Frontend Build Verification
```bash
cd apps/frontend
npm run build
```

---

## 🛡️ License

Built for **bitNbuild Hackathon** — Autonomous Travel Disruption Handling.
