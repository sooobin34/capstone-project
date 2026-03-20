from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.alert import Alert
from app.models.iot_node import IotNode
from app.utils.response import success_response

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
def get_alerts(
    field_id: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(Alert).join(IotNode, IotNode.id == Alert.node_id)

    if field_id is not None:
        query = query.filter(IotNode.field_id == field_id)

    alerts = query.order_by(Alert.created_at.desc()).all()
    return success_response(alerts, "알림 목록 조회 성공")


@router.patch("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="해당 알림이 존재하지 않습니다.")

    alert.is_resolved = True

    db.commit()
    db.refresh(alert)

    return success_response(alert, "알림 해결 처리 완료")