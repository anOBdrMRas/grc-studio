"""Per-request access to the API with the signed-in user's own session cookie and CSRF token."""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import httpx
from fastapi import Request

from grc_client import ApiError, GrcClient
from grc_client.models import Me
from grc_ui.config import get_settings

SESSION_COOKIE = "gs_session"


class NotSignedIn(Exception):
    """The API answered 401: the page redirects to the sign-in."""


class CsrfFailed(Exception):
    """An unsafe request without the session's CSRF token."""


UNSAFE = frozenset({"POST", "PUT", "PATCH", "DELETE"})


@dataclass
class UiContext:
    api: GrcClient
    me: Me
    permissions: frozenset[str] = field(default_factory=frozenset)

    def can(self, permission: str) -> bool:
        return permission in self.permissions


def http_client(
    request: Request, transport: httpx.AsyncBaseTransport | None = None
) -> httpx.AsyncClient:
    cookies = (
        {SESSION_COOKIE: request.cookies[SESSION_COOKIE]}
        if SESSION_COOKIE in request.cookies
        else {}
    )
    transport = transport or getattr(request.app.state, "api_transport", None)
    s = get_settings()
    return httpx.AsyncClient(
        base_url=s.api_url, cookies=cookies, timeout=s.api_timeout_seconds, transport=transport
    )


async def anonymous_api(request: Request) -> AsyncIterator[GrcClient]:
    async with http_client(request) as http:
        yield GrcClient(http)


async def ui_context(request: Request) -> AsyncIterator[UiContext]:
    if not request.cookies.get(SESSION_COOKIE):
        # without a session cookie there is nothing to ask the API
        raise NotSignedIn
    async with http_client(request) as http:
        api = GrcClient(http)
        try:
            me = await api.auth_me()
        except ApiError as exc:
            if exc.status == 401:
                raise NotSignedIn from exc
            raise
        api.csrf_token = me["csrf_token"]
        if request.method in UNSAFE:
            sent = request.headers.get("X-CSRF-Token")
            if sent is None and "form" in request.headers.get("content-type", ""):
                sent = str((await request.form()).get("csrf_token") or "")
            if sent != me["csrf_token"]:
                raise CsrfFailed
        request.state.me = me
        yield UiContext(api=api, me=me, permissions=frozenset(me["permissions"]))


def problem_text(exc: ApiError) -> str:
    from grc_ui.texts import error_text

    return error_text(exc.code, str(exc.problem.get("detail", "")))


def field_errors(exc: ApiError) -> dict[str, str]:
    out: dict[str, str] = {}
    errors: list[dict[str, Any]] = exc.problem.get("errors", []) or []
    for e in errors:
        loc = [x for x in e.get("loc", []) if x not in ("body", "values")]
        if loc:
            out[str(loc[0])] = str(e.get("msg", ""))
    return out
