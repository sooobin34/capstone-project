from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db
from app.models.field import Field
from app.models.iot_node import IotNode
from app.models.alert import Alert
from app.models.sensor_log import SensorLog
from app.models.awd_daily_summary import AwdDailySummary
from app.models.validation_record import ValidationRecord
from app.models.mrv_report import MrvReport
from app.schemas.field import FieldCreate
from app.utils.response import success_response

router = APIRouter(prefix="/fields", tags=["Fields"])


@router.post("")
def create_field(payload: FieldCreate, db: Session = Depends(get_db)):
    existing_field = (
        db.query(Field)
        .filter(Field.field_name == payload.field_name)
        .first()
    )
    if existing_field:
        raise HTTPException(status_code=400, detail="이미 등록된 논 이름입니다.")

    field = Field(
        field_name=payload.field_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_desc=payload.location_desc,
    )

    db.add(field)
    db.commit()
    db.refresh(field)

    return success_response(field, "논 등록 성공")


@router.get("")
def get_fields(db: Session = Depends(get_db)):
    fields = db.query(Field).order_by(Field.id.asc()).all()
    return success_response(fields, "논 목록 조회 성공")


@router.delete("/{field_id}")
def delete_field(field_id: int, db: Session = Depends(get_db)):
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="해당 field_id가 존재하지 않습니다.")

    nodes = db.query(IotNode).filter(IotNode.field_id == field_id).all()
    node_ids = [node.id for node in nodes]

    db.query(ValidationRecord).filter(ValidationRecord.field_id == field_id).delete(synchronize_session=False)
    db.query(MrvReport).filter(MrvReport.field_id == field_id).delete(synchronize_session=False)

    if node_ids:
        db.query(Alert).filter(Alert.node_id.in_(node_ids)).delete(synchronize_session=False)
        db.query(AwdDailySummary).filter(AwdDailySummary.node_id.in_(node_ids)).delete(synchronize_session=False)
        db.query(SensorLog).filter(SensorLog.node_id.in_(node_ids)).delete(synchronize_session=False)
        db.query(IotNode).filter(IotNode.id.in_(node_ids)).delete(synchronize_session=False)

    db.delete(field)
    db.commit()

    return success_response(None, "논 및 관련 데이터 삭제 성공")


from pydantic import BaseModel


class FieldUpdate(BaseModel):
    field_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_desc: str | None = None


@router.patch("/{field_id}")
def update_field(field_id: int, payload: FieldUpdate, db: Session = Depends(get_db)):
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="해당 field_id가 존재하지 않습니다.")

    if payload.field_name is not None:
        existing_field = (
            db.query(Field)
            .filter(Field.field_name == payload.field_name, Field.id != field_id)
            .first()
        )
        if existing_field:
            raise HTTPException(status_code=400, detail="이미 등록된 논 이름입니다.")
        field.field_name = payload.field_name

    if payload.latitude is not None:
        field.latitude = payload.latitude
    if payload.longitude is not None:
        field.longitude = payload.longitude
    if payload.location_desc is not None:
        field.location_desc = payload.location_desc

    db.commit()
    db.refresh(field)

    return success_response(field, "논 정보 수정 성공")