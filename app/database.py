"""Async SQLAlchemy engine, session factory, and declarative base.

The ``get_session`` dependency yields an ``AsyncSession`` scoped to the
lifetime of a single request. All models inherit from ``Base`` so that
``Base.metadata`` sees every table at startup (used by the dev lifespan
hook and by Alembic for autogenerate).
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Common declarative base for all ORM models."""


engine = create_async_engine(settings.database_url, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped async session."""
    async with AsyncSessionLocal() as session:
        yield session
