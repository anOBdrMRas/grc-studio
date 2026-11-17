"""Delegations and powers of attorney; legal-certainty checks."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.deps import current_principal, secured
from grc_api.auth.principal import Principal
from grc_api.db import get_db
from grc_api.schemas.common import CreateElement, ElementPatch, Revision, StateView
from grc_api.schemas.mandates import CheckOut, MandateAction, MandateListItem, MandateOut
from grc_api.services import mandates as svc

router = APIRouter(prefix="/api/v1", tags=["delegations"])
Db = Annotated[AsyncSession, Depends(get_db)]
Me = Annotated[Principal, Depends(current_principal)]
IfMatch = Annotated[str | None, Header()]


@router.get("/mandates", operation_id="mandates_list", **secured("org:read"))
async def mandates_list(db: Db, p: Me) -> list[MandateListItem]:
    return await svc.list_mandates(db, p)


@router.post("/mandates", operation_id="mandates_create", status_code=201, **secured("org:manage"))
async def mandates_create(body: CreateElement, db: Db, p: Me) -> MandateOut:
    return await svc.create_mandate(db, body.title, p)


@router.get("/mandates/{mandate_id}", operation_id="mandates_get", **secured("org:read"))
async def mandates_get(mandate_id: str, db: Db, p: Me) -> MandateOut:
    return await svc.mandate_view(db, mandate_id, p)


@router.patch("/mandates/{mandate_id}", operation_id="mandates_update", **secured("org:read"))
async def mandates_update(
    mandate_id: str, body: ElementPatch, db: Db, p: Me, if_match: IfMatch = None
) -> MandateOut:
    return await svc.update_mandate(db, mandate_id, body, if_match, p)


@router.delete(
    "/mandates/{mandate_id}",
    operation_id="mandates_delete",
    status_code=204,
    **secured("org:manage"),
)
async def mandates_delete(mandate_id: str, db: Db, p: Me) -> None:
    await svc.delete_mandate(db, mandate_id, p)


@router.post(
    "/mandates/{mandate_id}/workflow", operation_id="mandates_workflow", **secured("org:read")
)
async def mandates_workflow(
    mandate_id: str, body: MandateAction, db: Db, p: Me, if_match: IfMatch = None
) -> MandateOut:
    return await svc.mandate_workflow(db, mandate_id, body, if_match, p)


@router.get(
    "/mandates/{mandate_id}/history", operation_id="mandates_history", **secured("org:read")
)
async def mandates_history(mandate_id: str, db: Db, p: Me) -> list[Revision]:
    return await svc.history(db, mandate_id, p)


@router.get(
    "/mandates/{mandate_id}/history/{revision_id}",
    operation_id="mandates_state",
    **secured("org:read"),
)
async def mandates_state(mandate_id: str, revision_id: int, db: Db, p: Me) -> StateView:
    return await svc.state(db, mandate_id, revision_id, p)


@router.get("/checks", operation_id="checks_list", **secured("org:read"))
async def checks_list(
    db: Db,
    p: Me,
    user_id: str | None = None,
    role_id: str | None = None,
    position_id: str | None = None,
    mandate_id: str | None = None,
) -> list[CheckOut]:
    """Legal-certainty findings across persons, roles, positions and delegations."""
    return await svc.checks(
        db, p, user_id=user_id, role_id=role_id, position_id=position_id, mandate_id=mandate_id
    )
