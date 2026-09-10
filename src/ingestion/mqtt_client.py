import asyncio
import json
from datetime import datetime
from aiomqtt import Client
from src.models.meter_reading import MeterReading
from src.utils.db import get_db_pool

async def handle_message(payload: bytes):
    data = json.loads(payload)
    reading = MeterReading(**data)
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO meter_readings (device_id, timestamp, voltage, current, power, energy_kwh, frequency)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, reading.device_id, reading.timestamp, reading.voltage,
        reading.current, reading.power, reading.energy_kwh, reading.frequency)


async def mqtt_listener():
    async with Client(settings.mqtt_broker_host, settings.mqtt_broker_port) as client:
        await client.subscribe(settings.mqtt_topic)
        async for message in client.messages:
            await handle_message(message.payload)

if __name__ == "__main__":
    asyncio.run(mqtt_listener())