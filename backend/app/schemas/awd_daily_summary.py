from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class DailySummaryCreate(BaseModel):
    node_id: int
    record_date: date


class DailySummaryRead(BaseModel):
    id: int
    node_id: int
    record_date: date
    daily_status: str
    avg_inner_level: Decimal | None = None

    class Config:
        from_attributes = True