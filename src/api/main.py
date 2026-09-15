from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from datetime import datetime
from typing import List, Optional
from src.utils.db import get_db_pool, init_db
from src.ingestion.mqtt_client import mqtt_listener
from src.models.meter_reading import MeterReading
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    # Start MQTT listener in background
    asyncio.create_task(mqtt_listener())
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(
    title="Smart Meter Platform",
    description="Async IoT data ingestion and analytics API",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow()}

@app.get("/readings/{device_id}", response_model=List[MeterReading])
async def get_readings(
    device_id: str,
    start: datetime = Query(..., description="Start time (ISO 8601)"),
    end: Optional[datetime] = Query(None, description="End time"),
    limit: int = Query(1000, le=10000)
):
    pool = await get_db_pool()
    end = end or datetime.utcnow()
    
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT time as timestamp, device_id, voltage, current, power, energy_kwh, frequency
            FROM meter_readings
            WHERE device_id = $1 AND time BETWEEN $2 AND $3
            ORDER BY time DESC
            LIMIT $4
        """, device_id, start, end, limit)
        
    return [dict(r) for r in rows]

@app.get("/devices")
async def get_devices():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT DISTINCT device_id, 
                   COUNT(*) as reading_count,
                   MAX(time) as last_seen
            FROM meter_readings
            GROUP BY device_id
            ORDER BY last_seen DESC
        """)
    return [dict(r) for r in rows]