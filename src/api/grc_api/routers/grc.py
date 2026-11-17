"""Risks and opportunities. Everybody records (grc:record); rights per element are decided in the service."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.deps import current_principal, secured
from grc_api.auth.principal import Principal
from grc_api.db import get_db
from grc_api.schemas.common import CreateElement, ElementPatch, Revision, StateView, WorkflowAction
from grc_api.schemas.grc import (
    OpportunityListItem,
    OpportunityOut,
    RiskListItem,
    RiskOut,
)
from grc_api.services import grc as svc

router = APIRouter(prefix="/api/v1", tags=["risks and opportunities"])
Db = Annotated[AsyncSession, Depends(get_db)]
Me = Annotated[Principal, Depends(current_principal)]
IfMatch = Annotated[str | None, Header()]


# ---- risks -------------------------------------------------------------------------------------


@router.get("/risks", operation_id="risks_list", **secured("grc:read"))
async def risks_list(db: Db, p: Me) -> list[RiskListItem]:
    return await svc.list_risks(db, p)


@router.post("/risks", operation_id="risks_create", status_code=201, **secured("grc:record"))
async def risks_create(body: CreateElement, db: Db, p: Me) -> RiskOut:
    return await svc.create_risk(db, body.title, p)


@router.get("/risks/{risk_id}", operation_id="risks_get", **secured("grc:read"))
async def risks_get(risk_id: str, db: Db, p: Me) -> RiskOut:
    return await svc.risk_view(db, risk_id, p)


@router.patch("/risks/{risk_id}", operation_id="risks_update", **secured("grc:read"))
async def risks_update(
    risk_id: str, body: ElementPatch, db: Db, p: Me, if_match: IfMatch = None
) -> RiskOut:
    return await svc.update_risk(db, risk_id, body, if_match, p)


@router.delete(
    "/risks/{risk_id}", operation_id="risks_delete", status_code=204, **secured("grc:record")
)
async def risks_delete(risk_id: str, db: Db, p: Me) -> None:
    await svc.delete(db, "risk", risk_id, p)


@router.post("/risks/{risk_id}/workflow", operation_id="risks_workflow", **secured("grc:read"))
async def risks_workflow(
    risk_id: str, body: WorkflowAction, db: Db, p: Me, if_match: IfMatch = None
) -> RiskOut:
    await svc.workflow(db, "risk", risk_id, body, if_match, p)
    return await svc.risk_view(db, risk_id, p)


@router.get("/risks/{risk_id}/history", operation_id="risks_history", **secured("grc:read"))
async def risks_history(risk_id: str, db: Db, p: Me) -> list[Revision]:
    return await svc.history(db, "risk", risk_id, p)


@router.get(
    "/risks/{risk_id}/history/{revision_id}", operation_id="risks_state", **secured("grc:read")
)
async def risks_state(risk_id: str, revision_id: int, db: Db, p: Me) -> StateView:
    return await svc.state(db, "risk", risk_id, revision_id, p)


# ---- opportunities -----------------------------------------------------------------------------


@router.get("/opportunities", operation_id="opportunities_list", **secured("grc:read"))
async def opportunities_list(db: Db, p: Me) -> list[OpportunityListItem]:
    return await svc.list_opportunities(db, p)


@router.post(
    "/opportunities",
    operation_id="opportunities_create",
    status_code=201,
    **secured("grc:record"),
)
async def opportunities_create(body: CreateElement, db: Db, p: Me) -> OpportunityOut:
    return await svc.create_opportunity(db, body.title, p)


@router.get("/opportunities/{opp_id}", operation_id="opportunities_get", **secured("grc:read"))
async def opportunities_get(opp_id: str, db: Db, p: Me) -> OpportunityOut:
    return await svc.opportunity_view(db, opp_id, p)


@router.patch("/opportunities/{opp_id}", operation_id="opportunities_update", **secured("grc:read"))
async def opportunities_update(
    opp_id: str, body: ElementPatch, db: Db, p: Me, if_match: IfMatch = None
) -> OpportunityOut:
    return await svc.update_opportunity(db, opp_id, body, if_match, p)


@router.delete(
    "/opportunities/{opp_id}",
    operation_id="opportunities_delete",
    status_code=204,
    **secured("grc:record"),
)
async def opportunities_delete(opp_id: str, db: Db, p: Me) -> None:
    await svc.delete(db, "opportunity", opp_id, p)


@router.post(
    "/opportunities/{opp_id}/workflow",
    operation_id="opportunities_workflow",
    **secured("grc:read"),
)
async def opportunities_workflow(
    opp_id: str, body: WorkflowAction, db: Db, p: Me, if_match: IfMatch = None
) -> OpportunityOut:
    await svc.workflow(db, "opportunity", opp_id, body, if_match, p)
    return await svc.opportunity_view(db, opp_id, p)


@router.get(
    "/opportunities/{opp_id}/history",
    operation_id="opportunities_history",
    **secured("grc:read"),
)
async def opportunities_history(opp_id: str, db: Db, p: Me) -> list[Revision]:
    return await svc.history(db, "opportunity", opp_id, p)


@router.get(
    "/opportunities/{opp_id}/history/{revision_id}",
    operation_id="opportunities_state",
    **secured("grc:read"),
)
async def opportunities_state(opp_id: str, revision_id: int, db: Db, p: Me) -> StateView:
    return await svc.state(db, "opportunity", opp_id, revision_id, p)
