from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class FieldCreate(BaseModel):
    field_name: str
    latitude: Decimal
    longitude: Decimal
    location_desc: str | None = None


class FieldRead(BaseModel):
    id: int
    field_name: str
    latitude: Decimal
    longitude: Decimal
    location_desc: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True