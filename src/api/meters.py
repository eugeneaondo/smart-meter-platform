from fastapi import APIRouter, HTTPException, Query, Response
from typing import List
import asyncpg
from src.utils.db import get_db_pool
from src.models.meter import Meter, MeterCreate, MeterUpdate

router = APIRouter(prefix="/meters", tags=["meters"])

METER_COLUMNS = "device_id, name, location, meter_type, installed_at, created_at"

@router.post("", response_model=Meter, status_code=201)
async def create_meter(meter: MeterCreate):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(f"""
                INSERT INTO meters (device_id, name, location, meter_type, installed_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING {METER_COLUMNS}
            """, meter.device_id, meter.name, meter.location, meter.meter_type, meter.installed_at)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail=f"Meter '{meter.device_id}' already exists")
    return dict(row)

@router.get("", response_model=List[Meter])
async def list_meters(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT {METER_COLUMNS}
            FROM meters
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """, limit, offset)
    return [dict(r) for r in rows]

@router.get("/{device_id}", response_model=Meter)
async def get_meter(device_id: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(f"SELECT {METER_COLUMNS} FROM meters WHERE device_id = $1", device_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Meter '{device_id}' not found")
    return dict(row)

@router.patch("/{device_id}", response_model=Meter)
async def update_meter(device_id: str, meter: MeterUpdate):
    fields = meter.model_dump(exclude_unset=True)
    if not fields:
        return await get_meter(device_id)

    # Column names come from the Pydantic model, not user input
    assignments = ", ".join(f"{col} = ${i}" for i, col in enumerate(fields, start=2))
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(f"""
            UPDATE meters SET {assignments}
            WHERE device_id = $1
            RETURNING {METER_COLUMNS}
        """, device_id, *fields.values())
    if row is None:
        raise HTTPException(status_code=404, detail=f"Meter '{device_id}' not found")
    return dict(row)

@router.delete("/{device_id}", status_code=204)
async def delete_meter(device_id: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM meters WHERE device_id = $1", device_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail=f"Meter '{device_id}' not found")
    return Response(status_code=204)
