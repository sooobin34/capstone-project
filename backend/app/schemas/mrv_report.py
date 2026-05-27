from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class MrvReportCreate(BaseModel):
    field_id: int
    report_month: str

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

    # 계산값 (DB X)
    validation_method: str | None = None
    validation_sample_count: int | None = None
    validation_match_count: int | None = None
    validation_accuracy: Decimal | None = None
    validation_note: str | None = None

    created_at: datetime

    class Config:
        from_attributes = True


class MrvWeeklyAnalysis(BaseModel):
    week_no: int
    start_date: str
    end_date: str
    avg_inner_level_cm: float | None = None
    min_inner_level_cm: float | None = None
    max_inner_level_cm: float | None = None
    status_flow: str


class MrvValidationSnapshot(BaseModel):
    record_id: int
    record_date: str
    node_id: int | None = None
    sensor_predicted_status: str | None = None
    observed_surface_status: str | None = None
    ai_predicted_status: str | None = None
    ai_confidence: float | None = None
    sensor_observed_match: bool | None = None
    ai_sensor_match: bool | None = None
    image_url: str | None = None
    note: str | None = None
