import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Date
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class HolidayCalendar(Base):
    __tablename__ = "holiday_calendars"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255))
    year = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    calendar_id = Column(String(36), ForeignKey("holiday_calendars.id"), nullable=False)
    name = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    is_recurring = Column(Boolean, default=False)
    type = Column(String(50), default="public")

    calendar = relationship("HolidayCalendar")
