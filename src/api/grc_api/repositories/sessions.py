from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.models import User, UserSession


async def get_with_user(db: AsyncSession, token_hash: str) -> tuple[UserSession, User] | None:
    row = (
        await db.execute(
            select(UserSession, User)
            .join(User, User.id == UserSession.user_id)
            .where(UserSession.token_hash == token_hash)
        )
    ).first()
    return (row[0], row[1]) if row else None


async def create(
    db: AsyncSession, token_hash: str, user_id: str, csrf: str, expires_at: datetime
) -> None:
    db.add(
        UserSession(token_hash=token_hash, user_id=user_id, csrf_token=csrf, expires_at=expires_at)
    )
    await db.flush()


async def remove(db: AsyncSession, token_hash: str) -> None:
    await db.execute(delete(UserSession).where(UserSession.token_hash == token_hash))


async def remove_expired(db: AsyncSession, now: datetime) -> None:
    await db.execute(delete(UserSession).where(UserSession.expires_at < now))
