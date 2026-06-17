import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer, Time, Date, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class DeviceLog(Base):
    __tablename__ = "device_logs"
    __table_args__ = (
        UniqueConstraint("device_id", "zk_user_id", "punch_time", name="uq_device_log_punch"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    zk_user_id = Column(String(50), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    punch_time = Column(DateTime(timezone=True), nullable=False, index=True)
    punch_type = Column(String(20))
    verify_mode = Column(Integer, default=0)
    temperature = Column(Integer)
    raw_data = Column(JSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    device = relationship("Device", back_populates="device_logs")
    employee = relationship("Employee")


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    grace_late_minutes = Column(Integer, default=15)
    grace_early_minutes = Column(Integer, default=15)
    break_start = Column(Time)
    break_end = Column(Time)
    min_work_hours = Column(Integer, default=28800)  # 8 hours in seconds
    is_night_shift = Column(Boolean, default=False)
    applicable_days = Column(JSON, default=lambda: [1, 2, 3, 4, 5, 6, 7])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    organization = relationship("Organization", back_populates="shifts")
    assignments = relationship("ShiftAssignment", back_populates="shift")
    attendances = relationship("Attendance", back_populates="shift")


class ShiftAssignment(Base):
    __tablename__ = "shift_assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    shift_id = Column(String(36), ForeignKey("shifts.id"), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    is_rotation = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    employee = relationship("Employee")
    shift = relationship("Shift", back_populates="assignments")


class AttendancePolicy(Base):
    __tablename__ = "attendance_policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    auto_approve = Column(Boolean, default=False)
    require_geofence = Column(Boolean, default=False)
    require_photo = Column(Boolean, default=False)
    overtime_enabled = Column(Boolean, default=True)
    overtime_rate = Column(Integer, default=15)  # 1.5 * 10
    late_threshold = Column(Integer, default=30)
    absent_threshold = Column(Integer, default=240)
    max_early_leave = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    clock_in = Column(DateTime(timezone=True))
    clock_out = Column(DateTime(timezone=True))
    total_work_hours = Column(Integer)  # seconds
    total_break_hours = Column(Integer)  # seconds
    net_work_hours = Column(Integer)  # seconds
    overtime_hours = Column(Integer)  # seconds
    status = Column(String(30), default="present")
    late_minutes = Column(Integer, default=0)
    early_leave_minutes = Column(Integer, default=0)
    shift_id = Column(String(36), ForeignKey("shifts.id"), nullable=True)
    clock_in_log_id = Column(Integer, ForeignKey("device_logs.id"), nullable=True)
    clock_out_log_id = Column(Integer, ForeignKey("device_logs.id"), nullable=True)
    is_auto_processed = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    employee = relationship("Employee", back_populates="attendances")
    shift = relationship("Shift", back_populates="attendances")
