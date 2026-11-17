"""Sign-in, sessions and CSRF."""

import httpx

from tests.api.conftest import Login


async def test_health(anon: httpx.AsyncClient) -> None:
    assert (await anon.get("/health/live")).status_code == 200
    assert (await anon.get("/health/ready")).status_code == 200


async def test_requires_session(anon: httpx.AsyncClient) -> None:
    r = await anon.get("/api/v1/roles")
    assert r.status_code == 401
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["code"] == "not_authenticated"


async def test_demo_persons_listed(anon: httpx.AsyncClient) -> None:
    body = (await anon.get("/api/v1/auth/demo")).json()
    assert body["enabled"] is True
    assert len(body["persons"]) >= 20


async def test_unknown_person_cannot_sign_in(anon: httpx.AsyncClient) -> None:
    r = await anon.post("/api/v1/auth/demo-login", json={"user_id": "U-999"})
    assert r.status_code in (401, 404)


async def test_cookie_is_http_only(anon: httpx.AsyncClient) -> None:
    r = await anon.post("/api/v1/auth/demo-login", json={"user_id": "U-002"})
    cookie = r.headers["set-cookie"].lower()
    assert "gs_session=" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie or "samesite=strict" in cookie


async def test_csrf_required_for_changes(login: Login) -> None:
    c = await login("U-013")
    token = c.headers.pop("X-CSRF-Token")
    r = await c.post("/api/v1/roles", json={"title": "Neu"})
    assert r.status_code == 403
    assert r.json()["code"] == "csrf_failed"
    c.headers["X-CSRF-Token"] = token
    assert (await c.post("/api/v1/roles", json={"title": "Neu"})).status_code == 201


async def test_logout_ends_session(login: Login) -> None:
    c = await login("U-002")
    assert (await c.get("/api/v1/auth/me")).status_code == 200
    assert (await c.post("/api/v1/auth/logout")).status_code == 204
    assert (await c.get("/api/v1/auth/me")).status_code == 401


async def test_password_accounts_are_not_demo_persons(anon: httpx.AsyncClient) -> None:
    from grc_api.auth.passwords import hash_password
    from grc_api.db import get_sessionmaker
    from grc_api.models import User

    async with get_sessionmaker()() as db:
        db.add(
            User(
                id="U-PW",
                code="U-PW",
                last_name="Konto",
                display_name="Konto",
                username="konto",
                password_hash=hash_password("Geheim-123!"),
            )
        )
        await db.commit()
    persons = (await anon.get("/api/v1/auth/demo")).json()["persons"]
    assert "U-PW" not in [p["id"] for p in persons]
    assert (await anon.post("/api/v1/auth/demo-login", json={"user_id": "U-PW"})).status_code == 401
    assert (
        await anon.post("/api/v1/auth/login", json={"username": "konto", "password": "falsch"})
    ).status_code == 401
    assert (
        await anon.post("/api/v1/auth/login", json={"username": "konto", "password": "Geheim-123!"})
    ).status_code == 200
