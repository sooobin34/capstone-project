from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class ValidationRecord(Base):
    __tablename__ = "validation_records"

    id = Column(Integer, primary_key=True, index=True)

    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False, index=True)
    node_id = Column(Integer, ForeignKey("iot_nodes.id"), nullable=True, index=True)

    record_date = Column(Date, nullable=False, index=True)

    image_url = Column(String, nullable=False)
    image_title = Column(String, nullable=True)

    # 센서가 판단한 상태
    sensor_predicted_status = Column(String(20), nullable=True)

    # 사진/사람이 관찰한 표면 상태
    observed_surface_status = Column(String(30), nullable=True)

    # 센서 상태와 표면 관찰 결과의 일치 여부
    is_match = Column(Boolean, nullable=True)

    note = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())