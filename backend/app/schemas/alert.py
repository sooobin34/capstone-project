from datetime import datetime
from pydantic import BaseModel


class AlertRead(BaseModel):
    id: int
    node_id: int
    alert_type: str
    message: str
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True