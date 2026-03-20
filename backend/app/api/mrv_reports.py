from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.awd_daily_summary import AwdDailySummary
from app.models.field import Field
from app.models.iot_node import IotNode
from app.models.mrv_report import MrvReport
from app.schemas.mrv_report import MrvReportCreate
from app.utils.response import success_response

router = APIRouter(prefix="/mrv-reports", tags=["MRV Reports"])


def get_month_range(report_month: str) -> tuple[date, date]:
    year, month = map(int, report_month.split("-"))

    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    return start_date, end_date


@router.post("")
def create_mrv_report(payload: MrvReportCreate, db: Session = Depends(get_db)):
    field = db.query(Field).filter(Field.id == payload.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="해당 field_id가 존재하지 않습니다.")

    existing_report = (
        db.query(MrvReport)
        .filter(
            MrvReport.field_id == payload.field_id,
            MrvReport.report_month == payload.report_month
        )
        .first()
    )
    if existing_report:
        raise HTTPException(status_code=400, detail="해당 논의 해당 월 MRV 리포트가 이미 존재합니다.")

    start_date, end_date = get_month_range(payload.report_month)

    summaries = (
        db.query(AwdDailySummary)
        .join(IotNode, IotNode.id == AwdDailySummary.node_id)
        .filter(
            IotNode.field_id == payload.field_id,
            AwdDailySummary.record_date >= start_date,
            AwdDailySummary.record_date < end_date
        )
        .all()
    )

    if not summaries:
        raise HTTPException(status_code=404, detail="해당 논의 해당 월 일일 요약 데이터가 없습니다.")

    total_awd_cycles = sum(1 for summary in summaries if summary.daily_status == "DRY")
    carbon_reduction = (Decimal(total_awd_cycles) * Decimal("15.25")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    report = MrvReport(
        field_id=payload.field_id,
        report_month=payload.report_month,
        total_awd_cycles=total_awd_cycles,
        carbon_reduction=carbon_reduction,
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return success_response(report, "MRV 리포트 생성 성공")


@router.get("")
def get_mrv_reports(
    field_id: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(MrvReport)

    if field_id is not None:
        query = query.filter(MrvReport.field_id == field_id)

    reports = query.order_by(MrvReport.report_month.desc()).all()
    return success_response(reports, "MRV 리포트 조회 성공")