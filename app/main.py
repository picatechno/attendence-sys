from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, employees, zkteco, attendance, shifts, reports
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Attendance & HR System",
    description="Comprehensive attendance and HR management system with ZKTeco MA100 integration",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(employees.dept_router, prefix="/api/v1")
app.include_router(employees.loc_router, prefix="/api/v1")
app.include_router(attendance.router, prefix="/api/v1")
app.include_router(attendance.device_router, prefix="/api/v1")
app.include_router(attendance.dashboard_router, prefix="/api/v1")
app.include_router(shifts.shift_router)
app.include_router(shifts.holiday_router)
app.include_router(shifts.assignment_router)
app.include_router(reports.router)
app.include_router(zkteco.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
