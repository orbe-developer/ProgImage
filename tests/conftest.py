"""Shared pytest fixtures.

- Each test gets a fresh in-memory SQLite database.
- The ``app.database.get_session`` dependency is overridden to that DB.
- An async HTTP client runs against the FastAPI app via ``ASGITransport``.
- ``user_a_client`` / ``user_b_client`` provide pre-authenticated clients.
"""

from __future__ import annotations

import io
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from PIL import Image as PILImage
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_session
from app.main import app


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def engine():
    """Fresh in-memory SQLite engine for each test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    """Session factory bound to the per-test engine."""
    return async_sessionmaker(bind=engine, expire_on_commit=False)


# ---------------------------------------------------------------------------
# HTTP client fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncGenerator[AsyncClient, None]:
    """Anonymous async HTTP client with get_session overridden."""

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http

    app.dependency_overrides.clear()


async def _register_and_login(http: AsyncClient, email: str, password: str) -> str:
    """Register a user then log in; return a Bearer token."""
    r = await http.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 201, r.text
    r = await http.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest_asyncio.fixture
async def user_a_token(client: AsyncClient) -> str:
    return await _register_and_login(client, "a@test.com", "longenough")


@pytest_asyncio.fixture
async def user_b_token(client: AsyncClient) -> str:
    return await _register_and_login(client, "b@test.com", "longenough")


@pytest_asyncio.fixture
def auth_headers_a(user_a_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_a_token}"}


@pytest_asyncio.fixture
def auth_headers_b(user_b_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_b_token}"}


# ---------------------------------------------------------------------------
# Image fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
def png_bytes() -> bytes:
    """A tiny valid PNG for upload tests."""
    buf = io.BytesIO()
    PILImage.new("RGB", (10, 10), color="red").save(buf, "PNG")
    return buf.getvalue()
