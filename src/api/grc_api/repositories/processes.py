"""Role assignments of process steps."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.models import StepAssignment


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
