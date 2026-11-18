"""Persons: names for everybody, the user management for administrators."""

from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.domain.catalogs import SYSTEM_ROLE_IDS
from grc_api.domain.codes import full_name, next_code
from grc_api.domain.history import diff
from grc_api.errors import ProblemError
from grc_api.models import User
from grc_api.repositories import audit, elements
from grc_api.schemas.common import ElementPatch, Revision
from grc_api.schemas.users import PersonOut, UserFields, UserListItem, UserOut
from grc_api.services import common, content
from grc_api.services.context import load_org


def _need(p: Principal, perm: str) -> None:
    if not p.can(perm):
        raise ProblemError("forbidden", f"Permission {perm} required")


async def people(db: AsyncSession, p: Principal) -> list[PersonOut]:
    _need(p, "people:read")
    org = await load_org(db)
    return [
        PersonOut(
            id=u.id,
            name=u.display_name,
            position_id=u.position_id,
            position_title=org.positions[u.position_id].title
            if u.position_id in org.positions
            else "",
            system_roles=list(u.system_roles),
        )
        for u in sorted(org.users.values(), key=lambda u: (u.last_name, u.first_name))
        if u.status == "active"
    ]


async def list_users(db: AsyncSession, p: Principal) -> list[UserListItem]:
    _need(p, "users:read")
    org = await load_org(db)
    return [
        UserListItem(
            id=u.id,
            code=u.code,
            name=u.display_name,
            position_title=org.positions[u.position_id].title
            if u.position_id in org.positions
            else "",
            division=u.division,
        )
        for u in org.users.values()
    ]


async def user_view(db: AsyncSession, user_id: str, p: Principal) -> UserOut:
    _need(p, "users:read")
    org = await load_org(db)
    u = org.users.get(user_id)
    if u is None:
        raise ProblemError("not_found", "User not found")
    return UserOut(
        **common.fields_of(u, UserFields),
        id=u.id,
        custom=u.custom,
        code=u.code,
        name=u.display_name,
        status=u.status,
        version=u.version,
        created_at=u.created_at,
        updated_at=u.updated_at,
        labels={u.position_id: org.label(u.position_id)} if u.position_id else {},
        can_manage=p.can("users:manage"),
    )


async def create_user(db: AsyncSession, last_name: str, first_name: str, p: Principal) -> UserOut:
    _need(p, "users:manage")
    code = next_code(await elements.codes(db, User), "U")
    name = full_name(first_name, last_name)
    await elements.insert(
        db,
        User(
            id=code,
            code=code,
            last_name=last_name,
            first_name=first_name,
            display_name=name,
            system_roles=["employee"],
        ),
    )
    await audit.record(
        db, p.user_id, "create", "user", code, [{"key": "name", "from": None, "to": name}]
    )
    await db.commit()
    return await user_view(db, code, p)


async def update_user(
    db: AsyncSession, user_id: str, patch: ElementPatch, if_match: str | None, p: Principal
) -> UserOut:
    _need(p, "users:manage")
    u = await common.get_or_404(db, User, user_id)
    version = common.expected_version(if_match, patch.version)
    std, custom_raw = content.split(patch.values)
    before = common.fields_of(u, UserFields)
    after = common.validate_merge(UserFields, before, std)
    if any(r not in SYSTEM_ROLE_IDS for r in after["system_roles"]):
        raise ProblemError("invalid", "Unknown system role")
    changes = diff(before, after)
    custom_changes, custom_after = await common.custom_update(
        db, "user", u, custom_raw, await load_org(db)
    )
    changes += custom_changes
    if changes:
        values = dict(after) | {"display_name": full_name(after["first_name"], after["last_name"])}
        if custom_changes:
            values["custom"] = custom_after
        if "position_id" in {c["key"] for c in changes}:
            from datetime import date

            values["position_since"] = date.today() if after["position_id"] else None
        if not await elements.update_versioned(db, User, user_id, version[0], values):
            raise common.stale(version[1])
        await audit.record(db, p.user_id, "update", "user", user_id, changes)
        await db.commit()
        db.expire_all()
    return await user_view(db, user_id, p)


async def delete_user(db: AsyncSession, user_id: str, p: Principal) -> None:
    _need(p, "users:manage")
    if user_id == p.user_id:
        raise ProblemError("conflict", "You cannot delete yourself")
    await common.get_or_404(db, User, user_id)
    await elements.remove(db, User, user_id)
    await audit.record(db, p.user_id, "delete", "user", user_id)
    await db.commit()


async def history(db: AsyncSession, user_id: str, p: Principal) -> list[Revision]:
    _need(p, "users:read")
    return await common.revisions(db, "user", user_id, await load_org(db))
