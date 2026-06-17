import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=True)
    serial_number = Column(String(100), unique=True, nullable=False, index=True)
    device_name = Column(String(255))
    device_model = Column(String(100), default="MA100")
    ip_address = Column(String(45))
    firmware_version = Column(String(100))
    push_interval = Column(Integer, default=5)
    last_heartbeat = Column(DateTime(timezone=True))
    last_sync_at = Column(DateTime(timezone=True))
    timezone = Column(String(50), default="UTC")
    status = Column(String(20), default="offline")
    config = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    organization = relationship("Organization", back_populates="devices")
    location = relationship("Location", back_populates="devices")
    employee_devices = relationship("EmployeeDevice", back_populates="device")
    device_logs = relationship("DeviceLog", back_populates="device")


class EmployeeDevice(Base):
    __tablename__ = "employee_devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    zk_user_id = Column(String(50), nullable=False)
    fingerprint_template = Column(Text)
    face_template = Column(Text)
    card_number = Column(String(50))
    pin = Column(String(50))
    privilege = Column(String(20), default="user")
    enrolled_at = Column(DateTime(timezone=True), default=utcnow)

    employee = relationship("Employee", back_populates="employee_devices")
    device = relationship("Device", back_populates="employee_devices")
