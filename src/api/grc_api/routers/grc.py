"""Risks, opportunities, controls and KPI. Everybody records risks and opportunities (grc:record);
rights per element are decided in the service."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.deps import current_principal, secured
from grc_api.auth.principal import Principal
from grc_api.db import get_db
from grc_api.schemas.common import CreateElement, ElementPatch, Revision, StateView, WorkflowAction
from grc_api.schemas.grc import (
    ControlListItem,
    ControlOut,
    KpiListItem,
    KpiOut,
    MeasurementIn,
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


# ---- controls (ICS) ----------------------------------------------------------------------------


@router.get("/controls", operation_id="controls_list", **secured("grc:read"))
async def controls_list(db: Db, p: Me) -> list[ControlListItem]:
    return await svc.list_controls(db, p)


@router.post("/controls", operation_id="controls_create", status_code=201, **secured("grc:manage"))
async def controls_create(body: CreateElement, db: Db, p: Me) -> ControlOut:
    return await svc.create_control(db, body.title, p)


@router.get("/controls/{control_id}", operation_id="controls_get", **secured("grc:read"))
async def controls_get(control_id: str, db: Db, p: Me) -> ControlOut:
    return await svc.control_view(db, control_id, p)


@router.patch("/controls/{control_id}", operation_id="controls_update", **secured("grc:read"))
async def controls_update(
    control_id: str, body: ElementPatch, db: Db, p: Me, if_match: IfMatch = None
) -> ControlOut:
    return await svc.update_control(db, control_id, body, if_match, p)


@router.delete(
    "/controls/{control_id}",
    operation_id="controls_delete",
    status_code=204,
    **secured("grc:manage"),
)
async def controls_delete(control_id: str, db: Db, p: Me) -> None:
    await svc.delete(db, "control", control_id, p)


@router.get(
    "/controls/{control_id}/history", operation_id="controls_history", **secured("grc:read")
)
async def controls_history(control_id: str, db: Db, p: Me) -> list[Revision]:
    return await svc.history(db, "control", control_id, p)


@router.get(
    "/controls/{control_id}/history/{revision_id}",
    operation_id="controls_state",
    **secured("grc:read"),
)
async def controls_state(control_id: str, revision_id: int, db: Db, p: Me) -> StateView:
    return await svc.state(db, "control", control_id, revision_id, p)


# ---- KPI ---------------------------------------------------------------------------------------


@router.get("/kpis", operation_id="kpis_list", **secured("grc:read"))
async def kpis_list(db: Db, p: Me) -> list[KpiListItem]:
    return await svc.list_kpis(db, p)


@router.post("/kpis", operation_id="kpis_create", status_code=201, **secured("grc:manage"))
async def kpis_create(body: CreateElement, db: Db, p: Me) -> KpiOut:
    return await svc.create_kpi(db, body.title, p)


@router.get("/kpis/{kpi_id}", operation_id="kpis_get", **secured("grc:read"))
async def kpis_get(kpi_id: str, db: Db, p: Me) -> KpiOut:
    return await svc.kpi_view(db, kpi_id, p)


@router.patch("/kpis/{kpi_id}", operation_id="kpis_update", **secured("grc:read"))
async def kpis_update(
    kpi_id: str, body: ElementPatch, db: Db, p: Me, if_match: IfMatch = None
) -> KpiOut:
    return await svc.update_kpi(db, kpi_id, body, if_match, p)


@router.delete(
    "/kpis/{kpi_id}", operation_id="kpis_delete", status_code=204, **secured("grc:manage")
)
async def kpis_delete(kpi_id: str, db: Db, p: Me) -> None:
    await svc.delete(db, "kpi", kpi_id, p)


@router.put(
    "/kpis/{kpi_id}/measurements", operation_id="kpis_record_measurement", **secured("grc:read")
)
async def kpis_record_measurement(kpi_id: str, body: MeasurementIn, db: Db, p: Me) -> KpiOut:
    return await svc.record_measurement(db, kpi_id, body, p)


@router.delete(
    "/kpis/{kpi_id}/measurements/{day}",
    operation_id="kpis_delete_measurement",
    **secured("grc:read"),
)
async def kpis_delete_measurement(kpi_id: str, day: date, db: Db, p: Me) -> KpiOut:
    return await svc.delete_measurement(db, kpi_id, day, p)


@router.get("/kpis/{kpi_id}/history", operation_id="kpis_history", **secured("grc:read"))
async def kpis_history(kpi_id: str, db: Db, p: Me) -> list[Revision]:
    return await svc.history(db, "kpi", kpi_id, p)


@router.get(
    "/kpis/{kpi_id}/history/{revision_id}", operation_id="kpis_state", **secured("grc:read")
)
async def kpis_state(kpi_id: str, revision_id: int, db: Db, p: Me) -> StateView:
    return await svc.state(db, "kpi", kpi_id, revision_id, p)
