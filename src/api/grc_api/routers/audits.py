"""Audits and findings with corrective actions."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.deps import current_principal, secured
from grc_api.auth.principal import Principal
from grc_api.db import get_db
from grc_api.schemas.audits import AuditListItem, AuditOut, FindingCreate
from grc_api.schemas.common import CreateElement, ElementPatch, Revision, StateView
from grc_api.schemas.quality import CockpitOut
from grc_api.services import audits as svc
from grc_api.services import quality as quality_svc

router = APIRouter(prefix="/api/v1", tags=["audits"])
Db = Annotated[AsyncSession, Depends(get_db)]
Me = Annotated[Principal, Depends(current_principal)]
IfMatch = Annotated[str | None, Header()]


@router.get("/audits", operation_id="audits_list", **secured("grc:read"))
async def audits_list(db: Db, p: Me) -> list[AuditListItem]:
    return await svc.list_audits(db, p)


@router.post("/audits", operation_id="audits_create", status_code=201, **secured("grc:manage"))
async def audits_create(body: CreateElement, db: Db, p: Me) -> AuditOut:
    return await svc.create_audit(db, body.title, p)


@router.get("/audits/{audit_id}", operation_id="audits_get", **secured("grc:read"))
async def audits_get(audit_id: str, db: Db, p: Me) -> AuditOut:
    return await svc.audit_view(db, audit_id, p)


@router.patch("/audits/{audit_id}", operation_id="audits_update", **secured("grc:read"))
async def audits_update(
    audit_id: str, body: ElementPatch, db: Db, p: Me, if_match: IfMatch = None
) -> AuditOut:
    return await svc.update_audit(db, audit_id, body, if_match, p)


@router.delete(
    "/audits/{audit_id}", operation_id="audits_delete", status_code=204, **secured("grc:manage")
)
async def audits_delete(audit_id: str, db: Db, p: Me) -> None:
    await svc.delete_audit(db, audit_id, p)


@router.post(
    "/audits/{audit_id}/findings", operation_id="audits_create_finding", **secured("grc:read")
)
async def audits_create_finding(audit_id: str, body: FindingCreate, db: Db, p: Me) -> AuditOut:
    return await svc.create_finding(db, audit_id, body, p)


@router.patch(
    "/audits/{audit_id}/findings/{finding_id}",
    operation_id="audits_update_finding",
    **secured("grc:read"),
)
async def audits_update_finding(
    audit_id: str, finding_id: str, body: ElementPatch, db: Db, p: Me, if_match: IfMatch = None
) -> AuditOut:
    return await svc.update_finding(db, audit_id, finding_id, body, if_match, p)


@router.delete(
    "/audits/{audit_id}/findings/{finding_id}",
    operation_id="audits_delete_finding",
    **secured("grc:read"),
)
async def audits_delete_finding(audit_id: str, finding_id: str, db: Db, p: Me) -> AuditOut:
    return await svc.delete_finding(db, audit_id, finding_id, p)


@router.get("/audits/{audit_id}/history", operation_id="audits_history", **secured("grc:read"))
async def audits_history(audit_id: str, db: Db, p: Me) -> list[Revision]:
    return await svc.history(db, audit_id, p)


@router.get(
    "/audits/{audit_id}/history/{revision_id}", operation_id="audits_state", **secured("grc:read")
)
async def audits_state(audit_id: str, revision_id: int, db: Db, p: Me) -> StateView:
    return await svc.state(db, audit_id, revision_id, p)


@router.get("/cockpit", operation_id="cockpit_get", **secured("cockpit:read"))
async def cockpit_get(db: Db, p: Me) -> CockpitOut:
    """Quality checks, quality grade, workflow status and the review queue (I&A cockpit)."""
    return await quality_svc.cockpit(db, p)
