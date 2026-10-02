import asyncio
import json
import logging
from aiomqtt import Client, MqttError
from pydantic import ValidationError
from config.settings import settings
from src.models.meter_reading import MeterReading
from src.utils.db import get_db_pool

logger = logging.getLogger(__name__)

RECONNECT_INTERVAL = 5  # seconds

async def handle_message(payload: bytes):
    data = json.loads(payload)
    reading = MeterReading(**data)
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO meter_readings (device_id, time, voltage, current, power, energy_kwh, frequency)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, reading.device_id, reading.timestamp, reading.voltage,
        reading.current, reading.power, reading.energy_kwh, reading.frequency)


async def mqtt_listener():
    while True:
        try:
            async with Client(settings.mqtt_broker_host, settings.mqtt_broker_port) as client:
                await client.subscribe(settings.mqtt_topic)
                logger.info("Subscribed to %s", settings.mqtt_topic)
                async for message in client.messages:
                    try:
                        await handle_message(message.payload)
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.warning("Dropping invalid message on %s: %s", message.topic, e)
                    except Exception:
                        logger.exception("Failed to store message from %s", message.topic)
        except MqttError as e:
            logger.warning("MQTT connection lost (%s); reconnecting in %ss", e, RECONNECT_INTERVAL)
            await asyncio.sleep(RECONNECT_INTERVAL)

if __name__ == "__main__":
    asyncio.run(mqtt_listener())
