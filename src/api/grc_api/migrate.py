"""Apply the migrations (called at start of the API and by the CLI)."""

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

from grc_api.config import get_settings


def alembic_config(database_url: str | None = None) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
    cfg.set_main_option("sqlalchemy.url", database_url or get_settings().database_url)
    return cfg


def upgrade(database_url: str | None = None) -> None:
    command.upgrade(alembic_config(database_url), "head")


async def upgrade_async(database_url: str | None = None) -> None:
    # alembic's env.py runs its own event loop: run it in a thread
    await asyncio.to_thread(upgrade, database_url)
