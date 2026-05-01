from datetime import date, datetime

from pydantic import BaseModel, Field


class ValidationRecordCreate(BaseModel):
    field_id: int
    node_id: int | None = None
    record_date: date
    captured_at: datetime | None = None
    image_url: str
    image_title: str | None = None
    camera_height_cm: float | None = None
    actual_water_level_cm: float | None = None

    # 사진/사람 관찰 기준 표면 상태: WATER_VISIBLE / NO_WATER_VISIBLE / UNKNOWN
    observed_surface_status: str | None = None

    note: str | None = None


class ValidationRecordUpdate(BaseModel):
    image_title: str | None = None
    camera_height_cm: float | None = None
    actual_water_level_cm: float | None = None
    observed_surface_status: str | None = None
    note: str | None = None


class ValidationAnalyzeRequest(BaseModel):
    save_result: bool = True
    model: str | None = None


class ValidationAnalyzeResult(BaseModel):
    ai_predicted_status: str = Field(description="WATER_VISIBLE, NO_WATER_VISIBLE, or UNKNOWN")
    confidence: float
    reason: str
    limitations: str | None = None


class ValidationRecordRead(BaseModel):
    id: int
    field_id: int
    node_id: int | None = None
    record_date: date
    captured_at: datetime | None = None

    image_url: str
    image_title: str | None = None

    camera_height_cm: float | None = None
    actual_water_level_cm: float | None = None

    sensor_predicted_status: str | None = None
    observed_surface_status: str | None = None

    ai_predicted_status: str | None = None
    ai_confidence: float | None = None

    is_match: bool | None = None
    note: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True