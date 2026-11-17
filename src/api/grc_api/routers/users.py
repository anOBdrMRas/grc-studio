from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.deps import current_principal, secured
from grc_api.auth.principal import Principal
from grc_api.db import get_db
from grc_api.schemas.common import ElementPatch, Revision
from grc_api.schemas.users import CreateUser, PersonOut, UserListItem, UserOut
from grc_api.services import users as svc

router = APIRouter(prefix="/api/v1", tags=["users"])
Db = Annotated[AsyncSession, Depends(get_db)]
Me = Annotated[Principal, Depends(current_principal)]


@router.get("/people", operation_id="people_list", **secured("people:read"))
async def people_list(db: Db, p: Me) -> list[PersonOut]:
    return await svc.people(db, p)


@router.get("/users", operation_id="users_list", **secured("users:read"))
async def users_list(db: Db, p: Me) -> list[UserListItem]:
    return await svc.list_users(db, p)


@router.post("/users", operation_id="users_create", status_code=201, **secured("users:manage"))
async def users_create(body: CreateUser, db: Db, p: Me) -> UserOut:
    return await svc.create_user(db, body.last_name, body.first_name, p)


@router.get("/users/{user_id}", operation_id="users_get", **secured("users:read"))
async def users_get(user_id: str, db: Db, p: Me) -> UserOut:
    return await svc.user_view(db, user_id, p)


@router.patch("/users/{user_id}", operation_id="users_update", **secured("users:manage"))
async def users_update(
    user_id: str,
    body: ElementPatch,
    db: Db,
    p: Me,
    if_match: Annotated[str | None, Header()] = None,
) -> UserOut:
    return await svc.update_user(db, user_id, body, if_match, p)


@router.delete(
    "/users/{user_id}", operation_id="users_delete", status_code=204, **secured("users:manage")
)
async def users_delete(user_id: str, db: Db, p: Me) -> None:
    await svc.delete_user(db, user_id, p)


@router.get("/users/{user_id}/history", operation_id="users_history", **secured("users:read"))
async def users_history(user_id: str, db: Db, p: Me) -> list[Revision]:
    return await svc.history(db, user_id, p)
