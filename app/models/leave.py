import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer, Date, DECIMAL
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class LeaveType(Base):
    __tablename__ = "leave_types"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    is_paid = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=True)
    max_days_per_request = Column(Integer, default=30)
    min_notice_days = Column(Integer, default=1)
    carry_forward = Column(Boolean, default=False)
    carry_forward_limit = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    organization = relationship("Organization", back_populates="leave_types")
    balances = relationship("LeaveBalance", back_populates="leave_type")
    leaves = relationship("Leave", back_populates="leave_type")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    leave_type_id = Column(String(36), ForeignKey("leave_types.id"), nullable=False)
    year = Column(Integer, nullable=False)
    total_days = Column(Integer, nullable=False)
    used_days = Column(Integer, default=0)
    pending_days = Column(Integer, default=0)
    carried_forward = Column(Integer, default=0)

    employee = relationship("Employee", back_populates="leave_balances")
    leave_type = relationship("LeaveType", back_populates="balances")


class Leave(Base):
    __tablename__ = "leaves"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    leave_type_id = Column(String(36), ForeignKey("leave_types.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Integer, nullable=False)
    reason = Column(Text)
    status = Column(String(20), default="pending")
    approved_by = Column(String(36), ForeignKey("employees.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True))
    attachment_url = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    employee = relationship("Employee", back_populates="leaves", foreign_keys=[employee_id])
    leave_type = relationship("LeaveType", back_populates="leaves")
    approver = relationship("Employee", foreign_keys=[approved_by], primaryjoin="Employee.id == Leave.approved_by")
