"""Roles of positions."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.models import PositionRole


async def all_position_roles(db: AsyncSession) -> list[PositionRole]:
    return list(
        (
            await db.execute(
                select(PositionRole).order_by(PositionRole.position_id, PositionRole.sort)
            )
        ).scalars()
    )


async def replace_position_roles(
    db: AsyncSession, position_id: str, roles: list[tuple[str, str]]
) -> None:
    await db.execute(delete(PositionRole).where(PositionRole.position_id == position_id))
    for i, (role_id, comment) in enumerate(roles):
        db.add(PositionRole(position_id=position_id, role_id=role_id, comment=comment, sort=i))
    await db.flush()
