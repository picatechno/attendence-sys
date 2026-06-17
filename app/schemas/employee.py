from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class EmployeeCreate(BaseModel):
    employee_code: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_joining: date
    employment_type: str = "full_time"
    designation: Optional[str] = None
    grade: Optional[str] = None
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    reporting_to_id: Optional[str] = None
    work_email: Optional[str] = None
    work_phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_joining: Optional[date] = None
    date_of_exit: Optional[date] = None
    employment_type: Optional[str] = None
    designation: Optional[str] = None
    grade: Optional[str] = None
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    reporting_to_id: Optional[str] = None
    work_email: Optional[str] = None
    work_phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    is_active: Optional[bool] = None


class EmployeeResponse(BaseModel):
    id: str
    employee_code: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_joining: Optional[date] = None
    date_of_exit: Optional[date] = None
    employment_type: Optional[str] = None
    designation: Optional[str] = None
    grade: Optional[str] = None
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    reporting_to_id: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EmployeeListResponse(BaseModel):
    items: list[EmployeeResponse]
    total: int
    page: int
    page_size: int


class DepartmentCreate(BaseModel):
    name: str
    code: Optional[str] = None
    parent_id: Optional[str] = None
    manager_id: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: str
    name: str
    code: Optional[str] = None
    parent_id: Optional[str] = None
    manager_id: Optional[str] = None
    is_active: bool = True

    model_config = {"from_attributes": True}


class LocationCreate(BaseModel):
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: int = 100


class LocationResponse(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: int = 100
    is_active: bool = True

    model_config = {"from_attributes": True}
