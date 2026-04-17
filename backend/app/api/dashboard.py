from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.alert import Alert
from app.models.awd_daily_summary import AwdDailySummary
from app.models.field import Field
from app.models.iot_node import IotNode
from app.models.mrv_report import MrvReport
from app.models.sensor_log import SensorLog
from app.utils.response import success_response

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
def get_dashboard(
    field_id: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    alert_query = db.query(Alert).join(IotNode, IotNode.id == Alert.node_id)
    summary_query = db.query(AwdDailySummary).join(IotNode, IotNode.id == AwdDailySummary.node_id)
    mrv_query = db.query(MrvReport)
    node_query = db.query(IotNode)
    sensor_log_query = db.query(SensorLog).join(IotNode, IotNode.id == SensorLog.node_id)

    if field_id is not None:
        alert_query = alert_query.filter(IotNode.field_id == field_id)
        summary_query = summary_query.filter(IotNode.field_id == field_id)
        mrv_query = mrv_query.filter(MrvReport.field_id == field_id)
        node_query = node_query.filter(IotNode.field_id == field_id)
        sensor_log_query = sensor_log_query.filter(IotNode.field_id == field_id)
        total_fields = db.query(Field).filter(Field.id == field_id).count()
    else:
        total_fields = db.query(Field).count()

    total_nodes = node_query.count()
    total_alerts = alert_query.count()
    unresolved_alerts = alert_query.filter(Alert.is_resolved == False).count()

    latest_daily_summary = (
        summary_query
        .order_by(AwdDailySummary.record_date.desc(), AwdDailySummary.id.desc())
        .first()
    )

    latest_mrv_report = (
        mrv_query
        .order_by(MrvReport.created_at.desc(), MrvReport.id.desc())
        .first()
    )

    latest_sensor_log = (
        sensor_log_query
        .order_by(SensorLog.measured_at.desc(), SensorLog.id.desc())
        .first()
    )

    recent_alert_rows = (
        alert_query
        .order_by(Alert.created_at.desc(), Alert.id.desc())
        .limit(5)
        .all()
    )

    recent_alerts = [
        {
            "id": alert.id,
            "node_id": alert.node_id,
            "alert_type": alert.alert_type,
            "message": alert.message,
            "is_resolved": alert.is_resolved,
            "created_at": alert.created_at,
        }
        for alert in recent_alert_rows
    ]

    latest_mrv_report_data = None
    if latest_mrv_report:
        field = db.query(Field).filter(Field.id == latest_mrv_report.field_id).first()
        latest_mrv_report_data = {
            "id": latest_mrv_report.id,
            "field_id": latest_mrv_report.field_id,
            "field_name": field.field_name if field else None,
            "report_month": latest_mrv_report.report_month,
            "total_awd_cycles": latest_mrv_report.total_awd_cycles,
            "flood_days": latest_mrv_report.flood_days,
            "status": latest_mrv_report.status,
            "carbon_reduction": latest_mrv_report.carbon_reduction,
            "created_at": latest_mrv_report.created_at,
        }

    data = {
        "field_id": field_id,
        "total_fields": total_fields,
        "total_nodes": total_nodes,
        "total_alerts": total_alerts,
        "unresolved_alerts": unresolved_alerts,
        "latest_measured_at": latest_sensor_log.measured_at if latest_sensor_log else None,
        "recent_alerts": recent_alerts,
        "latest_daily_summary": {
            "id": latest_daily_summary.id,
            "node_id": latest_daily_summary.node_id,
            "record_date": latest_daily_summary.record_date,
            "daily_status": latest_daily_summary.daily_status,
            "avg_inner_level": latest_daily_summary.avg_inner_level,
        } if latest_daily_summary else None,
        "latest_mrv_report": latest_mrv_report_data
    }

    return success_response(data, "대시보드 요약 조회 성공")