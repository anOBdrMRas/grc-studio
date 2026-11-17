"""Sign-in (demo person choice or local account), sign-out and the signed-in person."""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.deps import token_hash
from grc_api.auth.passwords import verify_password
from grc_api.auth.principal import Principal
from grc_api.config import get_settings
from grc_api.errors import ProblemError
from grc_api.models import User
from grc_api.repositories import audit, sessions
from grc_api.schemas.auth import DemoInfo, DemoPerson, Me
from grc_api.services.context import load_org

MAX_FAILED = 5


async def demo_info(db: AsyncSession) -> DemoInfo:
    if not get_settings().demo_login:
        return DemoInfo(enabled=False, persons=[])
    org = await load_org(db)
    persons = [
        DemoPerson(
            id=u.id,
            name=u.display_name,
            position_title=org.positions[u.position_id].title
            if u.position_id in org.positions
            else "",
            system_roles=list(u.system_roles),
        )
        for u in sorted(org.users.values(), key=lambda u: (u.last_name, u.first_name))
        if u.status == "active" and not u.password_hash
    ]
    return DemoInfo(enabled=True, persons=persons)


async def _open_session(db: AsyncSession, user: User) -> tuple[str, Me]:
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(24)
    expires = datetime.now(UTC) + timedelta(hours=get_settings().session_ttl_hours)
    await sessions.remove_expired(db, datetime.now(UTC))
    await sessions.create(db, token_hash(token), user.id, csrf, expires)
    await audit.record(db, user.id, "login", "user", user.id)
    await db.commit()
    return token, await me(
        db, Principal.of(user.id, user.display_name, list(user.system_roles), csrf)
    )


async def demo_login(db: AsyncSession, user_id: str) -> tuple[str, Me]:
    if not get_settings().demo_login:
        raise ProblemError("demo_login_disabled", "The demo sign-in is switched off")
    user = await db.get(User, user_id)
    # accounts with a password (e.g. the bootstrap administrator) never sign in without it
    if user is None or user.status != "active" or user.password_hash:
        raise ProblemError("login_failed", "Unknown person")
    return await _open_session(db, user)


async def password_login(db: AsyncSession, username: str, password: str) -> tuple[str, Me]:
    user = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    if (
        user is None
        or not user.password_hash
        or user.status != "active"
        or user.failed_logins >= MAX_FAILED
    ):
        raise ProblemError("login_failed", "Sign-in failed")
    if not verify_password(user.password_hash, password):
        user.failed_logins += 1
        await db.commit()
        raise ProblemError("login_failed", "Sign-in failed")
    user.failed_logins = 0
    return await _open_session(db, user)


async def logout(db: AsyncSession, token: str | None) -> None:
    if token:
        await sessions.remove(db, token_hash(token))
        await db.commit()


async def me(db: AsyncSession, p: Principal) -> Me:
    org = await load_org(db)
    u = org.users.get(p.user_id)
    pos = org.positions.get(u.position_id or "") if u else None
    return Me(
        id=p.user_id,
        name=p.name,
        system_roles=list(p.system_roles),
        permissions=sorted(p.permissions),
        csrf_token=p.csrf_token,
        position_title=pos.title if pos else "",
    )
