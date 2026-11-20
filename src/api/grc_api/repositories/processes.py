"""Assignments of process steps: roles (RACI) and linked GRC elements."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.models import StepAssignment, StepLink


async def assignments(db: AsyncSession, process_id: str | None = None) -> list[StepAssignment]:
    stmt = select(StepAssignment).order_by(
        StepAssignment.process_id, StepAssignment.element_id, StepAssignment.id
    )
    if process_id:
        stmt = stmt.where(StepAssignment.process_id == process_id)
    return list((await db.execute(stmt)).scalars())


async def find(
    db: AsyncSession, process_id: str, element_id: str, role_id: str
) -> StepAssignment | None:
    stmt = select(StepAssignment).where(
        StepAssignment.process_id == process_id,
        StepAssignment.element_id == element_id,
        StepAssignment.role_id == role_id,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def add(db: AsyncSession, process_id: str, element_id: str, role_id: str, raci: str) -> None:
    db.add(StepAssignment(process_id=process_id, element_id=element_id, role_id=role_id, raci=raci))
    await db.flush()


async def remove(db: AsyncSession, process_id: str, element_id: str, role_id: str) -> None:
    await db.execute(
        delete(StepAssignment).where(
            StepAssignment.process_id == process_id,
            StepAssignment.element_id == element_id,
            StepAssignment.role_id == role_id,
        )
    )


# ---- risks, opportunities, controls and KPI of process steps -----------------------------------


async def links(db: AsyncSession, process_id: str | None = None) -> list[StepLink]:
    stmt = select(StepLink).order_by(StepLink.process_id, StepLink.element_id, StepLink.id)
    if process_id:
        stmt = stmt.where(StepLink.process_id == process_id)
    return list((await db.execute(stmt)).scalars())


async def links_to(db: AsyncSession, kind: str, target_id: str) -> list[StepLink]:
    stmt = select(StepLink).where(StepLink.kind == kind, StepLink.target_id == target_id)
    return list((await db.execute(stmt.order_by(StepLink.process_id, StepLink.id))).scalars())


async def links_of_kind(db: AsyncSession, kind: str) -> list[StepLink]:
    return list((await db.execute(select(StepLink).where(StepLink.kind == kind))).scalars())


async def find_link(
    db: AsyncSession, process_id: str, element_id: str, kind: str, target_id: str
) -> StepLink | None:
    stmt = select(StepLink).where(
        StepLink.process_id == process_id,
        StepLink.element_id == element_id,
        StepLink.kind == kind,
        StepLink.target_id == target_id,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def add_link(
    db: AsyncSession, process_id: str, element_id: str, kind: str, target_id: str
) -> None:
    db.add(StepLink(process_id=process_id, element_id=element_id, kind=kind, target_id=target_id))
    await db.flush()


async def remove_link(
    db: AsyncSession, process_id: str, element_id: str, kind: str, target_id: str
) -> None:
    await db.execute(
        delete(StepLink).where(
            StepLink.process_id == process_id,
            StepLink.element_id == element_id,
            StepLink.kind == kind,
            StepLink.target_id == target_id,
        )
    )


async def remove_links_to(db: AsyncSession, kind: str, target_id: str) -> None:
    """When an element is deleted its step assignments go too."""
    await db.execute(delete(StepLink).where(StepLink.kind == kind, StepLink.target_id == target_id))
