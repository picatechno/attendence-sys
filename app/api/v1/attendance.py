from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sa_func

from app.database import get_db
from app.models.auth import User
from app.models.attendance import Attendance
from app.schemas.attendance import AttendanceResponse, AttendanceUpdate, DeviceResponse, DeviceLogResponse, DeviceCommand
from app.services.attendance import AttendanceService
from app.services.device import DeviceService
from app.services.calculator import AttendanceCalculator
from app.core.security import get_current_user
from app.api.deps import get_user_with_permissions


class PaginatedDeviceLogs(BaseModel):
    items: list[DeviceLogResponse]
    total: int
    page: int
    page_size: int

router = APIRouter(prefix="/attendances", tags=["Attendance"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
device_router = APIRouter(prefix="/devices", tags=["Devices"])


# ----- Attendance endpoints -----

@router.get("", response_model=dict)
async def list_attendances(
    employee_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_user_with_permissions("attendance:read_all")),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else None
    items, total = await AttendanceService.list(db, org_id, employee_id, date_from, date_to, status, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{att_id}", response_model=AttendanceResponse)
async def get_attendance(
    att_id: str,
    current_user: User = Depends(get_user_with_permissions("attendance:read_all")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.get(Attendance, att_id)
    if not result:
        raise HTTPException(status_code=404, detail="Attendance not found")
    return result


@router.put("/{att_id}", response_model=AttendanceResponse)
async def update_attendance(
    att_id: str,
    data: AttendanceUpdate,
    current_user: User = Depends(get_user_with_permissions("attendance:manual_edit")),
    db: AsyncSession = Depends(get_db),
):
    att = await AttendanceService.update(db, att_id, data)
    if not att:
        raise HTTPException(status_code=404, detail="Attendance not found")
    return att


@router.post("/compute")
async def compute_attendance(
    employee_id: str,
    att_date: date,
    current_user: User = Depends(get_user_with_permissions("attendance:manual_edit")),
    db: AsyncSession = Depends(get_db),
):
    """Compute attendance for a single employee on a single date using the full engine."""
    att = await AttendanceCalculator.compute_attendance(db, employee_id, att_date)
    return AttendanceResponse.model_validate(att)


@router.post("/reprocess")
async def reprocess_attendance(
    employee_id: str,
    date_from: date,
    date_to: date,
    current_user: User = Depends(get_user_with_permissions("attendance:manual_edit")),
    db: AsyncSession = Depends(get_db),
):
    count = await AttendanceService.reprocess_range(db, employee_id, date_from, date_to)
    return {"message": f"Reprocessed {count} days for employee {employee_id}"}


# ----- Device endpoints -----

@device_router.get("", response_model=list[DeviceResponse])
async def list_devices(
    current_user: User = Depends(get_user_with_permissions("device:view_logs")),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else "SYSTEM"
    return await DeviceService.get_all(db, org_id)


@device_router.get("/{device_id}/logs", response_model=PaginatedDeviceLogs)
async def get_device_logs(
    device_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_user_with_permissions("device:view_logs")),
    db: AsyncSession = Depends(get_db),
):
    logs, total = await DeviceService.list_logs(db, device_id, page, page_size)
    return {"items": logs, "total": total, "page": page, "page_size": page_size}


# ----- Dashboard endpoints -----

@dashboard_router.get("/stats")
async def dashboard_stats(
    current_user: User = Depends(get_user_with_permissions("attendance:read_all")),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else ""

    from app.models.employee import Employee
    from app.models.attendance import Attendance

    today = date.today()

    # Total active employees
    emp_count_q = select(sa_func.count(Employee.id)).where(
        Employee.org_id == org_id, Employee.is_active == True
    )
    total_emp = (await db.execute(emp_count_q)).scalar() or 0

    emp_ids_subq = select(Employee.id).where(Employee.org_id == org_id)

    today_total = (await db.execute(
        select(sa_func.count(Attendance.id)).where(
            Attendance.date == today,
            Attendance.employee_id.in_(emp_ids_subq),
        )
    )).scalar() or 0

    status_counts = {}
    for status in ("present", "late", "absent", "holiday", "week_off"):
        count = (await db.execute(
            select(sa_func.count(Attendance.id)).where(
                Attendance.date == today,
                Attendance.status == status,
                Attendance.employee_id.in_(emp_ids_subq),
            )
        )).scalar() or 0
        if count > 0:
            status_counts[status] = count

    return {
        "org_id": org_id,
        "date": today.isoformat(),
        "total_employees": total_emp,
        "today_attendance": {
            "total": today_total,
            "by_status": status_counts,
        },
    }


@device_router.post("/{device_id}/command")
async def send_device_command(
    device_id: str,
    command: DeviceCommand,
    current_user: User = Depends(get_user_with_permissions("device:manage")),
    db: AsyncSession = Depends(get_db),
):
    return {"message": f"Command {command.command} queued for device {device_id}"}
