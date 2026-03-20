from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.field import Field
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