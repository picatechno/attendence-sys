from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import JSON, TypeDecorator
import json

from app.config import settings

_connect_args = {}
if "pgbouncer" in settings.DATABASE_URL or "pooler" in settings.DATABASE_URL:
    _connect_args["statement_cache_size"] = 0

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=20, max_overflow=10, connect_args=_connect_args)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
