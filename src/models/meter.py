from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MeterBase(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    location: Optional[str] = Field(default=None, max_length=200)
    meter_type: Optional[str] = Field(default=None, max_length=50, description="e.g. single_phase, three_phase")
    installed_at: Optional[datetime] = None

class MeterCreate(MeterBase):
    device_id: str = Field(..., min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_\-]+$")

class MeterUpdate(MeterBase):
    pass

class Meter(MeterBase):
    device_id: str
    created_at: datetime
