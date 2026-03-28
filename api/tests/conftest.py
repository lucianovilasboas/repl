"""Shared fixtures for API tests."""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Dict

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from api.database import Base, get_db
from api.main import app

# In-memory SQLite for tests
_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_TestSession = async_sessionmaker(_engine, expire_on_commit=False)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSession() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def _setup_db():
    """Create tables before each test, drop after."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> Dict[str, str]:
    """Register a test user and return Authorization headers."""
    await client.post("/auth/register", json={
        "username": "testuser", "email": "test@test.com", "password": "secret123",
    })
    resp = await client.post("/auth/login", json={
        "username": "testuser", "password": "secret123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def session_id(client: AsyncClient, auth_headers: Dict[str, str]) -> str:
    """Create a calculator session and return its ID."""
    resp = await client.post("/sessions", json={"name": "test"}, headers=auth_headers)
    return resp.json()["id"]
