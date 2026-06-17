"""
Attendance Calculation Engine

Computes work hours, late minutes, early leave, overtime, and status
based on shift assignments and device punch logs.
"""
from datetime import datetime, time, date, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.attendance import Attendance, Shift, ShiftAssignment, DeviceLog
from app.models.holiday import HolidayCalendar, Holiday


class AttendanceCalculator:

    @staticmethod
    def time_to_seconds(t: time) -> int:
        return t.hour * 3600 + t.minute * 60 + t.second

    @staticmethod
    def parse_time(time_str: str) -> Optional[time]:
        if not time_str:
            return None
        if isinstance(time_str, time):
            return time_str
        if isinstance(time_str, str):
            parts = time_str.split(":")
            return time(int(parts[0]), int(parts[1]))
        return None

    @staticmethod
    def datetime_to_seconds(dt: datetime) -> int:
        """Get seconds since midnight for a datetime."""
        return dt.hour * 3600 + dt.minute * 60 + dt.second

    @staticmethod
    async def get_employee_shift(db: AsyncSession, employee_id: str, att_date: date) -> Optional[Shift]:
        """Find the active shift assignment for an employee on a given date."""
        day_of_week = att_date.isoweekday()  # 1=Mon...7=Sun
        result = await db.execute(
            select(ShiftAssignment).where(
                ShiftAssignment.employee_id == employee_id,
                ShiftAssignment.effective_from <= att_date,
                (ShiftAssignment.effective_to >= att_date) | (ShiftAssignment.effective_to.is_(None)),
            ).order_by(ShiftAssignment.effective_from.desc()).limit(1)
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            return None
        shift_result = await db.execute(select(Shift).where(Shift.id == assignment.shift_id))
        shift = shift_result.scalar_one_or_none()
        if not shift:
            return None
        # Check if shift applies on this day of week
        applicable = shift.applicable_days
        if isinstance(applicable, list) and len(applicable) > 0 and day_of_week not in applicable:
            return None  # not a working day for this shift
        return shift

    @staticmethod
    async def is_holiday(db: AsyncSession, org_id: str, att_date: date) -> Optional[str]:
        """Check if date is a holiday. Returns holiday name or None."""
        result = await db.execute(
            select(Holiday).join(HolidayCalendar).where(
                HolidayCalendar.org_id == org_id,
                Holiday.date == att_date,
                HolidayCalendar.is_active == True,
            ).limit(1)
        )
        holiday = result.scalar_one_or_none()
        return holiday.name if holiday else None

    @staticmethod
    async def compute_attendance(db: AsyncSession, employee_id: str, att_date: date) -> Attendance:
        """Full attendance computation for an employee on a given date."""
        # Get or create attendance record
        result = await db.execute(
            select(Attendance).where(
                Attendance.employee_id == employee_id,
                Attendance.date == att_date,
            )
        )
        att = result.scalar_one_or_none()
        if not att:
            att = Attendance(employee_id=employee_id, date=att_date)
            db.add(att)

        # Get employee's org
        from app.models.employee import Employee
        emp_result = await db.execute(select(Employee).where(Employee.id == employee_id))
        emp = emp_result.scalar_one_or_none()
        org_id = emp.org_id if emp else None

        # Check holiday
        holiday_name = None
        if org_id:
            holiday_name = await AttendanceCalculator.is_holiday(db, org_id, att_date)
        if holiday_name:
            att.status = "holiday"
            att.notes = f"Holiday: {holiday_name}"
            await db.commit()
            return att

        # Get shift
        shift = await AttendanceCalculator.get_employee_shift(db, employee_id, att_date)
        if shift:
            att.shift_id = shift.id

        # Get device logs for this date
        att_date_str = att_date.isoformat()
        log_result = await db.execute(
            select(DeviceLog).where(
                DeviceLog.employee_id == employee_id,
                func.date(DeviceLog.punch_time) == att_date_str,
            ).order_by(DeviceLog.punch_time.asc())
        )
        logs = list(log_result.scalars().all())

        if not logs:
            # No punches on a working day
            if shift:
                att.status = "absent"
            else:
                # No shift assigned and no logs - mark as week_off
                # Check if it's a weekend (Sat/Sun) or unknown
                if att_date.isoweekday() in (6, 7):
                    att.status = "week_off"
                else:
                    att.status = "absent"
            att.total_work_hours = 0
            att.net_work_hours = 0
            att.late_minutes = 0
            att.early_leave_minutes = 0
            att.is_auto_processed = True
            await db.commit()
            return att

        # Assign first and last punch
        att.clock_in = logs[0].punch_time
        att.clock_in_log_id = logs[0].id
        if len(logs) > 1:
            att.clock_out = logs[-1].punch_time
            att.clock_out_log_id = logs[-1].id

        # Calculate total work hours (from first to last punch)
        if att.clock_in and att.clock_out:
            raw_seconds = int((att.clock_out - att.clock_in).total_seconds())
            if raw_seconds < 0:
                raw_seconds += 86400  # night shift across midnight
            att.total_work_hours = max(0, raw_seconds)
        else:
            att.total_work_hours = 0

        # Calculate net work hours (subtract breaks)
        total_break = 0
        if shift and shift.break_start and shift.break_end:
            bs = AttendanceCalculator.time_to_seconds(shift.break_start)
            be = AttendanceCalculator.time_to_seconds(shift.break_end)
            total_break = be - bs if be > bs else 0
        att.total_break_hours = total_break
        att.net_work_hours = max(0, (att.total_work_hours or 0) - total_break)

        # Determine status based on shift
        att.status = "present"
        att.late_minutes = 0
        att.early_leave_minutes = 0

        if shift:
            shift_start_sec = AttendanceCalculator.time_to_seconds(shift.start_time)
            shift_end_sec = AttendanceCalculator.time_to_seconds(shift.end_time)

            if att.clock_in:
                clock_in_sec = AttendanceCalculator.datetime_to_seconds(att.clock_in)
                late_sec = clock_in_sec - (shift_start_sec + shift.grace_late_minutes * 60)
                if late_sec > 0:
                    att.late_minutes = late_sec // 60
                    att.status = "late" if att.late_minutes > 15 else "present"

            if att.clock_out:
                clock_out_sec = AttendanceCalculator.datetime_to_seconds(att.clock_out)
                early_sec = (shift_end_sec - shift.grace_early_minutes * 60) - clock_out_sec
                if early_sec > 0:
                    att.early_leave_minutes = early_sec // 60

            # Overtime
            min_sec = shift.min_work_hours or 28800
            if att.net_work_hours and att.net_work_hours > min_sec:
                att.overtime_hours = att.net_work_hours - min_sec
            else:
                att.overtime_hours = 0

            # Determine if should be absent (extremely late)
            if att.clock_in:
                from app.models.attendance import AttendancePolicy
                policy_result = await db.execute(
                    select(AttendancePolicy).where(
                        AttendancePolicy.org_id == org_id,
                        AttendancePolicy.is_active == True,
                    ).limit(1)
                )
                policy = policy_result.scalar_one_or_none()
                if policy and att.late_minutes > policy.absent_threshold // 60:
                    att.status = "absent"

        elif len(logs) == 0:
            att.status = "absent"

        att.is_auto_processed = True
        await db.commit()
        await db.refresh(att)
        return att
