from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_alerts: int
    unresolved_alerts: int
    latest_daily_summary: dict | None = None
    latest_mrv_report: dict | None = None