from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class SensorLog(Base):
    __tablename__ = "sensor_logs"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("iot_nodes.id"), nullable=False)

    inner_water_level = Column(Numeric(5, 2), nullable=False)
    outer_water_level = Column(Numeric(5, 2), nullable=False)
    battery_voltage = Column(Numeric(4, 2), nullable=True)

    measured_at = Column(DateTime(timezone=True), nullable=False)

    node = relationship("IotNode")
