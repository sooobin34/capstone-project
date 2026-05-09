import base64
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import Request
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.sensor_logs import save_sensor_log
from app.models.iot_node import IotNode
from app.schemas.sensor_log import SensorLogCreate
from app.utils.response import success_response

router = APIRouter(prefix="/lora-webhook", tags=["LoRa Webhook"])


class LoRaDeviceInfo(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    dev_eui: str | None = Field(default=None, alias="devEui")
    dev_eui_upper: str | None = Field(default=None, alias="devEUI")


class LoRaWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    dev_eui: str | None = Field(default=None, alias="devEUI")
    dev_eui_lower: str | None = Field(default=None, alias="devEui")
    data: str | None = None
    payload_hex: str | None = Field(default=None, alias="payload")
    time: datetime | None = None
    timestamp: int | None = None
    event_type: str | None = Field(default=None, alias="type")
    f_port: int | None = Field(default=None, alias="fPort")
    device_info: LoRaDeviceInfo | None = Field(default=None, alias="deviceInfo")
    log_object: dict[str, Any] | None = Field(default=None, alias="logObject")


def get_log_payload(payload: LoRaWebhookPayload) -> dict[str, Any]:
    if not payload.log_object:
        return {}

    log_payload = payload.log_object.get("payload")
    if isinstance(log_payload, dict):
        return log_payload
    return {}


def normalize_deveui(value: str | None) -> str:
    return (value or "").replace(":", "").replace("-", "").strip().upper()


def get_payload_deveui(payload: LoRaWebhookPayload) -> str:
    log_payload = get_log_payload(payload)
    candidates = [
        payload.dev_eui,
        payload.dev_eui_lower,
        payload.device_info.dev_eui if payload.device_info else None,
        payload.device_info.dev_eui_upper if payload.device_info else None,
        log_payload.get("devEUI"),
        log_payload.get("devEui"),
    ]
    for candidate in candidates:
        normalized = normalize_deveui(candidate)
        if normalized:
            return normalized
    return ""


def find_node_by_deveui(db: Session, dev_eui: str) -> IotNode | None:
    normalized = normalize_deveui(dev_eui)
    if not normalized:
        return None

    nodes = db.query(IotNode).all()
    for node in nodes:
        if normalize_deveui(node.mac_address) == normalized:
            return node
    return None


def parse_water_level_cm(raw: bytes) -> Decimal:
    if len(raw) < 2:
        raise HTTPException(status_code=400, detail="LoRa payload must contain at least 2 bytes.")

    water_level_mm = int.from_bytes(raw[:2], byteorder="big", signed=False)
    return Decimal(water_level_mm) / Decimal("10")


def parse_raw_payload(payload: LoRaWebhookPayload) -> bytes | None:
    log_payload = get_log_payload(payload)
    data = payload.data or log_payload.get("data")
    if data:
        try:
            return base64.b64decode(str(data), validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="LoRa payload data must be valid Base64.") from exc

    payload_hex = payload.payload_hex or log_payload.get("payload")
    if payload_hex:
        try:
            return bytes.fromhex(str(payload_hex))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="LoRa payload must be valid HEX.") from exc

    return None


def get_measured_at(payload: LoRaWebhookPayload) -> datetime:
    if payload.time:
        return payload.time

    log_payload = get_log_payload(payload)
    timestamp = payload.timestamp or log_payload.get("timestamp")
    if timestamp:
        return datetime.fromtimestamp(int(timestamp), tz=timezone.utc)

    return datetime.now(timezone.utc)


@router.post("")
async def receive_lora_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    raw_body = await request.json()

    print(
        "LORA_WEBHOOK_RAW_BODY",
        json.dumps(raw_body, ensure_ascii=False),
        flush=True,
    )

    payload = LoRaWebhookPayload.model_validate(raw_body)

    print(
        "LORA_WEBHOOK_INCOMING",
        json.dumps(payload.model_dump(by_alias=True), default=str, ensure_ascii=False),
        flush=True,
    )

    raw_payload = parse_raw_payload(payload)

    if raw_payload is None:
        print("LORA_IGNORED_NO_PAYLOAD", {
            "dev_eui": get_payload_deveui(payload),
            "event_type": payload.event_type,
            "f_port": payload.f_port,
            "timestamp": payload.timestamp,
        }, flush=True)

        return success_response(
            {
                "event_type": payload.event_type,
                "dev_eui": get_payload_deveui(payload),
            },
            "LoRa webhook event ignored because it has no uplink payload.",
        )

    dev_eui = get_payload_deveui(payload)
    node = find_node_by_deveui(db, dev_eui)
    if not node:
        raise HTTPException(status_code=404, detail=f"DevEUI {dev_eui} node not found.")

    measured_at = get_measured_at(payload)
    water_level_cm = parse_water_level_cm(raw_payload)

    print("LORA_DECODED", {
    "dev_eui": dev_eui,
    "node_id": node.id,
    "raw_payload_hex": raw_payload.hex(),
    "water_level_cm": str(water_level_cm),
    "measured_at": str(measured_at),
    }, flush=True)
    
    sensor_log_payload = SensorLogCreate(
        node_id=node.id,
        inner_water_level=water_level_cm,
        outer_water_level=Decimal("0"),
        battery_voltage=Decimal("3.3"),
        measured_at=measured_at,
    )
    sensor_log_response = save_sensor_log(sensor_log_payload, db)

    print(
    f"LORA_DB_SAVED_OK node_id={node.id} "
    f"water_level_cm={water_level_cm} "
    f"measured_at={measured_at}",
    flush=True,
    )

    return success_response(
        {
            "dev_eui": dev_eui,
            "node_id": node.id,
            "raw_payload_hex": raw_payload.hex(),
            "parsed": {
                "inner_water_level_cm": water_level_cm,
                "outer_water_level_cm": Decimal("0"),
                "battery_voltage": Decimal("3.3"),
                "measured_at": measured_at,
            },
            "sensor_log": sensor_log_response["data"],
        },
        "LoRa webhook received and sensor log saved.",
    )
