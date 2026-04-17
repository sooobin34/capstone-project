from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class MrvReportCreate(BaseModel):
    field_id: int
    report_month: str

    validation_method: str | None = None
    validation_sample_count: int | None = None
    validation_match_count: int | None = None
    validation_accuracy: float | None = None
    validation_note: str | None = None


class MrvReportStatusUpdate(BaseModel):
    status: str


class MrvReportRead(BaseModel):
    id: int
    field_id: int
    field_name: str | None = None
    report_month: str
    total_awd_cycles: int
    flood_days: int
    status: str
    carbon_reduction: Decimal | None = None

    validation_method: str | None = None
    validation_sample_count: int | None = None
    validation_match_count: int | None = None
    validation_accuracy: Decimal | None = None
    validation_note: str | None = None

    created_at: datetime

    class Config:
        from_attributes = True