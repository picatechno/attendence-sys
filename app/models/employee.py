import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Date, UniqueConstraint, JSON, Integer
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=True)
    employee_code = Column(String(50), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    gender = Column(String(10))
    date_of_birth = Column(Date)
    date_of_joining = Column(Date, nullable=False)
    date_of_exit = Column(Date)
    employment_type = Column(String(50), default="full_time")
    designation = Column(String(255))
    grade = Column(String(50))
    reporting_to_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    work_email = Column(String(255))
    work_phone = Column(String(50))
    emergency_contact_name = Column(String(255))
    emergency_contact_phone = Column(String(50))
    avatar_url = Column(Text)
    biometric_ids = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    organization = relationship("Organization", back_populates="employees")
    department = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    location = relationship("Location", back_populates="employees")
    user = relationship("User", back_populates="employee", uselist=False, foreign_keys="User.employee_id")
    reporting_to = relationship("Employee", remote_side=[id], backref="subordinates")
    attendances = relationship("Attendance", back_populates="employee")
    leaves = relationship("Leave", back_populates="employee", foreign_keys="Leave.employee_id")
    leave_balances = relationship("LeaveBalance", back_populates="employee")
    documents = relationship("Document", back_populates="employee")
    employee_devices = relationship("EmployeeDevice", back_populates="employee")

    __table_args__ = (
        UniqueConstraint("org_id", "employee_code", name="uq_employee_code_per_org"),
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    doc_type = Column(String(100))
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100))
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_verified = Column(Boolean, default=False)
    expires_at = Column(Date)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    employee = relationship("Employee", back_populates="documents")
