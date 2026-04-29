from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class MrvReportCreate(BaseModel):
    field_id: int
    report_month: str


class MrvReportRead(BaseModel):
    id: int
    field_id: int
    report_month: str
    total_awd_cycles: int
    flood_days: int = 0
    status: str = "IN_PROGRESS"
    carbon_reduction: Decimal | None = None
    validation_method: str | None = None
    validation_sample_count: int = 0
    validation_match_count: int = 0
    validation_accuracy: Decimal | None = None
    validation_note: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
