from sqlalchemy import Column, DateTime, Integer, Numeric, String
from sqlalchemy.sql import func

from app.core.database import Base


class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    field_name = Column(String(100), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    location_desc = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())