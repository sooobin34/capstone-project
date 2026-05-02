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

    # 센서 기준 상태: OVERFLOODED / FLOODED / DRYING / DRY
    sensor_predicted_status = Column(String(50), nullable=True)

    # 사진/사람 관찰 기준 표면 상태: WATER_VISIBLE / NO_WATER_VISIBLE / UNKNOWN
    observed_surface_status = Column(String(50), nullable=True)

    # AI 분석 결과: WATER_VISIBLE / NO_WATER_VISIBLE / UNKNOWN
    ai_predicted_status = Column(String(50), nullable=True)
    ai_confidence = Column(Numeric(5, 2), nullable=True)

    # 센서 상태와 사진 관찰 결과의 일치 여부
    is_match = Column(Boolean, nullable=True)

    # 센서 상태와 AI 분석 결과의 일치 여부
    # 단, is_match가 True인 검증 데이터에서만 계산한다.
    ai_sensor_match = Column(Boolean, nullable=True)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())