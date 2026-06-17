from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.device import Device, EmployeeDevice
from app.models.attendance import DeviceLog


class DeviceService:

    @staticmethod
    async def get_by_serial(db: AsyncSession, serial: str) -> Optional[Device]:
        result = await db.execute(select(Device).where(Device.serial_number == serial))
        return result.scalar_one_or_none()

    @staticmethod
    async def register(db: AsyncSession, org_id: Optional[str], serial: str, name: Optional[str] = None, model: str = "MA100", ip: Optional[str] = None) -> Device:
        existing = await DeviceService.get_by_serial(db, serial)
        if existing:
            existing.is_active = True
            if ip:
                existing.ip_address = ip
            await db.commit()
            await db.refresh(existing)
            return existing
        device = Device(
            org_id=org_id,
            serial_number=serial,
            device_name=name or serial,
            device_model=model,
            ip_address=ip,
            status="online",
            last_heartbeat=datetime.now(timezone.utc),
        )
        db.add(device)
        await db.commit()
        await db.refresh(device)
        return device

    @staticmethod
    async def update_heartbeat(db: AsyncSession, device_id: str) -> None:
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        if device:
            device.last_heartbeat = datetime.now(timezone.utc)
            device.status = "online"
            await db.commit()

    @staticmethod
    async def get_all(db: AsyncSession, org_id: str) -> list[Device]:
        result = await db.execute(
            select(Device).where(Device.org_id == org_id).order_by(Device.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_logs(db: AsyncSession, device_id: str, page: int = 1, page_size: int = 50) -> tuple[list[DeviceLog], int]:
        count_q = select(func.count(DeviceLog.id)).where(DeviceLog.device_id == device_id)
        total = (await db.execute(count_q)).scalar() or 0
        q = select(DeviceLog).where(DeviceLog.device_id == device_id).order_by(DeviceLog.punch_time.desc())
        q = q.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(q)
        return list(result.scalars().all()), total

    @staticmethod
    async def save_device_log(
        db: AsyncSession, device_id: str, zk_user_id: str, punch_time: datetime,
        punch_type: str = None, verify_mode: int = 0, raw: str = None
    ) -> DeviceLog:
        log = DeviceLog(
            device_id=device_id,
            zk_user_id=zk_user_id,
            punch_time=punch_time,
            punch_type=punch_type,
            verify_mode=verify_mode,
            raw_data=raw,
        )
        # Try to resolve employee via device mapping, then fall back to employee_code
        from app.models.employee import Employee
        emp_result = await db.execute(
            select(EmployeeDevice).where(
                EmployeeDevice.device_id == device_id,
                EmployeeDevice.zk_user_id == zk_user_id,
            )
        )
        emp_dev = emp_result.scalar_one_or_none()
        if emp_dev:
            log.employee_id = emp_dev.employee_id
        else:
            emp_result = await db.execute(
                select(Employee).where(Employee.employee_code == zk_user_id)
            )
            emp = emp_result.scalar_one_or_none()
            if emp:
                log.employee_id = emp.id
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log
