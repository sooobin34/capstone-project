from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class AwdDailySummary(Base):
    __tablename__ = "awd_daily_summaries"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("iot_nodes.id"), nullable=False)

    record_date = Column(Date, nullable=False)
    daily_status = Column(String(20), nullable=False)
    avg_inner_level = Column(Numeric(5, 2), nullable=True)

    node = relationship("IotNode")