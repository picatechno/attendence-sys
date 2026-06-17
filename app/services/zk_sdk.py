import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from app.models.device import Device
from app.models.attendance import DeviceLog
from app.services.device import DeviceService

logger = logging.getLogger("zk_sdk")

async def pull_attendance_from_device(db: AsyncSession, device_ip: str, device_port: int = 4370) -> list[dict]:
    """Connect to ZKTeco device via SDK (port 4370) and pull attendance logs."""
    from zk import ZK

    zk = ZK(device_ip, port=device_port, timeout=30)
    conn = None
    inserted = []

    try:
        conn = zk.connect()
        conn.disable_device()
        logger.info(f"Connected to device {device_ip}:{device_port}")

        attendances = conn.get_attendance()
        logger.info(f"Fetched {len(attendances)} attendance records")

        # Find or register device
        result = await db.execute(
            select(Device).where(Device.ip_address == device_ip).limit(1)
        )
        device = result.scalar_one_or_none()

        if not device:
            from sqlalchemy import text
            org_result = await db.execute(text("SELECT id FROM organizations LIMIT 1"))
            org_row = org_result.first()
            device = await DeviceService.register(
                db, org_id=org_row[0] if org_row else None,
                serial=f"SDK-{device_ip}", ip=device_ip,
            )

        # Build batch insert values (skip employee resolution for speed)
        values = []
        for att in attendances:
            try:
                punch_time = att.timestamp
                if isinstance(punch_time, str):
                    punch_time = datetime.strptime(punch_time, "%Y-%m-%d %H:%M:%S")
                if punch_time.tzinfo is None:
                    punch_time = punch_time.replace(tzinfo=timezone.utc)

                values.append({
                    "device_id": device.id,
                    "zk_user_id": str(att.user_id),
                    "employee_id": None,
                    "punch_time": punch_time,
                    "verify_mode": int(att.status) if hasattr(att, 'status') and att.status is not None else 0,
                    "raw_data": {"user_id": str(att.user_id), "timestamp": str(att.timestamp)},
                })
            except Exception as e:
                logger.warning(f"Record error (user={att.user_id}): {e}")

        if values:
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            stmt = pg_insert(DeviceLog).values(values).on_conflict_do_nothing(
                constraint="uq_device_log_punch"
            )
            await db.execute(stmt)
            await db.commit()
            inserted = values
            logger.info(f"Inserted {len(values)} records via batch insert")

        conn.enable_device()

    except Exception as e:
        logger.error(f"ZKTeco SDK error for {device_ip}:{device_port}: {e}", exc_info=True)
    finally:
        try:
            if conn:
                conn.disconnect()
        except Exception:
            pass

    return inserted
