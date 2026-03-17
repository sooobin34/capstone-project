from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class IotNodeCreate(BaseModel):
    mac_address: str
    latitude: Decimal
    longitude: Decimal
    location_desc: str | None = None
    is_active: bool = True


class IotNodeRead(BaseModel):
    id: int
    mac_address: str
    latitude: Decimal
    longitude: Decimal
    location_desc: str | None = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True