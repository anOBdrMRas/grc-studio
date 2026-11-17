"""App factory: security headers, language, static files, error handling."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from grc_client import ApiError
from grc_ui.config import get_settings
from grc_ui.i18n import LANGUAGES, current_language, gettext
from grc_ui.routes import auth, modules, pages, processes
from grc_ui.security import security_headers
from grc_ui.session import CsrfFailed, NotSignedIn, problem_text
from grc_ui.templating import STATIC, render, toast

log = logging.getLogger("grc_ui")


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title="GRC Studio", docs_url=None, redoc_url=None, openapi_url=None)
    app.middleware("http")(security_headers(s.public_base_url.startswith("https://")))

    @app.middleware("http")
    async def language(request: Request, call_next):  # type: ignore[no-untyped-def]
        lang = request.cookies.get("gs_lang")
        if lang not in LANGUAGES:
            accept = request.headers.get("accept-language", "")[:2].lower()
            lang = accept if accept in LANGUAGES else s.default_language
        token = current_language.set(lang)
        try:
            return await call_next(request)
        finally:
            current_language.reset(token)

    @app.exception_handler(NotSignedIn)
    async def not_signed_in(request: Request, _: NotSignedIn) -> Response:
        if request.headers.get("HX-Request") == "true":
            return Response(status_code=204, headers={"HX-Redirect": "/login"})
        return RedirectResponse("/login", status_code=303)

    @app.exception_handler(CsrfFailed)
    async def csrf_failed(request: Request, _: CsrfFailed) -> Response:
        msg = gettext("Your session has expired. Please reload the page.")
        return Response(status_code=403, headers=toast("error", msg) | {"HX-Reswap": "none"})

    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError) -> Response:
        if exc.status == 401:
            return await not_signed_in(request, NotSignedIn())
        if request.headers.get("HX-Request") == "true":
            return Response(
                status_code=exc.status,
                headers=toast("error", problem_text(exc)) | {"HX-Reswap": "none"},
            )
        return render(request, "error.html", None, status=exc.status, message=problem_text(exc))

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception) -> Response:
        log.exception("unexpected error")
        if request.headers.get("HX-Request") == "true":
            return Response(
                status_code=500,
                headers=toast("error", gettext("Something went wrong.")) | {"HX-Reswap": "none"},
            )
        return HTMLResponse(
            render(
                request, "error.html", None, status=500, message=gettext("Something went wrong.")
            ).body,
            status_code=500,
        )

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict[str, str]:
        """Liveness of the interface container (the API has its own /health/*)."""
        return {"status": "ok"}

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    for r in (auth.router, pages.router, processes.router, modules.router):
        app.include_router(r)
    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("grc_ui.main:app", host="0.0.0.0", port=8001, workers=1)  # noqa: S104 - runs inside the container
