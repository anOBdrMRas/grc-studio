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
    DraftCreate,
    DraftIn,
    DraftOut,
    SuggestIn,
    SuggestOut,
)
from grc_api.schemas.processes import ProcessOut
from grc_api.services import assistant as svc
from grc_api.services import processes as processes_svc

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


@router.post(
    "/assistant/suggest/{kind}/{element_id}",
    operation_id="assistant_suggest",
    **secured("people:read"),
)
async def assistant_suggest(
    kind: str, element_id: str, body: SuggestIn, db: Db, p: Me
) -> SuggestOut:
    """AI suggestions for the text fields of an element the person may edit (nothing is saved)."""
    return await svc.suggest(db, kind, element_id, body, p)


@router.post(
    "/assistant/process-draft",
    operation_id="assistant_process_draft",
    **secured("processes:manage"),
)
async def assistant_process_draft(body: DraftIn, db: Db, p: Me) -> DraftOut:
    """Steps of a process from a description: AI, or one line per step (nothing is saved)."""
    return await svc.draft_process(db, body, p)


@router.post(
    "/processes/from-draft",
    operation_id="processes_create_from_draft",
    status_code=201,
    **secured("processes:manage"),
)
async def processes_create_from_draft(body: DraftCreate, db: Db, p: Me) -> ProcessOut:
    """A new draft process with a generated BPMN diagram and the roles of its steps."""
    return await processes_svc.create_from_draft(db, body, p)
