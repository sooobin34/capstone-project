import base64
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
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
    time: datetime | None = None
    f_port: int | None = Field(default=None, alias="fPort")
    device_info: LoRaDeviceInfo | None = Field(default=None, alias="deviceInfo")


def normalize_deveui(value: str | None) -> str:
    return (value or "").replace(":", "").replace("-", "").strip().upper()


def get_payload_deveui(payload: LoRaWebhookPayload) -> str:
    candidates = [
        payload.dev_eui,
        payload.dev_eui_lower,
        payload.device_info.dev_eui if payload.device_info else None,
        payload.device_info.dev_eui_upper if payload.device_info else None,
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
        raise HTTPException(
            status_code=400,
            detail="LoRa payload must contain at least 2 bytes.",
        )

    water_level_mm = int.from_bytes(raw[:2], byteorder="big", signed=True)
    return Decimal(water_level_mm) / Decimal("10")


@router.post("")
async def receive_lora_webhook(
    request: Request,
    payload: LoRaWebhookPayload,
    db: Session = Depends(get_db),
):
    raw_body = await request.body()
    event = request.query_params.get("event")

    print("LORA_WEBHOOK_EVENT", event)
    print("LORA_WEBHOOK_RAW_BODY", raw_body.decode("utf-8", errors="ignore"))
    print("LORA_WEBHOOK_PARSED", payload.model_dump())

    if event != "up":
        print("LORA_WEBHOOK_IGNORED_EVENT", event)
        return success_response(
            {"event": event},
            "LoRa webhook event ignored because it is not an uplink.",
        )

    if not payload.data:
        print("LORA_WEBHOOK_NO_DATA", payload.model_dump())
        return success_response(
            {"event": event, "dev_eui": get_payload_deveui(payload)},
            "LoRa webhook event ignored because it has no uplink payload.",
        )

    try:
        raw_payload = base64.b64decode(payload.data, validate=True)
    except Exception as exc:
        print("LORA_WEBHOOK_BASE64_ERROR", payload.data)
        raise HTTPException(status_code=400, detail="LoRa payload data must be valid Base64.") from exc

    dev_eui = get_payload_deveui(payload)
    print("LORA_DEV_EUI", dev_eui)
    print("LORA_RAW_PAYLOAD_HEX", raw_payload.hex())

    node = find_node_by_deveui(db, dev_eui)
    print("LORA_NODE", node.id if node else None)

    if not node:
        raise HTTPException(status_code=404, detail=f"DevEUI {dev_eui} node not found.")

    measured_at = payload.time or datetime.now(timezone.utc)
    water_level_cm = parse_water_level_cm(raw_payload)
    print("LORA_WATER_LEVEL_CM", water_level_cm)

    sensor_log_payload = SensorLogCreate(
        node_id=node.id,
        inner_water_level=water_level_cm,
        outer_water_level=Decimal("0"),
        battery_voltage=Decimal("3.3"),
        measured_at=measured_at,
    )

    print("LORA_SENSOR_LOG_PAYLOAD", sensor_log_payload.model_dump())

    sensor_log_response = save_sensor_log(sensor_log_payload, db)

    print("LORA_SENSOR_LOG_RESPONSE", sensor_log_response)

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
