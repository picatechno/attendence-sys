"""Report generation and export endpoints"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.auth import User
from app.api.deps import get_user_with_permissions
from app.services.reports import ReportService

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


def _format_response(data: list[dict], fmt: str, title: str) -> Response:
    if fmt == "xlsx":
        xlsx_bytes = ReportService.generate_xlsx(data, title)
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{title.lower().replace(" ", "_")}.xlsx"'},
        )
    elif fmt == "pdf":
        pdf_bytes = ReportService.generate_pdf(data, title)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{title.lower().replace(" ", "_")}.pdf"'},
        )
    return data


@router.get("/daily")
async def daily_report(
    report_date: date = Query(...),
    fmt: Optional[str] = Query(None, pattern="^(json|xlsx|pdf)$"),
    current_user: User = Depends(get_user_with_permissions("attendance:read_all")),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else ""
    data = await ReportService.get_daily_report(db, org_id, report_date)
    return _format_response(data, fmt or "json", f"Daily Report {report_date}")


@router.get("/monthly")
async def monthly_report(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    employee_id: Optional[str] = Query(None),
    fmt: Optional[str] = Query(None, pattern="^(json|xlsx|pdf)$"),
    current_user: User = Depends(get_user_with_permissions("attendance:read_all")),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else ""
    data = await ReportService.get_monthly_summary(db, org_id, year, month, employee_id)
    return _format_response(data, fmt or "json", f"Monthly Report {year}-{month:02d}")


@router.get("/employee")
async def employee_report(
    employee_id: str = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    fmt: Optional[str] = Query(None, pattern="^(json|xlsx|pdf)$"),
    current_user: User = Depends(get_user_with_permissions("attendance:read_all")),
    db: AsyncSession = Depends(get_db),
):
    data = await ReportService.get_employee_report(db, employee_id, date_from, date_to)
    return _format_response(data, fmt or "json", f"Employee Report {employee_id}")
