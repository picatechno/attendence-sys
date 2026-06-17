from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.auth import User
from app.models.employee import Employee
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeListResponse,
    DepartmentCreate, DepartmentResponse, LocationCreate, LocationResponse,
)
from app.services.employee import EmployeeService, DepartmentService, LocationService
from app.core.security import get_current_user
from app.api.deps import get_user_with_permissions

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=EmployeeListResponse)
async def list_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department_id: str = Query(None),
    search: str = Query(None),
    is_active: bool = Query(None),
    current_user: User = Depends(get_user_with_permissions("employee:list")),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else None
    if not org_id:
        raise HTTPException(status_code=403, detail="No organization linked")
    employees, total = await EmployeeService.list(db, org_id, page, page_size, department_id, search, is_active)
    return {
        "items": employees,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    data: EmployeeCreate,
    current_user: User = Depends(get_user_with_permissions("employee:create")),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else None
    if not org_id:
        raise HTTPException(status_code=403, detail="No organization linked")
    emp = await EmployeeService.create(db, org_id, data)
    return emp


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    current_user: User = Depends(get_user_with_permissions("employee:read")),
    db: AsyncSession = Depends(get_db),
):
    emp = await EmployeeService.get(db, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    data: EmployeeUpdate,
    current_user: User = Depends(get_user_with_permissions("employee:update")),
    db: AsyncSession = Depends(get_db),
):
    emp = await EmployeeService.update(db, employee_id, data)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: str,
    current_user: User = Depends(get_user_with_permissions("employee:delete")),
    db: AsyncSession = Depends(get_db),
):
    deleted = await EmployeeService.delete(db, employee_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Employee not found")


# ---------- Departments ----------

dept_router = APIRouter(prefix="/departments", tags=["Departments"])


@dept_router.get("", response_model=list[DepartmentResponse])
async def list_departments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else None
    if not org_id:
        raise HTTPException(status_code=403, detail="No organization linked")
    return await DepartmentService.list(db, org_id)


@dept_router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    current_user: User = Depends(get_user_with_permissions("organization:manage")),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else None
    if not org_id:
        raise HTTPException(status_code=403, detail="No organization linked")
    return await DepartmentService.create(db, org_id, data)


@dept_router.put("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: str,
    data: DepartmentCreate,
    current_user: User = Depends(get_user_with_permissions("organization:manage")),
    db: AsyncSession = Depends(get_db),
):
    dept = await DepartmentService.update(db, dept_id, data)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@dept_router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    dept_id: str,
    current_user: User = Depends(get_user_with_permissions("organization:manage")),
    db: AsyncSession = Depends(get_db),
):
    deleted = await DepartmentService.delete(db, dept_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Department not found")


# ---------- Locations ----------

loc_router = APIRouter(prefix="/locations", tags=["Locations"])


@loc_router.get("", response_model=list[LocationResponse])
async def list_locations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else None
    if not org_id:
        raise HTTPException(status_code=403, detail="No organization linked")
    return await LocationService.list(db, org_id)


@loc_router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    data: LocationCreate,
    current_user: User = Depends(get_user_with_permissions("organization:manage")),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.employee.org_id if current_user.employee else None
    if not org_id:
        raise HTTPException(status_code=403, detail="No organization linked")
    return await LocationService.create(db, org_id, data)


@loc_router.put("/{loc_id}", response_model=LocationResponse)
async def update_location(
    loc_id: str,
    data: LocationCreate,
    current_user: User = Depends(get_user_with_permissions("organization:manage")),
    db: AsyncSession = Depends(get_db),
):
    loc = await LocationService.update(db, loc_id, data)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc


@loc_router.delete("/{loc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    loc_id: str,
    current_user: User = Depends(get_user_with_permissions("organization:manage")),
    db: AsyncSession = Depends(get_db),
):
    deleted = await LocationService.delete(db, loc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Location not found")
