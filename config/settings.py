from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = Field(default="postgresql://smartmeter:smartmeter@localhost:5432/metrics")
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_topic: str = "smartmeter/+/data"

    class Config:
        env_file = ".env"

settings = Settings()