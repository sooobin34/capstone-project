from datetime import date, datetime

from pydantic import BaseModel, Field


class ValidationRecordCreate(BaseModel):
    field_id: int
    node_id: int | None = None
    record_date: date
    captured_at: datetime | None = None
    image_url: str
    image_title: str | None = None
    sensor_predicted_status: str | None = None
    observed_surface_status: str | None = None
    is_match: bool | None = None
    note: str | None = None


class ValidationRecordUpdate(BaseModel):
    image_title: str | None = None
    sensor_predicted_status: str | None = None
    observed_surface_status: str | None = None
    is_match: bool | None = None
    note: str | None = None


class ValidationAnalyzeRequest(BaseModel):
    save_result: bool = True
    model: str | None = None


class ValidationAnalyzeResult(BaseModel):
    observed_surface_status: str = Field(description="FLOODED, DRYING, DRY, or UNKNOWN")
    confidence: float
    reason: str
    limitations: str | None = None
    is_match: bool | None = None


class ValidationRecordRead(BaseModel):
    id: int
    field_id: int
    node_id: int | None = None
    record_date: date
    captured_at: datetime | None = None
    image_url: str
    image_title: str | None = None
    sensor_predicted_status: str | None = None
    observed_surface_status: str | None = None
    is_match: bool | None = None
    note: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
