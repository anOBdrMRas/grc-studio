"""Sign-in page (demo person choice, deviation A4; password form when the demo sign-in is off) and sign-out."""

import contextlib

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from grc_client import ApiError, GrcClient
from grc_ui.i18n import LANGUAGES, N_
from grc_ui.session import SESSION_COOKIE, anonymous_api, problem_text
from grc_ui.templating import render

router = APIRouter()

# tiles of the sign-in page: one person per kind of user
PERSONAS = [
    ("U-006", N_("Employee"), N_("Sees the process landscape and what is assigned to him.")),
    (
        "U-016",
        N_("Manager"),
        N_("Supervisor and therefore owner of the position Director Export Control & Customs."),
    ),
    ("U-013", N_("I&A team"), N_("Gives the quality approval and manages the GRC modules.")),
    ("U-001", N_("Administrator"), N_("Creates new elements and maintains users.")),
]


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request, api: GrcClient = Depends(anonymous_api), error: str = ""
) -> Response:
    info = await api.auth_demo_info()
    persons = {p["id"]: p for p in info["persons"]}
    tiles = [(persons[i], kind, text) for i, kind, text in PERSONAS if i in persons]
    return render(
        request,
        "login.html",
        None,
        demo=info["enabled"],
        tiles=tiles,
        persons=info["persons"],
        error=error,
    )


def _relay_cookie(api: GrcClient, response: Response) -> None:
    """The API sets the session cookie; the interface hands it on to the browser (one public address)."""
    r = api.last_response
    if r is not None:
        for value in r.headers.get_list("set-cookie"):
            response.headers.append("set-cookie", value)


@router.post("/login/demo")
async def login_demo(request: Request, api: GrcClient = Depends(anonymous_api)) -> Response:
    form = await request.form()
    try:
        await api.auth_demo_login({"user_id": str(form.get("user_id") or "")})
    except ApiError as exc:
        return await login_page(request, api, problem_text(exc))
    response = RedirectResponse("/", status_code=303)
    _relay_cookie(api, response)
    return response


@router.post("/login/password")
async def login_password(request: Request, api: GrcClient = Depends(anonymous_api)) -> Response:
    form = await request.form()
    try:
        await api.auth_login(
            {
                "username": str(form.get("username") or ""),
                "password": str(form.get("password") or ""),
            }
        )
    except ApiError as exc:
        return await login_page(request, api, problem_text(exc))
    response = RedirectResponse("/", status_code=303)
    _relay_cookie(api, response)
    return response


@router.post("/logout")
async def logout(request: Request, api: GrcClient = Depends(anonymous_api)) -> Response:
    with contextlib.suppress(ApiError):
        await api.auth_logout()
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.post("/language")
async def language(request: Request) -> Response:
    form = await request.form()
    lang = str(form.get("lang") or "de")
    response = RedirectResponse(str(form.get("next") or "/"), status_code=303)
    if lang in LANGUAGES:
        response.set_cookie("gs_lang", lang, max_age=365 * 86400, samesite="lax", path="/")
    return response
