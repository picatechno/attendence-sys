import asyncio
import uuid
from datetime import date

from app.database import engine, async_session_factory, Base
import app.models  # noqa: F401 - register all models
from app.models.organization import Organization
from app.models.auth import Role, User, UserRole
from app.core.security import hash_password


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        from sqlalchemy import text
        result = await db.execute(text("SELECT COUNT(*) FROM organizations"))
        count = result.scalar()
        if count == 0:
            org = Organization(
                name="Default Organization",
                code="DEFAULT",
            )
            db.add(org)
            await db.flush()

            admin_role = Role(
                org_id=org.id,
                name="super_admin",
                description="Super Administrator",
                permissions={
                    "employee:create": True, "employee:read": True, "employee:update": True,
                    "employee:delete": True, "employee:list": True,
                    "attendance:read_own": True, "attendance:read_all": True,
                    "attendance:manual_edit": True, "attendance:export": True,
                    "attendance:manage": True,
                    "leave:apply": True, "leave:approve": True,
                    "leave:read_own": True, "leave:read_all": True,
                    "device:manage": True, "device:view_logs": True,
                    "report:view": True, "report:export": True,
                    "organization:manage": True, "user:manage": True,
                    "audit:view": True, "all": True,
                },
                is_system=True,
            )
            hr_role = Role(
                org_id=org.id,
                name="hr_manager",
                description="HR Manager",
                permissions={
                    "employee:create": True, "employee:read": True, "employee:update": True,
                    "employee:delete": False, "employee:list": True,
                    "attendance:read_own": True, "attendance:read_all": True,
                    "attendance:manual_edit": True, "attendance:export": True,
                    "attendance:manage": True,
                    "leave:apply": True, "leave:approve": True,
                    "leave:read_own": True, "leave:read_all": True,
                    "device:manage": False, "device:view_logs": True,
                    "report:view": True, "report:export": True,
                    "organization:manage": False, "user:manage": True,
                    "audit:view": True,
                },
                is_system=True,
            )
            emp_role = Role(
                org_id=org.id,
                name="employee",
                description="Employee",
                permissions={
                    "employee:create": False, "employee:read": True, "employee:update": False,
                    "employee:delete": False, "employee:list": False,
                    "attendance:read_own": True, "attendance:read_all": False,
                    "attendance:manual_edit": False, "attendance:export": False,
                    "leave:apply": True, "leave:approve": False,
                    "leave:read_own": True, "leave:read_all": False,
                    "device:manage": False, "device:view_logs": False,
                    "report:view": False, "report:export": False,
                    "organization:manage": False, "user:manage": False,
                    "audit:view": False,
                },
                is_system=True,
            )
            db.add_all([admin_role, hr_role, emp_role])
            await db.flush()

            from app.models.employee import Employee
            admin_emp = Employee(
                org_id=org.id,
                employee_code="ADMIN001",
                first_name="System",
                last_name="Administrator",
                email="admin@attendence.com",
                date_of_joining=date.today(),
            )
            db.add(admin_emp)
            await db.flush()

            admin_user = User(
                employee_id=admin_emp.id,
                email="admin@attendence.com",
                password_hash=hash_password("Admin@123456"),
                is_active=True,
            )
            db.add(admin_user)
            await db.flush()

            db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
            await db.commit()

            print(f"Organization: {org.id}")
            print(f"Admin user: admin@attendence.com / Admin@123456")
        else:
            print("Database already seeded.")

    await engine.dispose()
    print("Database initialized successfully.")


if __name__ == "__main__":
    asyncio.run(init_db())
