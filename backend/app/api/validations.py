import base64
import json
import os
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.awd_daily_summary import AwdDailySummary
from app.models.field import Field
from app.models.iot_node import IotNode
from app.models.validation_record import ValidationRecord
from app.schemas.validation_record import (
    ValidationAnalyzeRequest,
    ValidationRecordCreate,
    ValidationRecordUpdate,
)
from app.utils.response import success_response

router = APIRouter(prefix="/validations", tags=["Validations"])

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "validation_records"
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

# ✅ 센서 상태는 daily_summary에서만 가져옴
def get_sensor_status(db: Session, node_id: int | None, record_date: date):
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
        return summary.daily_status

    return None

def calculate_match(sensor_status: str | None, observed_status: str | None):
    if not sensor_status or not observed_status or observed_status == "UNKNOWN":
        return None

    expected = SENSOR_TO_SURFACE_STATUS.get(sensor_status)
    if expected is None:
        return None

    return expected == observed_status

def build_ai_note(result: dict) -> str:
    confidence = result.get("confidence")
    reason = result.get("reason") or ""
    limitations = result.get("limitations") or ""
    note = f"AI confidence={confidence}; reason={reason}"
    if limitations:
        note += f"; limitations={limitations}"
    return note[:255]


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

def image_input_for_openai(image_url: str) -> dict:
    local_path = local_upload_path_from_url(image_url)
    if local_path and local_path.exists():
        suffix = local_path.suffix.lower()
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }.get(suffix, "image/jpeg")
        encoded = base64.b64encode(local_path.read_bytes()).decode("ascii")
        return {
            "type": "input_image",
            "image_url": f"data:{mime_type};base64,{encoded}",
        }

    return {"type": "input_image", "image_url": image_url}

# -------------------------
# CREATE
# -------------------------

@router.post("")
def create_validation(payload: ValidationRecordCreate, db: Session = Depends(get_db)):
    ensure_field_exists(db, payload.field_id)
    ensure_node_exists(db, payload.node_id)

    observed = normalize_surface_status(payload.observed_surface_status)
    sensor = get_sensor_status(db, payload.node_id, payload.record_date)

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
    sensor = get_sensor_status(db, node_id, record_date)

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

    total = len(all_records)
    matched = sum(1 for r in valid_records if r.is_match)

    accuracy = round((matched / len(valid_records)) * 100, 2) if valid_records else None

    return success_response(
        {
            "field_id": field_id,
            "total_validation_count": total,
            "match_count": matched,
            "validation_accuracy": accuracy,
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
    )

    record.is_match = calculate_match(
        record.sensor_predicted_status,
        record.observed_surface_status,
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

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="openai package is not installed.") from exc

    model = (payload.model if payload else None) or os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=api_key)

    prompt = """
This is a validation image for an AWD rice paddy water-management capstone project.
Classify whether standing water is visible on the paddy surface.

Use exactly one of:
WATER_VISIBLE, NO_WATER_VISIBLE, UNKNOWN.

Do not estimate exact centimeter water depth. Use only visual evidence such as
standing water, reflections, wet/dry soil, vegetation, angle, and occlusion.

Return JSON only:
{
  "ai_predicted_status": "WATER_VISIBLE | NO_WATER_VISIBLE | UNKNOWN",
  "confidence": 0-100,
  "reason": "short evidence",
  "limitations": "angle/reflection/occlusion/weather limitations"
}
""".strip()

    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        image_input_for_openai(record.image_url),
                    ],
                }
            ],
        )

        result = json.loads(response.output_text)

    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="OpenAI response was not valid JSON.") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI image analysis failed: {exc}") from exc

    # normalize 유지
    ai_status = normalize_surface_status(result.get("ai_predicted_status"))
    result["ai_predicted_status"] = ai_status

    # 저장
    if payload is None or payload.save_result:
        record.ai_predicted_status = ai_status
        record.ai_confidence = result.get("confidence")

        # ❌ note 덮어쓰기 제거 (중요)
        # record.note = build_ai_note(result)

        db.commit()
        db.refresh(record)

    return success_response(
        {
            "analysis": result,
            "record": record,
        },
        "Validation image analyzed.",
    )