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
