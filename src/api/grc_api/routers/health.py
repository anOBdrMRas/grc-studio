from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.db import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", operation_id="health_live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", operation_id="health_ready")
async def ready(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(text("select 1"))
    return {"status": "ok"}
