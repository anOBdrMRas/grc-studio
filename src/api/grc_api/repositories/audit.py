"""Audit log and workflow log."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.models import AuditEntry, WorkflowEntry


async def record(
    db: AsyncSession,
    actor_id: str,
    action: str,
    kind: str,
    entity_id: str,
    changes: list[dict[str, Any]] | None = None,
    note: str = "",
    vars_: dict[str, str] | None = None,
) -> None:
    db.add(
        AuditEntry(
            actor_id=actor_id,
            action=action,
            kind=kind,
            entity_id=entity_id,
            changes=changes or [],
            note=note,
            vars=vars_ or {},
        )
    )
    await db.flush()


async def history(db: AsyncSession, kind: str, entity_id: str) -> list[AuditEntry]:
    stmt = (
        select(AuditEntry)
        .where(AuditEntry.kind == kind, AuditEntry.entity_id == entity_id)
        .order_by(AuditEntry.id)
    )
    return list((await db.execute(stmt)).scalars())


async def add_workflow(
    db: AsyncSession,
    kind: str,
    entity_id: str,
    step: str,
    by_user_id: str,
    comment: str,
    status: str,
) -> None:
    db.add(
        WorkflowEntry(
            kind=kind,
            entity_id=entity_id,
            step=step,
            by_user_id=by_user_id,
            comment=comment,
            status=status,
        )
    )
    await db.flush()


async def workflow(
    db: AsyncSession, kind: str, entity_id: str | None = None
) -> list[WorkflowEntry]:
    stmt = select(WorkflowEntry).where(WorkflowEntry.kind == kind)
    if entity_id:
        stmt = stmt.where(WorkflowEntry.entity_id == entity_id)
    return list((await db.execute(stmt.order_by(WorkflowEntry.id))).scalars())
