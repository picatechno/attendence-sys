from typing import Optional
from datetime import date, time
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.attendance import Shift, ShiftAssignment
from app.models.holiday import Holiday, HolidayCalendar
from app.schemas.shift import ShiftCreate, ShiftAssignmentCreate, HolidayCreate


class ShiftService:

    @staticmethod
    def _parse_time(t_str: str) -> time:
        parts = t_str.split(":")
        return time(int(parts[0]), int(parts[1]))

    @staticmethod
    async def create(db: AsyncSession, org_id: str, data: ShiftCreate) -> Shift:
        shift = Shift(
            org_id=org_id,
            name=data.name,
            code=data.code,
            start_time=ShiftService._parse_time(data.start_time),
            end_time=ShiftService._parse_time(data.end_time),
            grace_late_minutes=data.grace_late_minutes,
            grace_early_minutes=data.grace_early_minutes,
            min_work_hours=data.min_work_hours,
            is_night_shift=data.is_night_shift,
            applicable_days=data.applicable_days,
        )
        if data.break_start:
            shift.break_start = ShiftService._parse_time(data.break_start)
        if data.break_end:
            shift.break_end = ShiftService._parse_time(data.break_end)
        db.add(shift)
        await db.commit()
        await db.refresh(shift)
        return shift

    @staticmethod
    async def list(db: AsyncSession, org_id: str) -> list[Shift]:
        result = await db.execute(
            select(Shift).where(Shift.org_id == org_id, Shift.is_active == True)
            .order_by(Shift.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, shift_id: str) -> Optional[Shift]:
        result = await db.execute(select(Shift).where(Shift.id == shift_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, shift_id: str, data: ShiftCreate) -> Optional[Shift]:
        shift = await ShiftService.get(db, shift_id)
        if not shift:
            return None
        shift.name = data.name
        shift.code = data.code
        shift.start_time = ShiftService._parse_time(data.start_time)
        shift.end_time = ShiftService._parse_time(data.end_time)
        shift.grace_late_minutes = data.grace_late_minutes
        shift.grace_early_minutes = data.grace_early_minutes
        shift.min_work_hours = data.min_work_hours
        shift.is_night_shift = data.is_night_shift
        shift.applicable_days = data.applicable_days
        if data.break_start:
            shift.break_start = ShiftService._parse_time(data.break_start)
        if data.break_end:
            shift.break_end = ShiftService._parse_time(data.break_end)
        await db.commit()
        await db.refresh(shift)
        return shift

    @staticmethod
    async def delete(db: AsyncSession, shift_id: str) -> bool:
        shift = await ShiftService.get(db, shift_id)
        if not shift:
            return False
        shift.is_active = False
        await db.commit()
        return True


class ShiftAssignmentService:

    @staticmethod
    async def create(db: AsyncSession, data: ShiftAssignmentCreate) -> ShiftAssignment:
        assignment = ShiftAssignment(**data.model_dump())
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def list(db: AsyncSession, employee_id: Optional[str] = None) -> list[ShiftAssignment]:
        q = select(ShiftAssignment)
        if employee_id:
            q = q.where(ShiftAssignment.employee_id == employee_id)
        q = q.order_by(ShiftAssignment.effective_from.desc())
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, assignment_id: str) -> bool:
        result = await db.execute(select(ShiftAssignment).where(ShiftAssignment.id == assignment_id))
        assignment = result.scalar_one_or_none()
        if not assignment:
            return False
        await db.delete(assignment)
        await db.commit()
        return True


class HolidayService:

    @staticmethod
    async def ensure_calendar(db: AsyncSession, org_id: str, year: int) -> HolidayCalendar:
        result = await db.execute(
            select(HolidayCalendar).where(
                HolidayCalendar.org_id == org_id,
                HolidayCalendar.year == year,
            )
        )
        cal = result.scalar_one_or_none()
        if not cal:
            cal = HolidayCalendar(org_id=org_id, year=year, name=f"{year} Calendar")
            db.add(cal)
            await db.commit()
            await db.refresh(cal)
        return cal

    @staticmethod
    async def add_holiday(db: AsyncSession, org_id: str, data: HolidayCreate) -> Holiday:
        year = int(data.date.split("-")[0])
        cal = await HolidayService.ensure_calendar(db, org_id, year)
        holiday = Holiday(
            calendar_id=cal.id,
            name=data.name,
            date=date.fromisoformat(data.date),
            is_recurring=data.is_recurring,
            type=data.type,
        )
        db.add(holiday)
        await db.commit()
        await db.refresh(holiday)
        return holiday

    @staticmethod
    async def list(db: AsyncSession, org_id: str, year: int) -> list[Holiday]:
        cal = await HolidayService.ensure_calendar(db, org_id, year)
        result = await db.execute(
            select(Holiday).where(Holiday.calendar_id == cal.id).order_by(Holiday.date)
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, holiday_id: str) -> bool:
        result = await db.execute(select(Holiday).where(Holiday.id == holiday_id))
        holiday = result.scalar_one_or_none()
        if not holiday:
            return False
        await db.delete(holiday)
        await db.commit()
        return True
