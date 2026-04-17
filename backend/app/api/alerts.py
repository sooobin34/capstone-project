from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.alert import Alert
from app.models.iot_node import IotNode
from app.utils.response import success_response

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
def get_alerts(
    field_id: int | None = Query(default=None),
    node_id: int | None = Query(default=None),
    alert_type: str | None = Query(default=None),
    is_resolved: bool | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(Alert).join(IotNode, IotNode.id == Alert.node_id)

    # 기존 필터
    if field_id is not None:
        query = query.filter(IotNode.field_id == field_id)

    # ✅ 추가 필터들
    if node_id is not None:
        query = query.filter(Alert.node_id == node_id)

    if alert_type is not None:
        query = query.filter(Alert.alert_type == alert_type)

    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)

    alerts = query.order_by(Alert.created_at.desc()).all()

    return success_response(alerts, "알림 목록 조회 성공")


@router.get("/count")
def get_alert_count(
    node_id: int,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    node = db.query(IotNode).filter(IotNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="해당 node_id가 존재하지 않습니다.")

    since_datetime = datetime.now() - timedelta(hours=hours)

    count = (
        db.query(func.count(Alert.id))
        .filter(
            Alert.node_id == node_id,
            Alert.created_at >= since_datetime
        )
        .scalar()
    )

    data = {
        "node_id": node_id,
        "hours": hours,
        "count_24h": int(count or 0)
    }

    return success_response(data, "24시간 알람 개수 조회 성공")


@router.patch("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="해당 알림이 존재하지 않습니다.")

    alert.is_resolved = True

    db.commit()
    db.refresh(alert)

    return success_response(alert, "알림 해결 처리 완료")