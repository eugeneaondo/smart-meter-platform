import asyncpg
from config.settings import settings

_pool = None

async def get_db_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(settings.database_url, min_size=5, max_size=20)
    return _pool

async def init_db():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Enable TimescaleDB extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS meter_readings (
                time TIMESTAMPTZ NOT NULL,
                device_id TEXT NOT NULL,
                voltage DOUBLE PRECISION,
                current DOUBLE PRECISION,
                power DOUBLE PRECISION,
                energy_kwh DOUBLE PRECISION,
                frequency DOUBLE PRECISION
            );
        """)
        
        # Convert to hypertable
        await conn.execute("""
            SELECT create_hypertable('meter_readings', 'time', 
                                     if_not_exists => TRUE, 
                                     migrate_data => TRUE);
        """)
        
        # Registry of known meters
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS meters (
                device_id TEXT PRIMARY KEY,
                name TEXT,
                location TEXT,
                meter_type TEXT,
                installed_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)

        # Index for device lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_device_time 
            ON meter_readings (device_id, time DESC);
        """)