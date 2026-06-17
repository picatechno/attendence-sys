from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.auth import User, Role, UserRole
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token


class AuthService:

    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            user.failed_attempts += 1
            if user.failed_attempts >= 10:
                user.is_locked = True
            await db.commit()
            return None
        user.failed_attempts = 0
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        return user

    @staticmethod
    def generate_tokens(user: User) -> dict:
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    @staticmethod
    def refresh_access_token(refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
        new_access = create_access_token({"sub": user_id})
        new_refresh = create_refresh_token({"sub": user_id})
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}

    @staticmethod
    async def get_user_roles(db: AsyncSession, user_id: UUID) -> list[Role]:
        result = await db.execute(
            select(Role).join(UserRole).where(UserRole.user_id == user_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_user(db: AsyncSession, email: str, password: str, employee_id: Optional[UUID] = None, role_ids: Optional[list[UUID]] = None) -> User:
        user = User(
            email=email,
            password_hash=hash_password(password),
            employee_id=employee_id,
        )
        db.add(user)
        await db.flush()
        if role_ids:
            for rid in role_ids:
                db.add(UserRole(user_id=user.id, role_id=rid))
        await db.commit()
        await db.refresh(user)
        return user
