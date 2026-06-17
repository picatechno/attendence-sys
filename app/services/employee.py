import json
from typing import Optional
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload

from app.models.employee import Employee, Document
from app.models.organization import Department, Location
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, DepartmentCreate, LocationCreate


class EmployeeService:

    @staticmethod
    async def create(db: AsyncSession, org_id: str, data: EmployeeCreate) -> Employee:
        emp = Employee(org_id=org_id, **data.model_dump())
        db.add(emp)
        await db.commit()
        await db.refresh(emp)
        return emp

    @staticmethod
    async def get(db: AsyncSession, employee_id: str) -> Optional[Employee]:
        result = await db.execute(
            select(Employee).where(Employee.id == employee_id, Employee.is_active == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, employee_id: str, data: EmployeeUpdate) -> Optional[Employee]:
        emp = await EmployeeService.get(db, employee_id)
        if not emp:
            return None
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(emp, key, val)
        await db.commit()
        await db.refresh(emp)
        return emp

    @staticmethod
    async def delete(db: AsyncSession, employee_id: str) -> bool:
        emp = await EmployeeService.get(db, employee_id)
        if not emp:
            return False
        emp.is_active = False
        emp.date_of_exit = date.today()
        await db.commit()
        return True

    @staticmethod
    async def list(
        db: AsyncSession, org_id: str,
        page: int = 1, page_size: int = 20,
        department_id: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Employee], int]:
        query = select(Employee).where(Employee.org_id == org_id)
        count_query = select(func.count(Employee.id)).where(Employee.org_id == org_id)

        if department_id:
            query = query.where(Employee.department_id == department_id)
            count_query = count_query.where(Employee.department_id == department_id)
        if is_active is not None:
            query = query.where(Employee.is_active == is_active)
            count_query = count_query.where(Employee.is_active == is_active)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                (Employee.first_name.ilike(pattern)) |
                (Employee.last_name.ilike(pattern)) |
                (Employee.employee_code.ilike(pattern)) |
                (Employee.email.ilike(pattern))
            )
            count_query = count_query.where(
                (Employee.first_name.ilike(pattern)) |
                (Employee.last_name.ilike(pattern)) |
                (Employee.employee_code.ilike(pattern)) |
                (Employee.email.ilike(pattern))
            )

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Employee.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        employees = list(result.scalars().all())
        return employees, total


class DepartmentService:

    @staticmethod
    async def create(db: AsyncSession, org_id: str, data: DepartmentCreate) -> Department:
        dept = Department(org_id=org_id, **data.model_dump())
        db.add(dept)
        await db.commit()
        await db.refresh(dept)
        return dept

    @staticmethod
    async def list(db: AsyncSession, org_id: str) -> list[Department]:
        result = await db.execute(
            select(Department).where(Department.org_id == org_id, Department.is_active == True)
            .order_by(Department.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, dept_id: str) -> Optional[Department]:
        result = await db.execute(select(Department).where(Department.id == dept_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, dept_id: str, data: DepartmentCreate) -> Optional[Department]:
        dept = await DepartmentService.get(db, dept_id)
        if not dept:
            return None
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(dept, key, val)
        await db.commit()
        await db.refresh(dept)
        return dept

    @staticmethod
    async def delete(db: AsyncSession, dept_id: str) -> bool:
        dept = await DepartmentService.get(db, dept_id)
        if not dept:
            return False
        dept.is_active = False
        await db.commit()
        return True


class LocationService:

    @staticmethod
    async def create(db: AsyncSession, org_id: str, data: LocationCreate) -> Location:
        loc = Location(org_id=org_id, **data.model_dump())
        db.add(loc)
        await db.commit()
        await db.refresh(loc)
        return loc

    @staticmethod
    async def list(db: AsyncSession, org_id: str) -> list[Location]:
        result = await db.execute(
            select(Location).where(Location.org_id == org_id, Location.is_active == True)
            .order_by(Location.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, loc_id: str) -> Optional[Location]:
        result = await db.execute(select(Location).where(Location.id == loc_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, loc_id: str, data: LocationCreate) -> Optional[Location]:
        loc = await LocationService.get(db, loc_id)
        if not loc:
            return None
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(loc, key, val)
        await db.commit()
        await db.refresh(loc)
        return loc

    @staticmethod
    async def delete(db: AsyncSession, loc_id: str) -> bool:
        loc = await LocationService.get(db, loc_id)
        if not loc:
            return False
        loc.is_active = False
        await db.commit()
        return True
