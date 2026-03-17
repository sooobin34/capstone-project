from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.alert import Alert
from app.models.iot_node import IotNode
from app.models.sensor_log import SensorLog
from app.schemas.sensor_log import SensorLogCreate
from app.utils.response import success_response

router = APIRouter(prefix="/sensor-logs", tags=["Sensor Logs"])

LOW_WATER_THRESHOLD = -15.0
HIGH_WATER_THRESHOLD = 5.0


@router.post("")
def create_sensor_log(payload: SensorLogCreate, db: Session = Depends(get_db)):
    node = db.query(IotNode).filter(IotNode.id == payload.node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="해당 node_id가 존재하지 않습니다.")

    sensor_log = SensorLog(
        node_id=payload.node_id,
        inner_water_level=payload.inner_water_level,
        outer_water_level=payload.outer_water_level,
        battery_voltage=payload.battery_voltage,
        measured_at=payload.measured_at,
    )

    db.add(sensor_log)
    db.commit()
    db.refresh(sensor_log)

    inner_level = float(payload.inner_water_level)

    if inner_level <= LOW_WATER_THRESHOLD:
        alert = Alert(
            node_id=payload.node_id,
            alert_type="LOW_WATER",
            message="내부 수위가 -15cm 이하로 떨어졌습니다. 재관개가 필요합니다."
        )
        db.add(alert)
        db.commit()

    elif inner_level >= HIGH_WATER_THRESHOLD:
        alert = Alert(
            node_id=payload.node_id,
            alert_type="HIGH_WATER",
            message="내부 수위가 기준 이상으로 높습니다."
        )
        db.add(alert)
        db.commit()

    return success_response(sensor_log, "센서 로그 저장 성공")


@router.get("/node/{node_id}")
def get_sensor_logs_by_node(
    node_id: int,
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db)
):
    node = db.query(IotNode).filter(IotNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="해당 node_id가 존재하지 않습니다.")

    if start and end and start > end:
        raise HTTPException(status_code=400, detail="start 날짜가 end 날짜보다 늦을 수 없습니다.")

    query = db.query(SensorLog).filter(SensorLog.node_id == node_id)

    if start:
        start_datetime = datetime.combine(start, time.min)
        query = query.filter(SensorLog.measured_at >= start_datetime)

    if end:
        end_datetime = datetime.combine(end + timedelta(days=1), time.min)
        query = query.filter(SensorLog.measured_at < end_datetime)

    logs = (
        query
        .order_by(SensorLog.measured_at.asc())
        .all()
    )

    return success_response(logs, "센서 로그 조회 성공")