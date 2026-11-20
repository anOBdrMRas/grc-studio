"""Work instructions: read by everybody who reads processes, created and deleted by I&A and
administration, edited by their owner (rights per element are decided in the service)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.deps import current_principal, secured
from grc_api.auth.principal import Principal
from grc_api.db import get_db
from grc_api.schemas.common import CreateElement, ElementPatch, Revision, StateView, WorkflowAction
from grc_api.schemas.instructions import WorkInstructionListItem, WorkInstructionOut
from grc_api.services import instructions as svc

router = APIRouter(prefix="/api/v1/instructions", tags=["work instructions"])
Db = Annotated[AsyncSession, Depends(get_db)]
Me = Annotated[Principal, Depends(current_principal)]
IfMatch = Annotated[str | None, Header()]


@router.get("", operation_id="instructions_list", **secured("processes:read"))
async def instructions_list(db: Db, p: Me) -> list[WorkInstructionListItem]:
    return await svc.list_instructions(db, p)


@router.post("", operation_id="instructions_create", status_code=201, **secured("processes:manage"))
async def instructions_create(body: CreateElement, db: Db, p: Me) -> WorkInstructionOut:
    return await svc.create(db, body.title, p)


@router.get("/{wi_id}", operation_id="instructions_get", **secured("processes:read"))
async def instructions_get(wi_id: str, db: Db, p: Me) -> WorkInstructionOut:
    return await svc.view(db, wi_id, p)


@router.patch("/{wi_id}", operation_id="instructions_update", **secured("processes:read"))
async def instructions_update(
    wi_id: str, body: ElementPatch, db: Db, p: Me, if_match: IfMatch = None
) -> WorkInstructionOut:
    """Owners edit their work instruction; the content is sanitised (only editor markup)."""
    return await svc.update(db, wi_id, body, if_match, p)


@router.delete(
    "/{wi_id}", operation_id="instructions_delete", status_code=204, **secured("processes:manage")
)
async def instructions_delete(wi_id: str, db: Db, p: Me) -> None:
    await svc.delete(db, wi_id, p)


@router.post("/{wi_id}/workflow", operation_id="instructions_workflow", **secured("processes:read"))
async def instructions_workflow(
    wi_id: str, body: WorkflowAction, db: Db, p: Me, if_match: IfMatch = None
) -> WorkInstructionOut:
    return await svc.workflow(db, wi_id, body, if_match, p)


@router.get("/{wi_id}/history", operation_id="instructions_history", **secured("processes:read"))
async def instructions_history(wi_id: str, db: Db, p: Me) -> list[Revision]:
    return await svc.history(db, wi_id, p)


@router.get(
    "/{wi_id}/history/{revision_id}",
    operation_id="instructions_state",
    **secured("processes:read"),
)
async def instructions_state(wi_id: str, revision_id: int, db: Db, p: Me) -> StateView:
    return await svc.state(db, wi_id, revision_id, p)
