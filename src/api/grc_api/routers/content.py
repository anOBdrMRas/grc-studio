from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.deps import current_principal, secured
from grc_api.auth.principal import Principal
from grc_api.db import get_db
from grc_api.schemas.content import ContentIn, ContentOut
from grc_api.services import content as svc

router = APIRouter(prefix="/api/v1", tags=["content"])
Db = Annotated[AsyncSession, Depends(get_db)]
Me = Annotated[Principal, Depends(current_principal)]


@router.get("/content", operation_id="content_get", **secured("people:read"))
async def content_get(db: Db) -> ContentOut:
    """Custom fields and additional dropdown values (every form needs them)."""
    return await svc.view(db)


@router.put("/content", operation_id="content_update", **secured("content:manage"))
async def content_update(
    body: ContentIn,
    db: Db,
    p: Me,
    if_match: Annotated[str | None, Header()] = None,
) -> ContentOut:
    return await svc.update(db, body, if_match, p)
