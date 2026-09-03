# Architecture Decisions

## Why MQTT?
- Lightweight pub/sub perfect for IoT devices with limited bandwidth
- Decouples device producers from data consumers

## Why TimescaleDB?
- PostgreSQL-compatible = familiar SQL, mature ecosystem
- Built-in time-series optimizations (hypertables, continuous aggregates)
- Seamless dbt integration for September's pipeline

## Why FastAPI + async?
- Native async/await matches MQTT's event-driven model
- Automatic OpenAPI docs for portfolio demos
- Pydantic v2 for validation at the edge