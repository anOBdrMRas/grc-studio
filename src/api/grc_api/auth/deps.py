"""Route dependencies: session cookie → principal, CSRF check, declared permission."""

import hashlib
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.db import get_db
from grc_api.errors import ProblemError
from grc_api.repositories import sessions as session_repo

SESSION_COOKIE = "gs_session"
UNSAFE = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def current_principal(request: Request, db: AsyncSession = Depends(get_db)) -> Principal:
    cached = getattr(request.state, "principal", None)
    if isinstance(cached, Principal):
        return cached
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise ProblemError("not_authenticated", "Please sign in")
    row = await session_repo.get_with_user(db, token_hash(token))
    if row is None or row[0].expires_at < datetime.now(UTC) or row[1].status != "active":
        raise ProblemError("not_authenticated", "Session expired")
    sess, user = row
    if request.method in UNSAFE and request.headers.get("X-CSRF-Token") != sess.csrf_token:
        raise ProblemError("csrf_failed", "CSRF token missing or wrong")
    principal = Principal.of(user.id, user.display_name, list(user.system_roles), sess.csrf_token)
    request.state.principal = principal
    return principal


def needs(permission: str) -> Callable[..., Coroutine[Any, Any, Principal]]:
    async def check(principal: Principal = Depends(current_principal)) -> Principal:
        if not principal.can(permission):
            raise ProblemError("forbidden", f"Permission {permission} required")
        return principal

    check.permission = permission  # type: ignore[attr-defined]
    return check


def secured(permission: str) -> dict[str, Any]:
    """Keyword arguments for a route: the permission check and its declaration in the contract."""
    return {
        "dependencies": [Depends(needs(permission))],
        "openapi_extra": {"x-permission": permission},
    }


# routes without a permission (checked by a test)
PUBLIC_PATHS = frozenset(
    {
        "/health/live",
        "/health/ready",
        "/api/v1/auth/login",
        "/api/v1/auth/demo",
        "/api/v1/auth/demo-login",
        "/api/v1/auth/logout",
        "/openapi.json",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
    }
)
