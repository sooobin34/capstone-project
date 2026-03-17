from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class SensorLogCreate(BaseModel):
    node_id: int
    inner_water_level: Decimal
    outer_water_level: Decimal
    battery_voltage: Decimal | None = None
    measured_at: datetime


class SensorLogRead(BaseModel):
    id: int
    node_id: int
    inner_water_level: Decimal
    outer_water_level: Decimal
    battery_voltage: Decimal | None = None
    measured_at: datetime

    class Config:
        from_attributes = True