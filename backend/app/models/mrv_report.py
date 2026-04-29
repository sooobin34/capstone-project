from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.sql import func

from app.core.database import Base


class MrvReport(Base):
    __tablename__ = "mrv_reports"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False, index=True)

    report_month = Column(String(7), nullable=False)
    total_awd_cycles = Column(Integer, default=0)
    flood_days = Column(Integer, default=0)
    status = Column(String(20), default="IN_PROGRESS")
    carbon_reduction = Column(Numeric(8, 2), nullable=True)
    validation_method = Column(String(50), nullable=True)
    validation_sample_count = Column(Integer, default=0)
    validation_match_count = Column(Integer, default=0)
    validation_accuracy = Column(Numeric(5, 2), nullable=True)
    validation_note = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
