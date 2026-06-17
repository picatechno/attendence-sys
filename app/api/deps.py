from typing import AsyncGenerator, Optional, Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.auth import User, Role, UserRole
from app.core.security import get_current_user


def get_user_with_permissions(permission: str) -> Callable:
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        result = await db.execute(
            select(Role).join(UserRole).where(UserRole.user_id == current_user.id)
        )
        roles = result.scalars().all()
        for role in roles:
            perms = role.permissions or {}
            if perms.get(permission) is True or perms.get("all") is True:
                return current_user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission}")
    return permission_checker


def check_entity_access(user: User, org_id: str) -> bool:
    if not user.employee:
        return False
    return str(user.employee.org_id) == str(org_id)
