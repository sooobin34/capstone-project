from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.field import Field
from app.models.iot_node import IotNode
from app.models.validation_record import ValidationRecord
from app.schemas.validation_record import (
    ValidationRecordCreate,
    ValidationRecordUpdate,
)
from app.utils.response import success_response

router = APIRouter(prefix="/validations", tags=["Validations"])

SENSOR_STATUSES = {"OVERFLOODED", "FLOODED", "DRYING", "DRY"}
SURFACE_STATUSES = {"WATER_VISIBLE", "NO_WATER_VISIBLE", "UNKNOWN"}


def calculate_surface_match(
    sensor_status: str | None,
    surface_status: str | None,
) -> bool | None:
    """
    센서 4단계 상태를 사진 기반 표면 담수 여부와 비교합니다.

    - FLOODED / OVERFLOODED -> WATER_VISIBLE이면 일치
    - DRYING / DRY -> NO_WATER_VISIBLE이면 일치
    - UNKNOWN은 판별 불가이므로 None 처리
    """
    if sensor_status is None or surface_status is None:
        return None

    if surface_status == "UNKNOWN":
        return None

    if sensor_status in ("FLOODED", "OVERFLOODED"):
        return surface_status == "WATER_VISIBLE"

    if sensor_status in ("DRYING", "DRY"):
        return surface_status == "NO_WATER_VISIBLE"

    return None


@router.post("")
def create_validation_record(payload: ValidationRecordCreate, db: Session = Depends(get_db)):
    field = db.query(Field).filter(Field.id == payload.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="해당 field_id가 존재하지 않습니다.")

    if payload.node_id is not None:
        node = db.query(IotNode).filter(IotNode.id == payload.node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="해당 node_id가 존재하지 않습니다.")

    if payload.sensor_predicted_status and payload.sensor_predicted_status not in SENSOR_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="sensor_predicted_status는 OVERFLOODED, FLOODED, DRYING, DRY 중 하나여야 합니다."
        )

    if payload.observed_surface_status and payload.observed_surface_status not in SURFACE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="observed_surface_status는 WATER_VISIBLE, NO_WATER_VISIBLE, UNKNOWN 중 하나여야 합니다."
        )

    auto_match = calculate_surface_match(
        payload.sensor_predicted_status,
        payload.observed_surface_status,
    )

    record = ValidationRecord(
        field_id=payload.field_id,
        node_id=payload.node_id,
        record_date=payload.record_date,
        image_url=payload.image_url,
        image_title=payload.image_title,
        sensor_predicted_status=payload.sensor_predicted_status,
        observed_surface_status=payload.observed_surface_status,
        is_match=payload.is_match if payload.is_match is not None else auto_match,
        note=payload.note,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return success_response(record, "Validation 기록 생성 성공")


@router.get("")
def get_validation_records(
    field_id: int | None = Query(default=None),
    node_id: int | None = Query(default=None),
    record_date: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(ValidationRecord)

    if field_id is not None:
        query = query.filter(ValidationRecord.field_id == field_id)

    if node_id is not None:
        query = query.filter(ValidationRecord.node_id == node_id)

    if record_date is not None:
        query = query.filter(ValidationRecord.record_date == record_date)

    rows = query.order_by(
        ValidationRecord.record_date.desc(),
        ValidationRecord.id.desc()
    ).all()

    return success_response(rows, "Validation 기록 조회 성공")


@router.patch("/{validation_id}")
def update_validation_record(
    validation_id: int,
    payload: ValidationRecordUpdate,
    db: Session = Depends(get_db),
):
    record = db.query(ValidationRecord).filter(ValidationRecord.id == validation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="해당 validation_id가 존재하지 않습니다.")

    if payload.node_id is not None:
        node = db.query(IotNode).filter(IotNode.id == payload.node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="해당 node_id가 존재하지 않습니다.")
        record.node_id = payload.node_id

    if payload.record_date is not None:
        record.record_date = payload.record_date

    if payload.image_url is not None:
        record.image_url = payload.image_url

    if payload.image_title is not None:
        record.image_title = payload.image_title

    if payload.sensor_predicted_status is not None:
        if payload.sensor_predicted_status not in SENSOR_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="sensor_predicted_status는 OVERFLOODED, FLOODED, DRYING, DRY 중 하나여야 합니다."
            )
        record.sensor_predicted_status = payload.sensor_predicted_status

    if payload.observed_surface_status is not None:
        if payload.observed_surface_status not in SURFACE_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="observed_surface_status는 WATER_VISIBLE, NO_WATER_VISIBLE, UNKNOWN 중 하나여야 합니다."
            )
        record.observed_surface_status = payload.observed_surface_status

    if payload.note is not None:
        record.note = payload.note

    # is_match를 직접 보냈으면 그 값 우선 사용
    if payload.is_match is not None:
        record.is_match = payload.is_match
    else:
        # 센서 상태나 표면 상태가 수정되었으면 자동 재계산
        record.is_match = calculate_surface_match(
            record.sensor_predicted_status,
            record.observed_surface_status,
        )

    db.commit()
    db.refresh(record)

    return success_response(record, "Validation 기록 수정 성공")