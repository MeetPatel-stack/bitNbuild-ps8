# Autonomous Travel-Disruption Concierge — Worker Service

The autonomous worker service powers intelligent, end-to-end resolution of travel disruptions. Orchestrated with **LangGraph**, it executes a deterministic state machine that analyzes connection impact, searches flight alternatives, applies policy constraints, scores and selects the optimal itinerary, synchronizes hotel check-ins, records rebookings, dispatches traveler notifications, and streams progress to the backend.

---

## 🛠 Tech Stack

- **Python**: 3.12+
- **State Machine**: LangGraph 1.2+ & LangChain-Core
- **HTTP API**: FastAPI & Uvicorn
- **HTTP Client**: HTTPX (calls Backend Core API)
- **Validation**: Pydantic v2 & Pydantic-Settings
- **Testing**: Pytest & AnyIO

---

## 📐 Architecture & LangGraph State Machine

```
[START]
   │
   ▼
[load_itinerary] ──► Fetches trip from GET /api/trips/{trip_id}
   │
   ▼
[analyze_disruption] ──► Inspects cancelled flight leg
   │
   ▼
[find_affected_segments] ──► Deterministic connection impact analysis (AMD->DEL cancellation breaks DEL->LHR)
   │                         Emits: IMPACT_ANALYZED to backend
   ▼
[search_flights] ──► Queries FlightSearchProvider (Mock / External)
   │                 Emits: FLIGHTS_SEARCHED to backend
   ▼
[apply_policy] ──► Deterministic policy filtering (Max extra fare, max stops, cabin)
   │               Emits: POLICY_CHECKED to backend
   ├─── (No valid options) ──► [require_human_approval] ──► [END]
   │
   ▼ (Valid options available)
[select_option] ──► Deterministic scoring engine (Arrival time, fare, stops)
   │
   ▼
[check_hotel_impact] ──► Evaluates hotel check-in window against new flight arrival
   │                     Emits: HOTEL_UPDATE_STARTED (if modification needed)
   ▼
[execute_rebooking] ──► POST /api/internal/rebookings
   │                    Emits: REBOOKING_STARTED to backend
   ▼
[execute_hotel_update] ──► POST /api/internal/hotel-updates (if applicable)
   │
   ▼
[send_notification] ──► Dispatches SMS/WhatsApp & POST /api/internal/notifications
   │
   ▼
[complete] ──► Summarizes resolution & emits PROCESS_COMPLETED
   │
   ▼
 [END]
```

---

## 📁 Project Structure

```
apps/worker/
├── app/
│   ├── agents/
│   │   ├── connection_analyzer.py # Broken connection detection & layover validation
│   │   └── llm_explainer.py       # LLM reasoning layer with deterministic fallback
│   ├── graph/
│   │   ├── nodes.py               # 12 LangGraph workflow nodes
│   │   └── workflow.py            # StateGraph definition & compiled runner
│   ├── integrations/
│   │   ├── flight_search.py       # FlightSearchProvider interface & mock
│   │   ├── hotel_provider.py      # HotelProvider interface & mock
│   │   └── notification.py        # NotificationProvider interface & mock
│   ├── policies/
│   │   ├── policy_engine.py       # Deterministic policy filtering (fare, stops, cabin)
│   │   └── scoring_engine.py      # Deterministic alternative scoring
│   ├── schemas/                   # Strongly typed LangGraph state & Pydantic models
│   ├── services/
│   │   └── backend_client.py      # HTTPX client for backend API communication
│   ├── config.py                  # Settings (BACKEND_URL, PORT, policy defaults)
│   └── main.py                    # Worker FastAPI entrypoint
├── tests/                         # Comprehensive pytest test suite
├── .env.example                   # Environment configuration template
├── requirements.txt               # Dependencies
└── README.md
```

---

## ⚙️ Setup & Execution

### 1. Configure Environment

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Key environment variables:
```env
BACKEND_URL=http://localhost:8000
HOST=0.0.0.0
PORT=8001
MAX_EXTRA_FARE=5000.0
MAX_STOPS=1
CABIN_CLASS=Economy
MIN_LAYOVER_MINUTES=60
MAX_LAYOVER_MINUTES=360
OPENAI_API_KEY=   # Optional; falls back to deterministic explainer if not provided
```

### 2. Run the Worker Application

```bash
cd apps/worker
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

- **Health Check**: `GET http://localhost:8001/health`
- **Process Disruption**: `POST http://localhost:8001/internal/process-disruption`

---

## 🧪 Running Automated Tests

Run the complete test suite:

```bash
cd apps/worker
pytest -v
```

All 12 tests verify connection analysis, policy filtering, scoring, mock providers, happy path workflow, human approval routing, and idempotency protection.
