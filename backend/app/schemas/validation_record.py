from datetime import date, datetime
from pydantic import BaseModel


class ValidationRecordCreate(BaseModel):
    field_id: int
    node_id: int | None = None
    record_date: date
    image_url: str
    image_title: str | None = None

    # 센서 기준 상태: OVERFLOODED / FLOODED / DRYING / DRY
    sensor_predicted_status: str | None = None

    # 사진/사람 관찰 기준 표면 상태: WATER_VISIBLE / NO_WATER_VISIBLE / UNKNOWN
    observed_surface_status: str | None = None

    # 직접 보내지 않아도 서버에서 자동 계산
    is_match: bool | None = None

    note: str | None = None


class ValidationRecordUpdate(BaseModel):
    node_id: int | None = None
    record_date: date | None = None
    image_url: str | None = None
    image_title: str | None = None
    sensor_predicted_status: str | None = None
    observed_surface_status: str | None = None
    is_match: bool | None = None
    note: str | None = None


class ValidationRecordRead(BaseModel):
    id: int
    field_id: int
    node_id: int | None = None
    record_date: date
    image_url: str
    image_title: str | None = None
    sensor_predicted_status: str | None = None
    observed_surface_status: str | None = None
    is_match: bool | None = None
    note: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True