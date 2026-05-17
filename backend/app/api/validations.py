import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.awd_daily_summary import AwdDailySummary
from app.models.field import Field
from app.models.iot_node import IotNode
from app.models.sensor_log import SensorLog
from app.models.validation_record import ValidationRecord
from app.schemas.validation_record import (
    ValidationAnalyzeRequest,
    ValidationRecordCreate,
    ValidationRecordUpdate,
)
from app.utils.response import success_response

router = APIRouter(prefix="/validations", tags=["Validations"])

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "validation_records"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from ml.inference import predict_water_level

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

SURFACE_STATUS_VALUES = {"WATER_VISIBLE", "NO_WATER_VISIBLE", "UNKNOWN"}

SENSOR_TO_SURFACE_STATUS = {
    "OVERFLOODED": "WATER_VISIBLE",
    "FLOODED": "WATER_VISIBLE",
    "DRY": "NO_WATER_VISIBLE",
}

# -------------------------
# 유틸
# -------------------------

def ensure_field_exists(db: Session, field_id: int):
    if not db.query(Field).filter(Field.id == field_id).first():
        raise HTTPException(status_code=404, detail="field_id does not exist.")

def ensure_node_exists(db: Session, node_id: int | None):
    if node_id is None:
        return
    if not db.query(IotNode).filter(IotNode.id == node_id).first():
        raise HTTPException(status_code=404, detail="node_id does not exist.")

def normalize_surface_status(status: str | None) -> str | None:
    if status is None:
        return None

    normalized = status.strip().upper()

    if normalized not in SURFACE_STATUS_VALUES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid surface status '{status}'. Use one of {sorted(SURFACE_STATUS_VALUES)}."
        )

    return normalized

def normalize_dt(dt: datetime) -> datetime:
    # DB/입력값의 timezone aware/naive 차이로 비교 오류가 나는 것을 방지한다.
    return dt.replace(tzinfo=None)


def water_level_to_surface_status(inner_water_level) -> str | None:
    if inner_water_level is None:
        return None

    value = float(inner_water_level)
    if value >= 0:
        return "WATER_VISIBLE"
    return "NO_WATER_VISIBLE"


def daily_status_to_surface_status(sensor_status: str | None) -> str | None:
    if not sensor_status:
        return None
    if sensor_status in SURFACE_STATUS_VALUES:
        return sensor_status
    return SENSOR_TO_SURFACE_STATUS.get(sensor_status)


def get_nearest_sensor_log(
    db: Session,
    node_id: int | None,
    captured_at: datetime | None,
    window_hours: int = 3,
) -> SensorLog | None:
    if node_id is None or captured_at is None:
        return None

    target = normalize_dt(captured_at)
    start_at = target - timedelta(hours=window_hours)
    end_at = target + timedelta(hours=window_hours)

    candidates = (
        db.query(SensorLog)
        .filter(
            SensorLog.node_id == node_id,
            SensorLog.measured_at >= start_at,
            SensorLog.measured_at <= end_at,
        )
        .all()
    )

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda row: abs((normalize_dt(row.measured_at) - target).total_seconds()),
    )


def get_sensor_status(
    db: Session,
    node_id: int | None,
    record_date: date,
    captured_at: datetime | None = None,
):
    # 1순위: captured_at 기준 근접 sensor_log의 cm 값을 물 보임/안 보임으로 변환
    nearest_log = get_nearest_sensor_log(db, node_id, captured_at)
    if nearest_log:
        return water_level_to_surface_status(nearest_log.inner_water_level)

    # 2순위: captured_at이 없거나 근접 로그가 없으면 기존 daily_summary 방식으로 fallback
    if node_id is None:
        return None

    summary = (
        db.query(AwdDailySummary)
        .filter(
            AwdDailySummary.node_id == node_id,
            AwdDailySummary.record_date == record_date,
        )
        .order_by(AwdDailySummary.id.desc())
        .first()
    )

    if summary:
        return daily_status_to_surface_status(summary.daily_status)

    return None


def calculate_match(sensor_status: str | None, observed_status: str | None):
    if not sensor_status or not observed_status or observed_status == "UNKNOWN":
        return None

    expected = daily_status_to_surface_status(sensor_status)
    if expected is None or expected == "UNKNOWN":
        return None

    return expected == observed_status


def calculate_ai_sensor_match(
    sensor_status: str | None,
    ai_status: str | None,
    sensor_observed_match: bool | None,
):
    # 센서-사람 검증이 True인 데이터만 AI-센서 비교 대상으로 사용한다.
    if sensor_observed_match is not True:
        return None

    sensor_surface_status = daily_status_to_surface_status(sensor_status)
    if (
        not sensor_surface_status
        or not ai_status
        or sensor_surface_status == "UNKNOWN"
        or ai_status == "UNKNOWN"
    ):
        return None

    return sensor_surface_status == ai_status

