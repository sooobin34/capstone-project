from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.awd_daily_summary import AwdDailySummary
from app.models.iot_node import IotNode
from app.models.sensor_log import SensorLog
from app.schemas.awd_daily_summary import DailySummaryCreate
from app.utils.response import success_response

router = APIRouter(prefix="/daily-summaries", tags=["Daily Summaries"])


def determine_daily_status(avg_inner_level: Decimal) -> str:
    if avg_inner_level >= Decimal("0"):
        return "FLOODED"
    elif avg_inner_level > Decimal("-15"):
        return "DRYING"
    else:
        return "DRY"


@router.post("")
def create_daily_summary(payload: DailySummaryCreate, db: Session = Depends(get_db)):
    node = db.query(IotNode).filter(IotNode.id == payload.node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="해당 node_id가 존재하지 않습니다.")

    existing_summary = (
        db.query(AwdDailySummary)
        .filter(
            AwdDailySummary.node_id == payload.node_id,
            AwdDailySummary.record_date == payload.record_date
        )
        .first()
    )
    if existing_summary:
        raise HTTPException(status_code=400, detail="해당 날짜의 요약이 이미 존재합니다.")

    start_datetime = datetime.combine(payload.record_date, time.min)
    end_datetime = start_datetime + timedelta(days=1)

    avg_value = (
        db.query(func.avg(SensorLog.inner_water_level))
        .filter(
            SensorLog.node_id == payload.node_id,
            SensorLog.measured_at >= start_datetime,
            SensorLog.measured_at < end_datetime
        )
        .scalar()
    )

    if avg_value is None:
        raise HTTPException(status_code=404, detail="해당 날짜의 센서 로그가 없습니다.")

    avg_decimal = Decimal(str(avg_value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    daily_status = determine_daily_status(avg_decimal)

    summary = AwdDailySummary(
        node_id=payload.node_id,
        record_date=payload.record_date,
        daily_status=daily_status,
        avg_inner_level=avg_decimal,
    )

    db.add(summary)
    db.commit()
    db.refresh(summary)

    return success_response(summary, "일일 요약 생성 성공")


@router.get("")
def get_daily_summaries(db: Session = Depends(get_db)):
    summaries = (
        db.query(AwdDailySummary)
        .order_by(AwdDailySummary.record_date.desc(), AwdDailySummary.id.desc())
        .all()
    )
    return success_response(summaries, "일일 요약 조회 성공")