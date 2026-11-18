from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.deps import current_principal, secured
from grc_api.auth.principal import Principal
from grc_api.db import get_db
from grc_api.schemas.assistant import (
    AiSettingsIn,
    AiSettingsOut,
    AiTestOut,
    AskIn,
    AskOut,
    AssistantStatus,
)
from grc_api.services import assistant as svc

router = APIRouter(prefix="/api/v1", tags=["assistant"])
Db = Annotated[AsyncSession, Depends(get_db)]
Me = Annotated[Principal, Depends(current_principal)]


@router.get("/ai/settings", operation_id="ai_settings_get", **secured("ai:manage"))
async def ai_settings_get(db: Db, p: Me) -> AiSettingsOut:
    return await svc.settings_view(db, p)


@router.put("/ai/settings", operation_id="ai_settings_update", **secured("ai:manage"))
async def ai_settings_update(
    body: AiSettingsIn,
    db: Db,
    p: Me,
    if_match: Annotated[str | None, Header()] = None,
) -> AiSettingsOut:
    return await svc.update_settings(db, body, if_match, p)


@router.post("/ai/test", operation_id="ai_test", **secured("ai:manage"))
async def ai_test(db: Db, p: Me) -> AiTestOut:
    """Sends a short request with the stored key and model."""
    return await svc.test_connection(db, p)


@router.get("/assistant", operation_id="assistant_status", **secured("people:read"))
async def assistant_status(db: Db) -> AssistantStatus:
    return await svc.status(db)


@router.post("/assistant/ask", operation_id="assistant_ask", **secured("people:read"))
async def assistant_ask(body: AskIn, db: Db, p: Me) -> AskOut:
    """Answer with links to elements the person may open (AI, or catalogue search without it)."""
    return await svc.ask(db, body, p)