def water_level_cm_to_ai_status(value):
    if value is None:
        return None

    value = float(value)

    if value < 2:
        return "LOW"
    if value < 4:
        return "MID"

    return "HIGH"

def local_upload_path_from_url(image_url: str) -> Path | None:
    marker = "/uploads/validation_records/"
    if marker not in image_url:
        return None
    filename = image_url.rsplit(marker, 1)[-1].split("?", 1)[0]
    candidate = (UPLOAD_DIR / filename).resolve()
    upload_root = UPLOAD_DIR.resolve()
    if upload_root not in candidate.parents and candidate != upload_root:
        return None
    return candidate

# -------------------------
# CREATE
# -------------------------

@router.post("")
def create_validation(payload: ValidationRecordCreate, db: Session = Depends(get_db)):
    ensure_field_exists(db, payload.field_id)
    ensure_node_exists(db, payload.node_id)

    observed = normalize_surface_status(payload.observed_surface_status)
    sensor = get_sensor_status(db, payload.node_id, payload.record_date, payload.captured_at)

    record = ValidationRecord(
        field_id=payload.field_id,
        node_id=payload.node_id,
        record_date=payload.record_date,
        captured_at=payload.captured_at,
        image_url=payload.image_url,
        image_title=payload.image_title,
        camera_height_cm=payload.camera_height_cm,
        actual_water_level_cm=payload.actual_water_level_cm,
        sensor_predicted_status=sensor,
        observed_surface_status=observed,
        is_match=calculate_match(sensor, observed),
        note=payload.note,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return success_response(record, "Validation record created")

# -------------------------
# UPLOAD
# -------------------------

@router.post("/upload")
async def upload_validation(
    request: Request,
    field_id: int = Form(...),
    node_id: int | None = Form(None),
    record_date: date = Form(...),
    captured_at: datetime | None = Form(None),
    image_title: str | None = Form(None),
    camera_height_cm: float | None = Form(None),
    actual_water_level_cm: float | None = Form(None),
    observed_surface_status: str | None = Form(None),
    note: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ensure_field_exists(db, field_id)
    ensure_node_exists(db, node_id)

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image type")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        suffix = ".jpg"

    filename = f"{uuid4().hex}{suffix}"
    path = UPLOAD_DIR / filename

    content = await file.read()
    path.write_bytes(content)

    image_url = str(request.base_url).rstrip("/") + f"/uploads/validation_records/{filename}"

    observed = normalize_surface_status(observed_surface_status)
    sensor = get_sensor_status(db, node_id, record_date, captured_at)

    record = ValidationRecord(
        field_id=field_id,
        node_id=node_id,
        record_date=record_date,
        captured_at=captured_at,
        image_url=image_url,
        image_title=image_title or file.filename,
        camera_height_cm=camera_height_cm,
        actual_water_level_cm=actual_water_level_cm,
        sensor_predicted_status=sensor,
        observed_surface_status=observed,
        is_match=calculate_match(sensor, observed),
        note=note,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return success_response(record, "Validation image uploaded")

# -------------------------
# GET
# -------------------------

@router.get("")
def get_validations(
    field_id: int | None = Query(None),
    node_id: int | None = Query(None),
    record_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(ValidationRecord)

    if field_id is not None:
        query = query.filter(ValidationRecord.field_id == field_id)
    if node_id is not None:
        query = query.filter(ValidationRecord.node_id == node_id)
    if record_date is not None:
        query = query.filter(ValidationRecord.record_date == record_date)

    records = query.order_by(
        ValidationRecord.record_date.desc(),
        ValidationRecord.id.desc()
    ).all()

    return success_response(records, "Validations loaded.")

# -------------------------
# SUMMARY (수정됨)
# -------------------------

@router.get("/summary")
def get_validation_summary(
    field_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(ValidationRecord)

    if field_id is not None:
        query = query.filter(ValidationRecord.field_id == field_id)

    all_records = query.all()
    valid_records = [r for r in all_records if r.is_match is not None]
    ai_sensor_records = [r for r in all_records if r.ai_sensor_match is not None]

    total = len(all_records)
    matched = sum(1 for r in valid_records if r.is_match)
    mismatched = sum(1 for r in valid_records if r.is_match is False)

    ai_sensor_matched = sum(1 for r in ai_sensor_records if r.ai_sensor_match)
    ai_sensor_mismatched = sum(1 for r in ai_sensor_records if r.ai_sensor_match is False)

    accuracy = round((matched / len(valid_records)) * 100, 2) if valid_records else None
    ai_sensor_accuracy = round((ai_sensor_matched / len(ai_sensor_records)) * 100, 2) if ai_sensor_records else None

    return success_response(
        {
            "field_id": field_id,
            "total_validation_count": total,
            "match_count": matched,
            "mismatch_count": mismatched,
            "validation_accuracy": accuracy,
            "ai_sensor_match_count": ai_sensor_matched,
            "ai_sensor_mismatch_count": ai_sensor_mismatched,
            "ai_sensor_accuracy": ai_sensor_accuracy,
        },
        "Validation summary loaded.",
    )

# -------------------------
# GET ONE
# -------------------------

@router.get("/{validation_id}")
def get_validation(validation_id: int, db: Session = Depends(get_db)):
    record = db.query(ValidationRecord).filter(ValidationRecord.id == validation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Validation record not found.")
    return success_response(record, "Validation loaded.")


# -------------------------
# UPDATE
# -------------------------

@router.patch("/{validation_id}")
def update_validation(
    validation_id: int,
    payload: ValidationRecordUpdate,
    db: Session = Depends(get_db),
):
    record = db.query(ValidationRecord).filter(ValidationRecord.id == validation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Validation record not found.")

    if payload.image_title is not None:
        record.image_title = payload.image_title
    if payload.camera_height_cm is not None:
        record.camera_height_cm = payload.camera_height_cm
    if payload.actual_water_level_cm is not None:
        record.actual_water_level_cm = payload.actual_water_level_cm
    if payload.observed_surface_status is not None:
        record.observed_surface_status = normalize_surface_status(payload.observed_surface_status)
    if payload.note is not None:
        record.note = payload.note

    # 수정 완료: actual_water_level_cm 제거
    record.sensor_predicted_status = get_sensor_status(
        db,
        record.node_id,
        record.record_date,
        record.captured_at,
    )

    record.is_match = calculate_match(
        record.sensor_predicted_status,
        record.observed_surface_status,
    )
    record.ai_sensor_match = calculate_ai_sensor_match(
        record.sensor_predicted_status,
        record.ai_predicted_status,
        record.is_match,
    )

    db.commit()
    db.refresh(record)

    return success_response(record, "Validation updated.")


# -------------------------
# DOWNLOAD
# -------------------------

@router.get("/{validation_id}/download")
def download_validation_image(validation_id: int, db: Session = Depends(get_db)):
    record = db.query(ValidationRecord).filter(ValidationRecord.id == validation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Validation record not found.")

    local_path = local_upload_path_from_url(record.image_url)

    if local_path and local_path.exists():
        return FileResponse(local_path, filename=local_path.name)

    return RedirectResponse(record.image_url)


# -------------------------
# ANALYZE (최종 수정)
# -------------------------

@router.post("/{validation_id}/analyze")
def analyze_validation_image(
    validation_id: int,
    payload: ValidationAnalyzeRequest | None = None,
    db: Session = Depends(get_db),
):
    record = db.query(ValidationRecord).filter(ValidationRecord.id == validation_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Validation record not found.")

    local_path = local_upload_path_from_url(record.image_url)

    if not local_path or not local_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Uploaded image file not found on server."
        )

    try:
        result = predict_water_level(str(local_path))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI image analysis failed: {exc}"
        ) from exc

    ai_status = result.get("predicted_class")  # LOW / MID / HIGH
    ai_confidence = round(float(result.get("confidence", 0)) * 100, 2)

    if payload is None or payload.save_result:
        record.ai_predicted_status = ai_status
        record.ai_confidence = ai_confidence

        nearest_log = get_nearest_sensor_log(
            db=db,
            node_id=record.node_id,
            captured_at=record.captured_at,
        )

        if nearest_log:
            sensor_level = nearest_log.inner_water_level
        else:
            summary = (
                db.query(AwdDailySummary)
                .filter(
                    AwdDailySummary.node_id == record.node_id,
                    AwdDailySummary.record_date == record.record_date,
                )
                .order_by(AwdDailySummary.id.desc())
                .first()
            )

            sensor_level = summary.avg_inner_level if summary else None

        sensor_ai_status = water_level_cm_to_ai_status(sensor_level)

        record.ai_sensor_match = (
            sensor_ai_status == ai_status
            if sensor_ai_status is not None
            else None
        )

        db.commit()
        db.refresh(record)

    return success_response(
        {
            "analysis": result,
            "record": record,
        },
        "Validation image analyzed.",
    )