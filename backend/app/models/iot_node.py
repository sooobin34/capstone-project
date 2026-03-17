from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class IotNode(Base):
    __tablename__ = "iot_nodes"

    id = Column(Integer, primary_key=True, index=True)
    mac_address = Column(String(50), unique=True, nullable=False)

    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)

    location_desc = Column(String(100))

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())