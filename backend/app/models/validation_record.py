from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.sql import func

from app.core.database import Base


class ValidationRecord(Base):
    __tablename__ = "validation_records"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False, index=True)
    node_id = Column(Integer, ForeignKey("iot_nodes.id"), nullable=True, index=True)
    record_date = Column(Date, nullable=False, index=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)
    image_url = Column(String(255), nullable=False)
    image_title = Column(String(255), nullable=True)
    camera_height_cm = Column(Numeric(6, 2), nullable=True)
    actual_water_level_cm = Column(Numeric(6, 2), nullable=True)
    sensor_predicted_status = Column(String(50), nullable=True)
    observed_surface_status = Column(String(50), nullable=True)
    ai_predicted_status = Column(String(50), nullable=True)
    ai_confidence = Column(Numeric(5, 2), nullable=True)
    is_match = Column(Boolean, nullable=True)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
