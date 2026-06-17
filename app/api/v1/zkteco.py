"""
ZKTeco PUSH Protocol Endpoints

These endpoints are called by ZKTeco MA100 devices via HTTP.
They are intentionally unauthenticated (device uses serial number for identity).

Endpoints:
  GET  /iclock/cdata       - Device handshake
  POST /iclock/cdata       - Receive attendance/biometric data
  GET  /iclock/getrequest  - Heartbeat / command polling
  GET  /iclock/devicecmd   - Server commands to device
  POST /iclock/devicecmd   - Device command response
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.services.device import DeviceService
from app.services.zkteco import ZKTecoPUSHHandler, build_handshake_response
from app.models.organization import Organization

logger = logging.getLogger("zkteco")
router = APIRouter(prefix="/iclock", tags=["ZKTeco PUSH"])


@router.get("/cdata")
async def device_handshake(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Device handshake endpoint. Called when device first connects."""
    sn = request.query_params.get("SN", "")
    options = request.query_params.get("options", "")
    logger.info(f"Device handshake: SN={sn}, options={options}")

    if not sn:
        return Response("ERROR: No serial number", media_type="text/plain")

    # Use first available org for auto-registration
    org_result = await db.execute(select(Organization).limit(1))
    org = org_result.scalar_one_or_none()
    org_id = org.id if org else None

    await DeviceService.register(
        db, org_id=org_id, serial=sn, ip=request.client.host if request.client else None
    )

    response_text = build_handshake_response(sn)
    logger.info(f"Handshake response for {sn}: stamps configured")
    return Response(response_text, media_type="text/plain")


@router.post("/cdata")
async def receive_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive attendance logs, biometric data, or options from device."""
    table = request.query_params.get("table", "")
    body = (await request.body()).decode("utf-8", errors="replace")
    sn = request.query_params.get("SN", "")

    logger.info(f"Data received: table={table}, SN={sn}, {len(body)} bytes")

    if not sn:
        return Response("ERROR: No serial number", media_type="text/plain")

    device = await DeviceService.get_by_serial(db, sn)
    if not device:
        return Response("ERROR: Unknown device", media_type="text/plain")

    await DeviceService.update_heartbeat(db, device.id)

    if table == "ATTLOG":
        records = ZKTecoPUSHHandler.parse_attlog_payload(body)
        logger.info(f"Parsed {len(records)} attendance records from {sn}")
        for rec in records:
            try:
                punch_time = datetime.strptime(rec["timestamp_str"], "%Y-%m-%d %H:%M:%S")
                punch_time = punch_time.replace(tzinfo=timezone.utc)
            except ValueError:
                logger.warning(f"Invalid timestamp: {rec['timestamp_str']}")
                continue
            await DeviceService.save_device_log(
                db, device.id, rec["zk_user_id"], punch_time,
                verify_mode=int(rec["verify_mode"]) if rec.get("verify_mode") else 0,
                raw=str(rec),
            )

    elif table == "BIODATA":
        records = ZKTecoPUSHHandler.parse_biodata_payload(body)
        logger.info(f"Received {len(records)} biometric records from {sn}")

    elif table == "options":
        logger.info(f"Device {sn} options: {body[:200]}")

    else:
        logger.info(f"Unknown table '{table}' from {sn}: {body[:100]}")

    return Response("OK", media_type="text/plain")


@router.get("/getrequest")
async def heartbeat(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Device heartbeat. Server can return commands here."""
    sn = request.query_params.get("SN", "")
    if sn:
        device = await DeviceService.get_by_serial(db, sn)
        if device:
            await DeviceService.update_heartbeat(db, device.id)
    return Response("", media_type="text/plain")


@router.get("/devicecmd")
async def get_commands(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Server -> Device commands. Return pending commands."""
    sn = request.query_params.get("SN", "")
    return Response("", media_type="text/plain")


@router.post("/devicecmd")
async def command_response(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Device response to commands."""
    body = (await request.body()).decode("utf-8", errors="replace")
    logger.info(f"Device command response: {body[:200]}")
    return Response("OK", media_type="text/plain")


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify the iclock routes are active."""
    return {"status": "ZKTeco PUSH listener is active"}
