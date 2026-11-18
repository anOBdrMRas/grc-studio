"""Generic access to the versioned element tables (users, roles, positions, processes)."""

from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.models import (
    Audit,
    AuditFinding,
    Control,
    Kpi,
    Mandate,
    Opportunity,
    Position,
    Process,
    Risk,
    Role,
    User,
)

# every table of versioned elements
Element = (
    User
    | Role
    | Position
    | Process
    | Risk
    | Opportunity
    | Control
    | Kpi
    | Mandate
    | Audit
    | AuditFinding
)


async def list_all[M: Element](db: AsyncSession, model: type[M]) -> list[M]:
    return list((await db.execute(select(model).order_by(model.code))).scalars())


async def get[M: Element](db: AsyncSession, model: type[M], id_: str) -> M | None:
    return await db.get(model, id_)


async def codes[M: Element](db: AsyncSession, model: type[M]) -> list[str]:
    return list((await db.execute(select(model.code))).scalars())


async def insert[M: Element](db: AsyncSession, obj: M) -> M:
    db.add(obj)
    await db.flush()
    return obj


async def update_versioned[M: Element](
    db: AsyncSession, model: type[M], id_: str, version: int, values: dict[str, Any]
) -> bool:
    """UPDATE … WHERE id = :id AND version = :v; False when the version is stale."""
    stmt = (
        update(model)
        .where(model.id == id_, model.version == version)
        .values(**values, version=model.version + 1, updated_at=func.now())
        .execution_options(synchronize_session=False)
    )
    result = await db.execute(stmt)
    return bool(result.rowcount)  # type: ignore[attr-defined]


async def remove[M: Element](db: AsyncSession, model: type[M], id_: str) -> None:
    await db.execute(delete(model).where(model.id == id_))
