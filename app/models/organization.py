import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer, DECIMAL
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(255))
    logo_url = Column(Text)
    timezone = Column(String(50), default="UTC")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    departments = relationship("Department", back_populates="organization")
    locations = relationship("Location", back_populates="organization")
    employees = relationship("Employee", back_populates="organization")
    devices = relationship("Device", back_populates="organization")
    shifts = relationship("Shift", back_populates="organization")
    leave_types = relationship("LeaveType", back_populates="organization")
    roles = relationship("Role", back_populates="organization")


class Department(Base):
    __tablename__ = "departments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    parent_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    manager_id = Column(String(36), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    organization = relationship("Organization", back_populates="departments")
    children = relationship("Department", backref="parent", remote_side=[id])
    employees = relationship("Employee", back_populates="department", foreign_keys="Employee.department_id")



class Location(Base):
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    latitude = Column(DECIMAL(10, 7))
    longitude = Column(DECIMAL(10, 7))
    radius_meters = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    organization = relationship("Organization", back_populates="locations")
    employees = relationship("Employee", back_populates="location")
    devices = relationship("Device", back_populates="location")
