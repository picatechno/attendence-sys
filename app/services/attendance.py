from typing import Optional
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.attendance import Attendance, DeviceLog
from app.schemas.attendance import AttendanceUpdate


class AttendanceService:

    @staticmethod
    async def get_or_create(db: AsyncSession, employee_id: str, att_date: date) -> Attendance:
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
            await db.commit()
            await db.refresh(att)
        return att

    @staticmethod
    async def process_device_logs(db: AsyncSession, employee_id: str, att_date: date) -> Attendance:
        """Basic processing: take first punch as clock-in, last as clock-out."""
        punch_start = datetime.combine(att_date, time.min, tzinfo=timezone.utc)
        punch_end = datetime.combine(att_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
        result = await db.execute(
            select(DeviceLog).where(
                DeviceLog.employee_id == employee_id,
                DeviceLog.punch_time >= punch_start,
                DeviceLog.punch_time < punch_end,
            ).order_by(DeviceLog.punch_time.asc())
        )
        logs = list(result.scalars().all())
        if not logs:
            att = await AttendanceService.get_or_create(db, employee_id, att_date)
            att.status = "absent"
            await db.commit()
            return att

        att = await AttendanceService.get_or_create(db, employee_id, att_date)
        att.clock_in = logs[0].punch_time
        att.clock_in_log_id = logs[0].id

        if len(logs) > 1:
            att.clock_out = logs[-1].punch_time
            att.clock_out_log_id = logs[-1].id

        # Calculate work hours (in seconds)
        if att.clock_in and att.clock_out:
            raw_seconds = int((att.clock_out - att.clock_in).total_seconds())
            if raw_seconds < 0:
                raw_seconds += 86400  # night shift across midnight
            att.total_work_hours = raw_seconds
            att.net_work_hours = raw_seconds
            att.status = "present"
        else:
            att.status = "present"
            att.total_work_hours = 0
            att.net_work_hours = 0

        att.is_auto_processed = True
        await db.commit()
        await db.refresh(att)
        return att

    @staticmethod
    async def update(db: AsyncSession, att_id: str, data: AttendanceUpdate) -> Optional[Attendance]:
        result = await db.execute(select(Attendance).where(Attendance.id == att_id))
        att = result.scalar_one_or_none()
        if not att:
            return None
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(att, key, val)
        await db.commit()
        await db.refresh(att)
        return att

    @staticmethod
    async def list(
        db: AsyncSession,
        org_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Attendance], int]:
        from app.models.employee import Employee
        conditions = []
        if org_id:
            conditions.append(Attendance.employee_id.in_(
                select(Employee.id).where(Employee.org_id == org_id)
            ))
        if employee_id:
            conditions.append(Attendance.employee_id == employee_id)
        if date_from:
            conditions.append(Attendance.date >= date_from)
        if date_to:
            conditions.append(Attendance.date <= date_to)
        if status:
            conditions.append(Attendance.status == status)

        count_q = select(func.count(Attendance.id))
        query = select(Attendance)
        if conditions:
            count_q = count_q.where(and_(*conditions))
            query = query.where(and_(*conditions))

        total = (await db.execute(count_q)).scalar() or 0
        query = query.order_by(Attendance.date.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def get_by_date(db: AsyncSession, employee_id: str, att_date: date) -> Optional[Attendance]:
        result = await db.execute(
            select(Attendance).where(
                Attendance.employee_id == employee_id,
                Attendance.date == att_date,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def reprocess_range(db: AsyncSession, employee_id: str, from_date: date, to_date: date) -> int:
        """Reprocess attendance for a date range."""
        count = 0
        current = from_date
        while current <= to_date:
            await AttendanceService.process_device_logs(db, employee_id, current)
            count += 1
            from datetime import timedelta
            current += timedelta(days=1)
        return count
