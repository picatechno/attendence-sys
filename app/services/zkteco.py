"""ZKTeco PUSH Protocol Handler

Implements the device-initiated HTTP protocol used by ZKTeco MA100 devices.

Protocol Flow:
1. Device handshake: GET /iclock/cdata?SN=XXX&options=all
2. Server responds with config stamps
3. Data push: POST /iclock/cdata (attendance logs, biometric data)
4. Heartbeat: GET /iclock/getrequest?SN=XXX
5. Commands: GET /iclock/devicecmd (server -> device)
"""
import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession


def parse_cdata_line(line: str) -> Optional[dict]:
    """Parse a single attendance log line from device.

    Format: <ZKUserID>\t<YYYY-MM-DD HH:MM:SS>\t<verifyMode>\t<workCode>
    Example: 1001  2026-06-17 09:01:33  1  0
    """
    parts = line.strip().split("\t")
    if len(parts) < 2:
        return None
    record = {
        "zk_user_id": parts[0].strip(),
        "timestamp_str": parts[1].strip(),
    }
    if len(parts) >= 3:
        record["verify_mode"] = int(parts[2].strip())
    else:
        record["verify_mode"] = 0
    if len(parts) >= 4:
        record["work_code"] = parts[3].strip()
    else:
        record["work_code"] = "0"
    return record


def build_handshake_response(serial: str, attlog_stamp: str = "0") -> str:
    """Build the handshake response for the device."""
    lines = [
        f"GET OPTION FROM: {serial}",
        f"ATTLOGStamp={attlog_stamp}",
        "OPERLOGStamp=0",
        "ATTPHOTOStamp=0",
        "Realtime=1",
        "ServerVer=3.0.1",
        "TransFlag=111111111111",
    ]
    return "\n".join(lines)


def build_device_cmd_response(commands: list[str]) -> str:
    """Build command response for device heartbeat."""
    if not commands:
        return ""
    return "\n".join(commands)


def determine_punch_type(punch_time: datetime, existing_logs: list) -> str:
    """Basic punch type determination - will be enhanced in Phase 4."""
    if not existing_logs:
        return "0"  # check-in
    # Simple toggle: if last punch was check-in, this is check-out
    return "1"  # check-out


class ZKTecoPUSHHandler:
    """Handles the ZKTeco PUSH protocol communication."""

    @staticmethod
    def parse_table_param(query_params: dict) -> str:
        """Extract table parameter from query string."""
        return query_params.get("table", "")

    @staticmethod
    def parse_attlog_payload(body: str) -> list[dict]:
        """Parse attendance log payload from POST body.

        Body format: one record per line, tab-separated.
        """
        records = []
        for line in body.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            record = parse_cdata_line(line)
            if record:
                records.append(record)
        return records

    @staticmethod
    def parse_biodata_payload(body: str) -> list[dict]:
        """Parse biometric data payload.

        Format: <ZKUserID>\t<fingerId>\t<template> (base64)
        """
        records = []
        for line in body.strip().split("\n"):
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue
            records.append({
                "zk_user_id": parts[0].strip(),
                "finger_id": parts[1].strip(),
                "template": parts[2].strip(),
            })
        return records
