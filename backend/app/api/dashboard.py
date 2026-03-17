from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.alert import Alert
from app.models.awd_daily_summary import AwdDailySummary
from app.models.mrv_report import MrvReport
from app.utils.response import success_response

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
def get_dashboard(db: Session = Depends(get_db)):
    total_alerts = db.query(Alert).count()
    unresolved_alerts = db.query(Alert).filter(Alert.is_resolved == False).count()

    latest_daily_summary = (
        db.query(AwdDailySummary)
        .order_by(AwdDailySummary.record_date.desc(), AwdDailySummary.id.desc())
        .first()
    )

    latest_mrv_report = (
        db.query(MrvReport)
        .order_by(MrvReport.report_month.desc(), MrvReport.id.desc())
        .first()
    )

    data = {
        "total_alerts": total_alerts,
        "unresolved_alerts": unresolved_alerts,
        "latest_daily_summary": {
            "id": latest_daily_summary.id,
            "node_id": latest_daily_summary.node_id,
            "record_date": latest_daily_summary.record_date,
            "daily_status": latest_daily_summary.daily_status,
            "avg_inner_level": latest_daily_summary.avg_inner_level,
        } if latest_daily_summary else None,
        "latest_mrv_report": {
            "id": latest_mrv_report.id,
            "report_month": latest_mrv_report.report_month,
            "total_awd_cycles": latest_mrv_report.total_awd_cycles,
            "carbon_reduction": latest_mrv_report.carbon_reduction,
            "created_at": latest_mrv_report.created_at,
        } if latest_mrv_report else None
    }

    return success_response(data, "대시보드 요약 조회 성공")