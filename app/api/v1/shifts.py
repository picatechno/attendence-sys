"""Shift and holiday management endpoints"""
from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.auth import User
from app.schemas.shift import (
    ShiftCreate, ShiftResponse,
    ShiftAssignmentCreate, ShiftAssignmentResponse,
    HolidayCreate, HolidayResponse,
)
from app.services.shift import ShiftService, ShiftAssignmentService, HolidayService
from app.api.deps import get_user_with_permissions

shift_router = APIRouter(prefix="/api/v1/shifts", tags=["Shifts"])
holiday_router = APIRouter(prefix="/api/v1/holidays", tags=["Holidays"])
assignment_router = APIRouter(prefix="/api/v1/shift-assignments", tags=["Shift Assignments"])

admin_or_manager = get_user_with_permissions("attendance:manage")


# ---- Shifts ----

@shift_router.get("", response_model=list[ShiftResponse])
async def list_shifts(
    current_user: User = Depends(admin_or_manager),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else "SYSTEM"
    return await ShiftService.list(db, org_id)


@shift_router.post("", response_model=ShiftResponse, status_code=201)
async def create_shift(
    data: ShiftCreate,
    current_user: User = Depends(admin_or_manager),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else "SYSTEM"
    return await ShiftService.create(db, org_id, data)


@shift_router.put("/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: str,
    data: ShiftCreate,
    current_user: User = Depends(admin_or_manager),
    db: AsyncSession = Depends(get_db),
):
    shift = await ShiftService.update(db, shift_id, data)
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    return shift


@shift_router.delete("/{shift_id}", status_code=204)
async def delete_shift(
    shift_id: str,
    current_user: User = Depends(admin_or_manager),
    db: AsyncSession = Depends(get_db),
):
    ok = await ShiftService.delete(db, shift_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Shift not found")


# ---- Shift Assignments ----

@assignment_router.get("", response_model=list[ShiftAssignmentResponse])
async def list_assignments(
    employee_id: Optional[str] = None,
    current_user: User = Depends(admin_or_manager),
    db: AsyncSession = Depends(get_db),
):
    return await ShiftAssignmentService.list(db, employee_id)


@assignment_router.post("", response_model=ShiftAssignmentResponse, status_code=201)
async def create_assignment(
    data: ShiftAssignmentCreate,
    current_user: User = Depends(admin_or_manager),
    db: AsyncSession = Depends(get_db),
):
    return await ShiftAssignmentService.create(db, data)


@assignment_router.delete("/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: str,
    current_user: User = Depends(admin_or_manager),
    db: AsyncSession = Depends(get_db),
):
    ok = await ShiftAssignmentService.delete(db, assignment_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Assignment not found")


# ---- Holidays ----

@holiday_router.get("", response_model=list[HolidayResponse])
async def list_holidays(
    year: int,
    current_user: User = Depends(admin_or_manager),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else "SYSTEM"
    return await HolidayService.list(db, org_id, year)


@holiday_router.post("", response_model=HolidayResponse, status_code=201)
async def create_holiday(
    data: HolidayCreate,
    current_user: User = Depends(admin_or_manager),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else "SYSTEM"
    return await HolidayService.add_holiday(db, org_id, data)


@holiday_router.delete("/{holiday_id}", status_code=204)
async def delete_holiday(
    holiday_id: str,
    current_user: User = Depends(admin_or_manager),
    db: AsyncSession = Depends(get_db),
):
    ok = await HolidayService.delete(db, holiday_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Holiday not found")
