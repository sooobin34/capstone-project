from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.field import Field
from app.models.iot_node import IotNode
from app.schemas.iot_node import IotNodeCreate
from app.utils.response import success_response
from app.models.alert import Alert
from app.models.sensor_log import SensorLog

router = APIRouter(prefix="/nodes", tags=["Nodes"])


@router.post("")
def create_node(payload: IotNodeCreate, db: Session = Depends(get_db)):
    existing_node = db.query(IotNode).filter(IotNode.mac_address == payload.mac_address).first()
    if existing_node:
        raise HTTPException(status_code=400, detail="이미 등록된 mac_address입니다.")

    field = db.query(Field).filter(Field.id == payload.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="해당 field_id가 존재하지 않습니다.")

    node = IotNode(
        field_id=payload.field_id,
        mac_address=payload.mac_address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_desc=payload.location_desc,
        is_active=payload.is_active,
    )

    db.add(node)
    db.commit()
    db.refresh(node)

    return success_response(node, "노드 등록 성공")


@router.get("")
def get_nodes(
    field_id: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(IotNode)

    if field_id is not None:
        query = query.filter(IotNode.field_id == field_id)

    nodes = query.order_by(IotNode.id.asc()).all()
    return success_response(nodes, "노드 목록 조회 성공")


@router.get("/{node_id}/status")
def get_node_status(node_id: int, db: Session = Depends(get_db)):
    node = db.query(IotNode).filter(IotNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="해당 node_id가 존재하지 않습니다.")

    latest_log = (
        db.query(SensorLog)
        .filter(SensorLog.node_id == node_id)
        .order_by(SensorLog.measured_at.desc(), SensorLog.id.desc())
        .first()
    )

    unresolved_alerts = (
        db.query(Alert)
        .filter(
            Alert.node_id == node_id,
            Alert.is_resolved == False
        )
        .order_by(Alert.created_at.desc())
        .all()
    )

    if latest_log:
        inner_level = float(latest_log.inner_water_level)

        if inner_level >= 5:
            current_status = "OVERFLOODED"
        elif inner_level >= 0:
            current_status = "FLOODED"
        elif inner_level > -15:
            current_status = "DRYING"
        else:
            current_status = "DRY"
    else:
        current_status = "NO_DATA"

    data = {
        "node_id": node.id,
        "field_id": node.field_id,
        "mac_address": node.mac_address,
        "is_active": node.is_active,
        "location_desc": node.location_desc,
        "latest_log": {
            "inner_water_level": latest_log.inner_water_level,
            "outer_water_level": latest_log.outer_water_level,
            "battery_voltage": latest_log.battery_voltage,
            "measured_at": latest_log.measured_at,
        } if latest_log else None,
        "current_status": current_status,
        "has_unresolved_alert": len(unresolved_alerts) > 0,
        "unresolved_alert_count": len(unresolved_alerts),
        "latest_unresolved_alert": {
            "id": unresolved_alerts[0].id,
            "alert_type": unresolved_alerts[0].alert_type,
            "message": unresolved_alerts[0].message,
            "created_at": unresolved_alerts[0].created_at,
        } if unresolved_alerts else None
    }

    return success_response(data, "기기 상태 조회 성공")