from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.deps import current_principal, secured
from grc_api.auth.principal import Principal
from grc_api.db import get_db
from grc_api.schemas.common import CreateElement, ElementPatch, Revision, StateView, WorkflowAction
from grc_api.schemas.processes import (
    CallLinkIn,
    DiagramIn,
    DiagramOut,
    ProcessListItem,
    ProcessOut,
    StepLinkIn,
    StepRoleIn,
)
from grc_api.services import processes as svc

router = APIRouter(prefix="/api/v1/processes", tags=["processes"])
Db = Annotated[AsyncSession, Depends(get_db)]
Me = Annotated[Principal, Depends(current_principal)]
IfMatch = Annotated[str | None, Header()]


@router.get("", operation_id="processes_list", **secured("processes:read"))
async def processes_list(db: Db, p: Me) -> list[ProcessListItem]:
    return await svc.list_processes(db, p)


@router.post("", operation_id="processes_create", status_code=201, **secured("processes:manage"))
async def processes_create(body: CreateElement, db: Db, p: Me) -> ProcessOut:
    return await svc.create_process(db, body.title, p)


@router.get("/{process_id}", operation_id="processes_get", **secured("processes:read"))
async def processes_get(process_id: str, db: Db, p: Me) -> ProcessOut:
    return await svc.process_view(db, process_id, p)


@router.patch("/{process_id}", operation_id="processes_update", **secured("processes:read"))
async def processes_update(
    process_id: str, body: ElementPatch, db: Db, p: Me, if_match: IfMatch = None
) -> ProcessOut:
    return await svc.update_process(db, process_id, body, if_match, p)


@router.delete(
    "/{process_id}", operation_id="processes_delete", status_code=204, **secured("processes:manage")
)
async def processes_delete(process_id: str, db: Db, p: Me) -> None:
    await svc.delete_process(db, process_id, p)


@router.get("/{process_id}/diagram", operation_id="processes_diagram", **secured("processes:read"))
async def processes_diagram(process_id: str, db: Db, p: Me) -> DiagramOut:
    return await svc.diagram(db, process_id, p)


@router.put(
    "/{process_id}/diagram", operation_id="processes_save_diagram", **secured("processes:read")
)
async def processes_save_diagram(
    process_id: str, body: DiagramIn, db: Db, p: Me, if_match: IfMatch = None
) -> DiagramOut:
    return await svc.save_diagram(db, process_id, body, if_match, p)


@router.put(
    "/{process_id}/steps/{element_id}/call",
    operation_id="processes_link_call",
    **secured("processes:read"),
)
async def processes_link_call(
    process_id: str, element_id: str, body: CallLinkIn, db: Db, p: Me, if_match: IfMatch = None
) -> ProcessOut:
    """Links a call activity to the called process; the editing rights of the process apply."""
    return await svc.link_call(db, process_id, element_id, body, if_match, p)


@router.put(
    "/{process_id}/steps/{element_id}/roles",
    operation_id="processes_assign_role",
    **secured("processes:read"),
)
async def processes_assign_role(
    process_id: str, element_id: str, body: StepRoleIn, db: Db, p: Me, if_match: IfMatch = None
) -> ProcessOut:
    return await svc.assign_role(db, process_id, element_id, body, if_match, p)


@router.delete(
    "/{process_id}/steps/{element_id}/roles/{role_id}",
    operation_id="processes_unassign_role",
    **secured("processes:read"),
)
async def processes_unassign_role(
    process_id: str,
    element_id: str,
    role_id: str,
    db: Db,
    p: Me,
    version: int | None = None,
    if_match: IfMatch = None,
) -> ProcessOut:
    return await svc.unassign_role(db, process_id, element_id, role_id, version, if_match, p)


@router.post(
    "/{process_id}/workflow", operation_id="processes_workflow", **secured("processes:read")
)
async def processes_workflow(
    process_id: str, body: WorkflowAction, db: Db, p: Me, if_match: IfMatch = None
) -> ProcessOut:
    return await svc.workflow(db, process_id, body, if_match, p)


@router.get("/{process_id}/history", operation_id="processes_history", **secured("processes:read"))
async def processes_history(process_id: str, db: Db, p: Me) -> list[Revision]:
    return await svc.history(db, process_id, p)


@router.get(
    "/{process_id}/history/{revision_id}",
    operation_id="processes_state",
    **secured("processes:read"),
)
async def processes_state(process_id: str, revision_id: int, db: Db, p: Me) -> StateView:
    return await svc.state(db, process_id, revision_id, p)


@router.put(
    "/{process_id}/steps/{element_id}/links",
    operation_id="processes_link_element",
    **secured("processes:read"),
)
async def processes_link_element(
    process_id: str, element_id: str, body: StepLinkIn, db: Db, p: Me, if_match: IfMatch = None
) -> ProcessOut:
    return await svc.link_element(db, process_id, element_id, body, if_match, p)


@router.delete(
    "/{process_id}/steps/{element_id}/links/{kind}/{target_id}",
    operation_id="processes_unlink_element",
    **secured("processes:read"),
)
async def processes_unlink_element(
    process_id: str,
    element_id: str,
    kind: str,
    target_id: str,
    db: Db,
    p: Me,
    version: int | None = None,
    if_match: IfMatch = None,
) -> ProcessOut:
    return await svc.unlink_element(
        db, process_id, element_id, kind, target_id, version, if_match, p
    )
