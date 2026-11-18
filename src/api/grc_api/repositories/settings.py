"""Settings documents (one JSON value per key, optimistic versioning)."""

from typing import Any

from sqlalchemy import func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.models import Setting


async def get(db: AsyncSession, key: str) -> Setting | None:
    return await db.get(Setting, key)


async def save(db: AsyncSession, key: str, version: int, value: dict[str, Any]) -> bool:
    """Writes `value` if the stored version is `version` (0: not stored yet); False when stale."""
    if version == 0:
        result = await db.execute(
            insert(Setting)
            .values(key=key, value=value, version=1)
            .on_conflict_do_nothing(index_elements=["key"])
        )
    else:
        result = await db.execute(
            update(Setting)
            .where(Setting.key == key, Setting.version == version)
            .values(value=value, version=Setting.version + 1, updated_at=func.now())
            .execution_options(synchronize_session=False)
        )
    return bool(result.rowcount)  # type: ignore[attr-defined]
