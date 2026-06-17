from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class DeviceRegister(BaseModel):
    serial_number: str
    device_name: Optional[str] = None
    device_model: str = "MA100"
    ip_address: Optional[str] = None


class DeviceResponse(BaseModel):
    id: str
    serial_number: str
    device_name: Optional[str] = None
    device_model: Optional[str] = None
    ip_address: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    status: str = "offline"
    location_id: Optional[str] = None
    is_active: bool = True

    model_config = {"from_attributes": True}


class DeviceLogResponse(BaseModel):
    id: int
    device_id: str
    zk_user_id: str
    employee_id: Optional[str] = None
    punch_time: datetime
    punch_type: Optional[str] = None
    verify_mode: Optional[int] = 0
    processed: bool = False

    model_config = {"from_attributes": True}


class AttendanceResponse(BaseModel):
    id: str
    employee_id: str
    date: date
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    total_work_hours: Optional[int] = None
    net_work_hours: Optional[int] = None
    overtime_hours: Optional[int] = None
    status: str = "present"
    late_minutes: int = 0
    early_leave_minutes: int = 0
    shift_id: Optional[str] = None

    model_config = {"from_attributes": True}


class AttendanceUpdate(BaseModel):
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class DeviceCommand(BaseModel):
    command: str
    params: Optional[str] = None
