from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
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
        existing_alert = (
            db.query(Alert)
            .filter(
                Alert.node_id == payload.node_id,
                Alert.alert_type == "LOW_WATER",
                Alert.is_resolved == False
            )
            .first()
        )

        if not existing_alert:
            alert = Alert(
                node_id=payload.node_id,
                alert_type="LOW_WATER",
                message="내부 수위가 -15cm 이하로 떨어졌습니다. 재관개가 필요합니다."
            )
            db.add(alert)
            db.commit()

    elif inner_level >= HIGH_WATER_THRESHOLD:
        existing_alert = (
            db.query(Alert)
            .filter(
                Alert.node_id == payload.node_id,
                Alert.alert_type == "HIGH_WATER",
                Alert.is_resolved == False
            )
            .first()
        )

        if not existing_alert:
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

@router.get("/node/{node_id}/range")
def get_sensor_logs_by_period(
    node_id: int,
    period: str = Query("1d", pattern="^(1h|1d|1w|1m)$"),
    db: Session = Depends(get_db)
):
    node = db.query(IotNode).filter(IotNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="해당 node_id가 존재하지 않습니다.")

    now = datetime.now()

    if period == "1h":
        start_datetime = now - timedelta(hours=1)
    elif period == "1d":
        start_datetime = now - timedelta(days=1)
    elif period == "1w":
        start_datetime = now - timedelta(weeks=1)
    elif period == "1m":
        start_datetime = now - timedelta(days=30)
    else:
        raise HTTPException(status_code=400, detail="period는 1h, 1d, 1w, 1m 중 하나여야 합니다.")

    logs = (
        db.query(SensorLog)
        .filter(
            SensorLog.node_id == node_id,
            SensorLog.measured_at >= start_datetime,
            SensorLog.measured_at <= now
        )
        .order_by(SensorLog.measured_at.asc())
        .all()
    )

    data = {
        "node_id": node_id,
        "period": period,
        "start": start_datetime,
        "end": now,
        "count": len(logs),
        "logs": logs,
    }

    return success_response(data, "기간별 센서 로그 조회 성공")

@router.get("/node/{node_id}/stats")
def get_sensor_log_stats(
    node_id: int,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    node = db.query(IotNode).filter(IotNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="해당 node_id가 존재하지 않습니다.")

    since_datetime = datetime.now() - timedelta(hours=hours)

    stats = (
        db.query(
            func.avg(SensorLog.inner_water_level).label("avg_inner_water_level"),
            func.max(SensorLog.inner_water_level).label("max_inner_water_level"),
            func.min(SensorLog.inner_water_level).label("min_inner_water_level"),
            func.avg(SensorLog.outer_water_level).label("avg_outer_water_level"),
            func.max(SensorLog.outer_water_level).label("max_outer_water_level"),
            func.min(SensorLog.outer_water_level).label("min_outer_water_level"),
            func.count(SensorLog.id).label("log_count"),
        )
        .filter(
            SensorLog.node_id == node_id,
            SensorLog.measured_at >= since_datetime
        )
        .first()
    )

    data = {
        "node_id": node_id,
        "hours": hours,
        "avg_inner_water_level": float(stats.avg_inner_water_level) if stats.avg_inner_water_level is not None else None,
        "max_inner_water_level": float(stats.max_inner_water_level) if stats.max_inner_water_level is not None else None,
        "min_inner_water_level": float(stats.min_inner_water_level) if stats.min_inner_water_level is not None else None,
        "avg_outer_water_level": float(stats.avg_outer_water_level) if stats.avg_outer_water_level is not None else None,
        "max_outer_water_level": float(stats.max_outer_water_level) if stats.max_outer_water_level is not None else None,
        "min_outer_water_level": float(stats.min_outer_water_level) if stats.min_outer_water_level is not None else None,
        "log_count": int(stats.log_count or 0),
    }

    return success_response(data, "24시간 수위 통계 조회 성공")


@router.get("/latest/{node_id}")
def get_latest_sensor_log(node_id: int, db: Session = Depends(get_db)):
    node = db.query(IotNode).filter(IotNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="해당 node_id가 존재하지 않습니다.")

    latest_log = (
        db.query(SensorLog)
        .filter(SensorLog.node_id == node_id)
        .order_by(SensorLog.measured_at.desc(), SensorLog.id.desc())
        .first()
    )

    if not latest_log:
        raise HTTPException(status_code=404, detail="해당 node의 센서 로그가 없습니다.")

    return success_response(latest_log, "최신 센서 로그 조회 성공")