from pydantic import BaseModel, field_serializer
from typing import Optional, Union
from datetime import time, date


class ShiftCreate(BaseModel):
    name: str
    code: Optional[str] = None
    start_time: str  # "09:00"
    end_time: str    # "18:00"
    grace_late_minutes: int = 15
    grace_early_minutes: int = 15
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    min_work_hours: int = 28800  # 8h in seconds
    is_night_shift: bool = False
    applicable_days: list[int] = [1, 2, 3, 4, 5, 6, 7]


class ShiftResponse(BaseModel):
    id: str
    name: str
    code: Optional[str] = None
    start_time: Union[str, time]
    end_time: Union[str, time]
    grace_late_minutes: int
    grace_early_minutes: int
    is_night_shift: bool
    is_active: bool

    model_config = {"from_attributes": True}

    @field_serializer("start_time", "end_time")
    @classmethod
    def serialize_time(cls, v):
        if isinstance(v, time):
            return v.strftime("%H:%M")
        return str(v)


class ShiftAssignmentCreate(BaseModel):
    employee_id: str
    shift_id: str
    effective_from: date
    effective_to: Optional[date] = None


class ShiftAssignmentResponse(BaseModel):
    id: str
    employee_id: str
    shift_id: str
    effective_from: date
    effective_to: Optional[date] = None

    model_config = {"from_attributes": True}


class HolidayCreate(BaseModel):
    name: str
    date: str  # "2026-12-25"
    is_recurring: bool = False
    type: str = "public"


class HolidayResponse(BaseModel):
    id: str
    name: str
    date: Union[str, date]
    is_recurring: bool
    type: str

    model_config = {"from_attributes": True}

    @field_serializer("date")
    @classmethod
    def serialize_date(cls, v):
        if isinstance(v, date):
            return v.isoformat()
        return str(v)
