from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MeterReading(BaseModel):
    device_id: str = Field(..., min_length=1)
    timestamp: datetime
    voltage: float = Field(..., ge=0, le=500)
    current: float = Field(..., ge=0)
    power: float = Field(..., ge=0)
    energy_kwh: float = Field(..., ge=0)
    frequency: Optional[float] = Field(default=50.0, ge=45, le=65)