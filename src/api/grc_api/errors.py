"""Errors are documents: application/problem+json (RFC 9457) with a stable code."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

PROBLEM = "application/problem+json"
log = logging.getLogger("grc_api")

# stable codes (the interface maps them to translated messages)
CODES = {
    "not_authenticated": 401,
    "csrf_failed": 403,
    "forbidden": 403,
    "not_found": 404,
    "version_conflict": 412,
    "version_required": 428,
    "conflict": 409,
    "invalid": 422,
    "login_failed": 401,
    "demo_login_disabled": 403,
    "four_eyes": 409,
    "workflow_state": 409,
}


class ProblemError(Exception):
    def __init__(
        self, code: str, detail: str = "", status: int | None = None, **extra: Any
    ) -> None:
        super().__init__(detail or code)
        self.code = code
        self.status = status or CODES.get(code, 400)
        self.detail = detail or code
        self.extra = extra


def problem(status: int, code: str, detail: str, **extra: Any) -> JSONResponse:
    body = {
        "type": f"about:blank#{code}",
        "title": code.replace("_", " "),
        "status": status,
        "code": code,
        "detail": detail,
        **extra,
    }
    return JSONResponse(body, status_code=status, media_type=PROBLEM)


def install(app: FastAPI) -> None:
    @app.exception_handler(ProblemError)
    async def _problem(_: Request, exc: ProblemError) -> JSONResponse:
        return problem(exc.status, exc.code, exc.detail, **exc.extra)

    @app.exception_handler(RequestValidationError)
    async def _invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"loc": [str(x) for x in e.get("loc", [])], "msg": str(e.get("msg", ""))}
            for e in exc.errors()
        ]
        return problem(422, "invalid", "Invalid request", errors=errors)

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
        # the traceback goes to the log, the client gets a stable code without details
        log.error("unexpected error on %s %s", request.method, request.url.path, exc_info=exc)
        return problem(500, "internal", "Unexpected error")
