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
from app.models.field import Field
from app.models.iot_node import IotNode
from app.models.validation_record import ValidationRecord
from app.schemas.validation_record import (
    ValidationAnalyzeRequest,
    ValidationRecordCreate,
    ValidationRecordUpdate,
)
from app.utils.response import success_response

router = APIRouter(prefix="/validation-records", tags=["Validation Records"])

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "validation_records"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
STATUS_VALUES = {"FLOODED", "DRYING", "DRY", "UNKNOWN"}


def ensure_field_exists(db: Session, field_id: int):
    if not db.query(Field).filter(Field.id == field_id).first():
        raise HTTPException(status_code=404, detail="field_id does not exist.")


def ensure_node_exists(db: Session, node_id: int | None):
    if node_id is None:
        return
    if not db.query(IotNode).filter(IotNode.id == node_id).first():
        raise HTTPException(status_code=404, detail="node_id does not exist.")


def calculate_match(sensor_status: str | None, observed_status: str | None) -> bool | None:
    if not sensor_status or not observed_status:
        return None
    if observed_status == "UNKNOWN":
        return None
    return sensor_status.upper() == observed_status.upper()


def normalize_status(status: str | None) -> str | None:
    if status is None:
        return None
    normalized = status.strip().upper()
    if normalized not in STATUS_VALUES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status}'. Use one of {sorted(STATUS_VALUES)}.",
        )
    return normalized


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


@router.post("")
def create_validation_record(payload: ValidationRecordCreate, db: Session = Depends(get_db)):
    ensure_field_exists(db, payload.field_id)
    ensure_node_exists(db, payload.node_id)

    sensor_status = normalize_status(payload.sensor_predicted_status)
    observed_status = normalize_status(payload.observed_surface_status)
    is_match = payload.is_match
    if is_match is None:
        is_match = calculate_match(sensor_status, observed_status)

    record = ValidationRecord(
        field_id=payload.field_id,
        node_id=payload.node_id,
        record_date=payload.record_date,
        captured_at=payload.captured_at,
        image_url=payload.image_url,
        image_title=payload.image_title,
        sensor_predicted_status=sensor_status,
        observed_surface_status=observed_status,
        is_match=is_match,
        note=payload.note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return success_response(record, "Validation record created.")


@router.post("/upload")
async def upload_validation_image(
    request: Request,
    field_id: int = Form(...),
    node_id: int | None = Form(default=None),
    record_date: date = Form(...),
    captured_at: datetime | None = Form(default=None),
    image_title: str | None = Form(default=None),
    sensor_predicted_status: str | None = Form(default=None),
    observed_surface_status: str | None = Form(default=None),
    note: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ensure_field_exists(db, field_id)
    ensure_node_exists(db, node_id)

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WEBP, and GIF images are allowed.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "").suffix.lower() or ".jpg"
    filename = f"{uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / filename

    content = await file.read()
    destination.write_bytes(content)

    image_url = str(request.base_url).rstrip("/") + f"/uploads/validation_records/{filename}"
    sensor_status = normalize_status(sensor_predicted_status)
    observed_status = normalize_status(observed_surface_status)

    record = ValidationRecord(
        field_id=field_id,
        node_id=node_id,
        record_date=record_date,
        captured_at=captured_at,
        image_url=image_url,
        image_title=image_title or file.filename,
        sensor_predicted_status=sensor_status,
        observed_surface_status=observed_status,
        is_match=calculate_match(sensor_status, observed_status),
        note=note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return success_response(record, "Validation image uploaded.")


@router.get("")
def get_validation_records(
    field_id: int | None = Query(default=None),
    node_id: int | None = Query(default=None),
    record_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(ValidationRecord)
    if field_id is not None:
        query = query.filter(ValidationRecord.field_id == field_id)
    if node_id is not None:
        query = query.filter(ValidationRecord.node_id == node_id)
    if record_date is not None:
        query = query.filter(ValidationRecord.record_date == record_date)

    records = query.order_by(ValidationRecord.record_date.desc(), ValidationRecord.id.desc()).all()
    return success_response(records, "Validation records loaded.")


@router.get("/summary")
def get_validation_summary(
    field_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(ValidationRecord).filter(ValidationRecord.is_match.isnot(None))
    if field_id is not None:
        query = query.filter(ValidationRecord.field_id == field_id)

    records = query.all()
    total = len(records)
    matched = sum(1 for record in records if record.is_match)
    accuracy = round((matched / total) * 100, 2) if total else None

    return success_response(
        {
            "field_id": field_id,
            "total_validation_count": total,
            "match_count": matched,
            "validation_accuracy": accuracy,
        },
        "Validation summary loaded.",
    )


@router.get("/{record_id}")
def get_validation_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(ValidationRecord).filter(ValidationRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Validation record not found.")
    return success_response(record, "Validation record loaded.")


@router.patch("/{record_id}")
def update_validation_record(
    record_id: int,
    payload: ValidationRecordUpdate,
    db: Session = Depends(get_db),
):
    record = db.query(ValidationRecord).filter(ValidationRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Validation record not found.")

    if payload.image_title is not None:
        record.image_title = payload.image_title
    if payload.sensor_predicted_status is not None:
        record.sensor_predicted_status = normalize_status(payload.sensor_predicted_status)
    if payload.observed_surface_status is not None:
        record.observed_surface_status = normalize_status(payload.observed_surface_status)
    if payload.note is not None:
        record.note = payload.note

    record.is_match = payload.is_match
    if record.is_match is None:
        record.is_match = calculate_match(record.sensor_predicted_status, record.observed_surface_status)

    db.commit()
    db.refresh(record)
    return success_response(record, "Validation record updated.")


@router.get("/{record_id}/download")
def download_validation_image(record_id: int, db: Session = Depends(get_db)):
    record = db.query(ValidationRecord).filter(ValidationRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Validation record not found.")

    local_path = local_upload_path_from_url(record.image_url)
    if local_path and local_path.exists():
        return FileResponse(local_path, filename=local_path.name)

    return RedirectResponse(record.image_url)


@router.post("/{record_id}/analyze")
def analyze_validation_image(
    record_id: int,
    payload: ValidationAnalyzeRequest | None = None,
    db: Session = Depends(get_db),
):
    record = db.query(ValidationRecord).filter(ValidationRecord.id == record_id).first()
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
Classify the visible paddy surface into exactly one of:
FLOODED, DRYING, DRY, UNKNOWN.

Do not estimate exact centimeter water depth. Use only visual evidence such as
visible standing water, wet soil, dry soil, reflection, and occlusion.

Return JSON only:
{
  "observed_surface_status": "FLOODED | DRYING | DRY | UNKNOWN",
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

    observed_status = normalize_status(result.get("observed_surface_status"))
    result["observed_surface_status"] = observed_status
    result["is_match"] = calculate_match(record.sensor_predicted_status, observed_status)

    if payload is None or payload.save_result:
        record.observed_surface_status = observed_status
        record.is_match = result["is_match"]
        record.note = build_ai_note(result)
        db.commit()
        db.refresh(record)

    return success_response(
        {
            "analysis": result,
            "record": record,
        },
        "Validation image analyzed.",
    )
