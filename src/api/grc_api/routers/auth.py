from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.deps import SESSION_COOKIE, current_principal, secured
from grc_api.auth.principal import Principal
from grc_api.config import get_settings
from grc_api.db import get_db
from grc_api.schemas.auth import DemoInfo, DemoLogin, Me, PasswordLogin
from grc_api.services import auth as svc

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _set_cookie(response: Response, token: str) -> None:
    s = get_settings()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=s.session_ttl_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=s.secure_cookies,
        path="/",
    )


@router.get("/demo", operation_id="auth_demo_info")
async def demo(db: AsyncSession = Depends(get_db)) -> DemoInfo:
    return await svc.demo_info(db)


@router.post("/demo-login", operation_id="auth_demo_login")
async def demo_login(body: DemoLogin, response: Response, db: AsyncSession = Depends(get_db)) -> Me:
    token, me = await svc.demo_login(db, body.user_id)
    _set_cookie(response, token)
    return me


@router.post("/login", operation_id="auth_login")
async def login(body: PasswordLogin, response: Response, db: AsyncSession = Depends(get_db)) -> Me:
    token, me = await svc.password_login(db, body.username, body.password)
    _set_cookie(response, token)
    return me


@router.post("/logout", operation_id="auth_logout", status_code=204)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)) -> None:
    await svc.logout(db, request.cookies.get(SESSION_COOKIE))
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me", operation_id="auth_me", **secured("people:read"))
async def me(p: Principal = Depends(current_principal), db: AsyncSession = Depends(get_db)) -> Me:
    return await svc.me(db, p)
