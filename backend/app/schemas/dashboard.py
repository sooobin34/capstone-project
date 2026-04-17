from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


class LatestDailySummary(BaseModel):
    id: int
    node_id: int
    record_date: date
    daily_status: str
    avg_inner_level: Decimal | None = None


class LatestMrvReport(BaseModel):
    id: int
    field_id: int
    report_month: str
    total_awd_cycles: int
    flood_days: int
    status: str
    carbon_reduction: Decimal | None = None
    created_at: datetime


class RecentAlert(BaseModel):
    id: int
    node_id: int
    alert_type: str
    message: str
    is_resolved: bool
    created_at: datetime


class DashboardSummary(BaseModel):
    field_id: int | None = None
    total_fields: int
    total_nodes: int
    total_alerts: int
    unresolved_alerts: int
    latest_measured_at: datetime | None = None
    recent_alerts: list[RecentAlert] = []
    latest_daily_summary: LatestDailySummary | None = None
    latest_mrv_report: LatestMrvReport | None = None