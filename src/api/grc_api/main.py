"""App factory and lifespan: migrations first, then built-ins, then serve."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from grc_api import __version__
from grc_api.config import get_settings
from grc_api.db import get_sessionmaker
from grc_api.errors import install
from grc_api.migrate import upgrade_async
from grc_api.routers import (
    assistant,
    audits,
    auth,
    content,
    grc,
    health,
    instructions,
    mandates,
    meta,
    org,
    processes,
    users,
)

log = logging.getLogger("grc_api")


async def _bootstrap() -> None:
    """Built-ins are reconciled at start: the first administrator and (optionally) the demo data."""
    from grc_api.auth.passwords import hash_password
    from grc_api.models import User
    from grc_api.seed.loader import is_empty, load_demo

    s = get_settings()
    async with get_sessionmaker()() as db:
        if s.seed_demo_on_empty and await is_empty(db):
            log.info("loading demo data: %s", await load_demo(db))
        if s.bootstrap_admin_user and s.bootstrap_admin_password:
            from sqlalchemy import select

            existing = (
                await db.execute(select(User).where(User.username == s.bootstrap_admin_user))
            ).scalar_one_or_none()
            if existing is None:
                db.add(
                    User(
                        id="U-ADMIN",
                        code="U-ADMIN",
                        last_name="Administrator",
                        display_name="Administrator",
                        username=s.bootstrap_admin_user,
                        password_hash=hash_password(s.bootstrap_admin_password),
                        system_roles=["admin"],
                    )
                )
                await db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await upgrade_async()
    await _bootstrap()
    yield


def create_app(*, run_lifespan: bool = True) -> FastAPI:
    app = FastAPI(
        title="GRC Studio API",
        version=__version__,
        description="All rules and all data access of GRC Studio. Every operation declares its permission (x-permission).",
        lifespan=lifespan if run_lifespan else None,
        docs_url="/docs",
    )
    install(app)
    for r in (
        health.router,
        auth.router,
        meta.router,
        users.router,
        org.router,
        processes.router,
        instructions.router,
        grc.router,
        mandates.router,
        audits.router,
        content.router,
        assistant.router,
    ):
        app.include_router(r)
    return app


app = create_app()
