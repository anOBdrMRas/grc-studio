"""Fixtures of the API tests: migrated test database, demo data, HTTP client, sign-in."""

from collections.abc import AsyncIterator, Awaitable, Callable

import httpx
import pytest
from sqlalchemy import text

from tests.conftest import TEST_DB

if not TEST_DB:
    pytest.skip("TEST_DATABASE_URL not set (PostgreSQL 16 needed)", allow_module_level=True)

from grc_api.db import Base, get_engine, get_sessionmaker
from grc_api.main import create_app
from grc_api.migrate import upgrade_async
from grc_api.seed.loader import load_demo

Login = Callable[[str], Awaitable[httpx.AsyncClient]]


@pytest.fixture(scope="session")
async def migrated() -> AsyncIterator[None]:
    async with get_engine().begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await upgrade_async(TEST_DB)
    yield
    await get_engine().dispose()


@pytest.fixture
async def demo(migrated: None) -> None:
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with get_engine().begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    async with get_sessionmaker()() as db:
        await load_demo(db)
        await db.commit()


@pytest.fixture
async def anon(demo: None) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(run_lifespan=False)), base_url="http://test"
    ) as c:
        yield c


@pytest.fixture
async def login(demo: None) -> AsyncIterator[Login]:
    """Signs a demo person in; returns a client with session cookie and CSRF header."""
    app = create_app(run_lifespan=False)
    clients: list[httpx.AsyncClient] = []

    async def sign_in(user_id: str) -> httpx.AsyncClient:
        c = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
        clients.append(c)
        r = await c.post("/api/v1/auth/demo-login", json={"user_id": user_id})
        assert r.status_code == 200, r.text
        c.headers["X-CSRF-Token"] = r.json()["csrf_token"]
        return c

    yield sign_in
    for c in clients:
        await c.aclose()
