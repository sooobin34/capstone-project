from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class MrvReportCreate(BaseModel):
    report_month: str


class MrvReportRead(BaseModel):
    id: int
    report_month: str
    total_awd_cycles: int
    carbon_reduction: Decimal | None = None
    created_at: datetime

    class Config:
        from_attributes = True