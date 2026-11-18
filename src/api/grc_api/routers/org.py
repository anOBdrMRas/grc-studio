from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.deps import current_principal, secured
from grc_api.auth.principal import Principal
from grc_api.db import get_db
from grc_api.schemas.common import CreateElement, ElementPatch, Revision, StateView, WorkflowAction
from grc_api.schemas.org import OrgChartOut, PositionListItem, PositionOut, RoleListItem, RoleOut
from grc_api.services import org as svc

router = APIRouter(prefix="/api/v1", tags=["organisation"])
Db = Annotated[AsyncSession, Depends(get_db)]
Me = Annotated[Principal, Depends(current_principal)]
IfMatch = Annotated[str | None, Header()]


@router.get("/roles", operation_id="roles_list", **secured("org:read"))
async def roles_list(db: Db, p: Me) -> list[RoleListItem]:
    return await svc.list_roles(db, p)


@router.post("/roles", operation_id="roles_create", status_code=201, **secured("org:manage"))
async def roles_create(body: CreateElement, db: Db, p: Me) -> RoleOut:
    return await svc.create_role(db, body.title, p)


@router.get("/roles/{role_id}", operation_id="roles_get", **secured("org:read"))
async def roles_get(role_id: str, db: Db, p: Me) -> RoleOut:
    return await svc.role_view(db, role_id, p)


@router.patch("/roles/{role_id}", operation_id="roles_update", **secured("org:read"))
async def roles_update(
    role_id: str, body: ElementPatch, db: Db, p: Me, if_match: IfMatch = None
) -> RoleOut:
    return await svc.update_role(db, role_id, body, if_match, p)


@router.delete(
    "/roles/{role_id}", operation_id="roles_delete", status_code=204, **secured("org:manage")
)
async def roles_delete(role_id: str, db: Db, p: Me) -> None:
    await svc.delete_role(db, role_id, p)


@router.post("/roles/{role_id}/workflow", operation_id="roles_workflow", **secured("org:read"))
async def roles_workflow(
    role_id: str, body: WorkflowAction, db: Db, p: Me, if_match: IfMatch = None
) -> RoleOut:
    return await svc.role_workflow(db, role_id, body, if_match, p)


@router.get("/roles/{role_id}/history", operation_id="roles_history", **secured("org:read"))
async def roles_history(role_id: str, db: Db, p: Me) -> list[Revision]:
    return await svc.history(db, "role", role_id, p)


@router.get(
    "/roles/{role_id}/history/{revision_id}", operation_id="roles_state", **secured("org:read")
)
async def roles_state(role_id: str, revision_id: int, db: Db, p: Me) -> StateView:
    return await svc.state(db, "role", role_id, revision_id, p)


@router.get("/org-chart", operation_id="org_chart", **secured("org:read"))
async def org_chart(db: Db, p: Me) -> OrgChartOut:
    """Hierarchies of the positions, positions by unit and the role matrix."""
    return await svc.org_chart(db, p)


@router.get("/positions", operation_id="positions_list", **secured("org:read"))
async def positions_list(db: Db, p: Me) -> list[PositionListItem]:
    return await svc.list_positions(db, p)


@router.post(
    "/positions", operation_id="positions_create", status_code=201, **secured("org:manage")
)
async def positions_create(body: CreateElement, db: Db, p: Me) -> PositionOut:
    return await svc.create_position(db, body.title, p)


@router.get("/positions/{position_id}", operation_id="positions_get", **secured("org:read"))
async def positions_get(position_id: str, db: Db, p: Me) -> PositionOut:
    return await svc.position_view(db, position_id, p)


@router.patch("/positions/{position_id}", operation_id="positions_update", **secured("org:read"))
async def positions_update(
    position_id: str, body: ElementPatch, db: Db, p: Me, if_match: IfMatch = None
) -> PositionOut:
    return await svc.update_position(db, position_id, body, if_match, p)


@router.delete(
    "/positions/{position_id}",
    operation_id="positions_delete",
    status_code=204,
    **secured("org:manage"),
)
async def positions_delete(position_id: str, db: Db, p: Me) -> None:
    await svc.delete_position(db, position_id, p)


@router.post(
    "/positions/{position_id}/workflow", operation_id="positions_workflow", **secured("org:read")
)
async def positions_workflow(
    position_id: str, body: WorkflowAction, db: Db, p: Me, if_match: IfMatch = None
) -> PositionOut:
    return await svc.position_workflow(db, position_id, body, if_match, p)


@router.get(
    "/positions/{position_id}/history", operation_id="positions_history", **secured("org:read")
)
async def positions_history(position_id: str, db: Db, p: Me) -> list[Revision]:
    return await svc.history(db, "position", position_id, p)


@router.get(
    "/positions/{position_id}/history/{revision_id}",
    operation_id="positions_state",
    **secured("org:read"),
)
async def positions_state(position_id: str, revision_id: int, db: Db, p: Me) -> StateView:
    return await svc.state(db, "position", position_id, revision_id, p)
