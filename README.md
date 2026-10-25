# Smart Meter Platform

Real-time ingestion and analytics API for smart energy meters. Devices publish readings over MQTT, the platform validates them at the edge, stores them in a TimescaleDB hypertable, and exposes them through an async REST API.

![Python](https://img.shields.io/badge/Python-3.11-0d1117?style=flat-square&logo=python&logoColor=3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-0d1117?style=flat-square&logo=fastapi&logoColor=009688)
![TimescaleDB](https://img.shields.io/badge/TimescaleDB-0d1117?style=flat-square&logo=timescale&logoColor=FDB515)
![MQTT](https://img.shields.io/badge/MQTT-0d1117?style=flat-square&logo=mqtt&logoColor=A076F9)
![Docker](https://img.shields.io/badge/Docker-0d1117?style=flat-square&logo=docker&logoColor=2496ED)
![License](https://img.shields.io/badge/License-MIT-0d1117?style=flat-square)

---

## Architecture

```mermaid
flowchart LR
    M1[Smart meter] -->|JSON over MQTT| B[(Mosquitto broker)]
    M2[Smart meter] -->|smartmeter/+/data| B
    B --> L[Async MQTT listener]
    L -->|Pydantic validation| DB[(TimescaleDB<br/>meter_readings hypertable)]
    API[FastAPI] --> DB
    C[Clients / dashboards] -->|REST| API
```

The MQTT listener runs as a background task inside the FastAPI process, so a single service handles both ingestion and queries. Invalid payloads are logged and dropped without interrupting the stream, and the listener reconnects automatically if the broker goes away.

## Features

- **Async end to end:** `aiomqtt` for ingestion, `asyncpg` connection pooling for storage, FastAPI for serving
- **Validation at the edge:** every reading is checked against a Pydantic model (voltage range, non-negative power and energy, grid frequency bounds) before it touches the database
- **Time-series storage:** readings live in a TimescaleDB hypertable with a `(device_id, time DESC)` index for fast per-device range queries
- **Meter registry:** full CRUD for meter metadata (name, location, meter type, install date)
- **Resilient ingestion:** automatic broker reconnection and per-message error isolation
- **Self-documenting API:** interactive OpenAPI docs at `/docs`

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Transport | MQTT (Eclipse Mosquitto) | Lightweight pub/sub suited to constrained devices; decouples producers from consumers |
| Storage | TimescaleDB (PostgreSQL 15) | Familiar SQL with time-series optimisations such as hypertables and continuous aggregates |
| API | FastAPI + Pydantic v2 | Native async matches the event-driven ingestion model; validation and docs come built in |
| Runtime | Docker Compose | One command brings up the broker, database and API |

More detail on these decisions is in [`docs/architecture.md`](docs/architecture.md).

## Getting started

### Prerequisites

- Docker and Docker Compose

### 1. Configure environment

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://smartmeter:smartmeter@timescaledb:5432/metrics
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
MQTT_TOPIC=smartmeter/+/data
```

### 2. Start the stack

```bash
docker compose -f docker/docker-compose.yml up --build
```

The API is now available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### 3. Send a test reading

```bash
docker compose -f docker/docker-compose.yml exec mosquitto \
  mosquitto_pub -t smartmeter/meter-001/data -m '{
    "device_id": "meter-001",
    "timestamp": "2026-10-25T10:00:00Z",
    "voltage": 230.4,
    "current": 5.2,
    "power": 1198.1,
    "energy_kwh": 152.37,
    "frequency": 50.0
  }'
```

Then query it back:

```bash
curl "http://localhost:8000/readings/meter-001?start=2026-10-25T00:00:00Z"
```

### Running locally without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

You will still need a running TimescaleDB instance and MQTT broker; point `DATABASE_URL` and `MQTT_BROKER_HOST` at them in `.env`.

## API reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `GET` | `/devices` | All devices with reading count and last-seen time |
| `GET` | `/readings/{device_id}` | Readings for a device in a time range (`start`, optional `end`, `limit` up to 10,000) |
| `POST` | `/meters` | Register a meter |
| `GET` | `/meters` | List registered meters (paginated) |
| `GET` | `/meters/{device_id}` | Get a meter |
| `PATCH` | `/meters/{device_id}` | Update meter metadata |
| `DELETE` | `/meters/{device_id}` | Remove a meter |

## Message format

Devices publish to `smartmeter/<device_id>/data`:

| Field | Type | Rules |
|---|---|---|
| `device_id` | string | Required |
| `timestamp` | ISO 8601 datetime | Required |
| `voltage` | float | 0 – 500 V |
| `current` | float | ≥ 0 A |
| `power` | float | ≥ 0 W |
| `energy_kwh` | float | ≥ 0 kWh |
| `frequency` | float | 45 – 65 Hz, defaults to 50 |

## Project structure

```
smart-meter-platform/
├── config/
│   └── settings.py          # Environment-driven settings (pydantic-settings)
├── docker/
│   ├── docker-compose.yml   # TimescaleDB, Mosquitto, API
│   ├── Dockerfile
│   └── mosquitto.conf
├── docs/
│   └── architecture.md      # Design decisions
└── src/
    ├── api/
    │   ├── main.py          # App, lifespan, readings and devices endpoints
    │   └── meters.py        # Meter registry CRUD
    ├── ingestion/
    │   └── mqtt_client.py   # Async MQTT listener with reconnection
    ├── models/              # Pydantic models
    └── utils/
        └── db.py            # Connection pool and schema setup
```

## Roadmap

- [ ] Continuous aggregates for hourly and daily consumption
- [ ] Transformation layer with dbt
- [ ] Grafana dashboards
- [ ] Test suite with pytest
- [ ] Device authentication on the broker

## License

MIT, see [LICENSE](LICENSE).
