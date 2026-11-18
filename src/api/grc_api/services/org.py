"""Roles and positions."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.domain.codes import next_code
from grc_api.domain.org import sod_conflicts, tree
from grc_api.errors import ProblemError
from grc_api.models import Position, Role
from grc_api.repositories import audit, elements
from grc_api.repositories import org as org_repo
from grc_api.schemas.common import ElementPatch, Revision, StateView, WorkflowAction
from grc_api.schemas.common import PersonRef as PersonRefOut
from grc_api.schemas.org import (
    ChartPosition,
    ChartRole,
    ChartTree,
    ChartUnit,
    Holder,
    OrgChartOut,
    PositionFields,
    PositionListItem,
    PositionOut,
    RoleFields,
    RoleListItem,
    RoleOut,
)
from grc_api.services import common
from grc_api.services.context import OrgData, load_org


def _need(p: Principal, perm: str) -> None:
    if not p.can(perm):
        raise ProblemError("forbidden", f"Permission {perm} required")


# ---- roles -------------------------------------------------------------------------------------


async def list_roles(db: AsyncSession, p: Principal) -> list[RoleListItem]:
    _need(p, "org:read")
    org = await load_org(db)
    return [
        RoleListItem(
            id=r.id,
            code=r.code,
            title=r.title,
            role_type=r.role_type,
            mandatory=r.mandatory,
            holders=sorted({org.name(u) for u in org.role_holders(r.id)}),
            status=r.status,
            is_owner=p.user_id in org.owners("role", r),
        )
        for r in org.roles.values()
    ]


async def role_view(
    db: AsyncSession, role_id: str, p: Principal, org: OrgData | None = None
) -> RoleOut:
    _need(p, "org:read")
    org = org or await load_org(db)
    r = org.roles.get(role_id)
    if r is None:
        raise ProblemError("not_found", "Role not found")
    holders = [
        Holder(
            user=PersonRefOut(id=u.id, name=u.display_name),
            position_id=u.position_id or "",
            position_title=org.positions[u.position_id].title,
        )
        for u in org.users.values()
        if u.position_id in org.positions
        and any(rid == r.id for rid, _ in org.position_roles.get(u.position_id, []))
    ]
    positions = [
        {"id": pos.id, "code": pos.code, "title": pos.title, "comment": c}
        for pos in org.positions.values()
        for rid, c in org.position_roles.get(pos.id, [])
        if rid == r.id
    ]
    refs = [r.role_owner_user_id, *r.incompatible_role_ids]
    return RoleOut(
        **common.fields_of(r, RoleFields),
        id=r.id,
        custom=r.custom,
        code=r.code,
        status=r.status,
        doc_version=r.doc_version,
        version=r.version,
        created_at=r.created_at,
        updated_at=r.updated_at,
        rights=common.rights("role", r, org, p),
        holders=holders,
        positions=positions,
        workflow=await common.workflow_out(db, "role", r.id, org),
        released=r.released,
        labels={x: org.label(x) for x in refs if x},
    )


async def create_role(db: AsyncSession, title: str, p: Principal) -> RoleOut:
    _need(p, "org:manage")
    code = next_code(await elements.codes(db, Role), "RO")
    await elements.insert(db, Role(id=code, code=code, title=title))
    await audit.record(
        db, p.user_id, "create", "role", code, [{"key": "title", "from": None, "to": title}]
    )
    await db.commit()
    return await role_view(db, code, p)


async def update_role(
    db: AsyncSession, role_id: str, patch: ElementPatch, if_match: str | None, p: Principal
) -> RoleOut:
    org = await load_org(db)
    r = await common.get_or_404(db, Role, role_id)
    version = common.expected_version(if_match, patch.version)
    changes = await common.save_element(db, "role", r, RoleFields, patch.values, version, p, org)
    # incompatible roles are symmetric: keep the counterparts in sync
    inc = next((c for c in changes if c["key"] == "incompatible_role_ids"), None)
    if inc:
        before, after = set(inc["from"] or []), set(inc["to"] or [])
        for other_id in before ^ after:
            other = org.roles.get(other_id)
            if other is None:
                continue
            new = sorted(
                (set(other.incompatible_role_ids) | {role_id})
                if other_id in after
                else (set(other.incompatible_role_ids) - {role_id})
            )
            if new != sorted(other.incompatible_role_ids):
                await elements.update_versioned(
                    db, Role, other.id, other.version, {"incompatible_role_ids": new}
                )
                await audit.record(
                    db,
                    p.user_id,
                    "update",
                    "role",
                    other.id,
                    [
                        {
                            "key": "incompatible_role_ids",
                            "from": other.incompatible_role_ids,
                            "to": new,
                        }
                    ],
                )
    await db.commit()
    db.expire_all()
    return await role_view(db, role_id, p)


async def delete_role(db: AsyncSession, role_id: str, p: Principal) -> None:
    _need(p, "org:manage")
    await common.get_or_404(db, Role, role_id)
    await elements.remove(db, Role, role_id)
    await audit.record(db, p.user_id, "delete", "role", role_id)
    await db.commit()


async def role_workflow(
    db: AsyncSession, role_id: str, body: WorkflowAction, if_match: str | None, p: Principal
) -> RoleOut:
    org = await load_org(db)
    r = await common.get_or_404(db, Role, role_id)
    await common.workflow_action(
        db,
        "role",
        r,
        RoleFields,
        body.action,
        body.comment,
        body.target_status,
        common.expected_version(if_match, body.version),
        p,
        org,
    )
    await db.commit()
    db.expire_all()
    return await role_view(db, role_id, p)


# ---- positions ---------------------------------------------------------------------------------


def _pos_fields(pos: Position, org: OrgData) -> dict[str, Any]:
    return common.fields_of(pos, PositionFields) | {
        "roles": [{"role_id": r, "comment": c} for r, c in org.position_roles.get(pos.id, [])]
    }


async def list_positions(db: AsyncSession, p: Principal) -> list[PositionListItem]:
    _need(p, "org:read")
    org = await load_org(db)
    return [
        PositionListItem(
            id=x.id,
            code=x.code,
            title=x.title,
            org_unit=x.org_unit,
            holders=[u.display_name for u in org.users.values() if u.position_id == x.id],
            status=x.status,
            is_owner=p.user_id in org.owners("position", x),
        )
        for x in org.positions.values()
    ]


async def org_chart(db: AsyncSession, p: Principal) -> OrgChartOut:
    """Positions as hierarchies (disciplinary, functional), by organisational unit and as role
    matrix."""
    _need(p, "org:read")
    org = await load_org(db)
    positions = sorted(org.positions.values(), key=lambda x: x.code)

    def chart_role(role_id: str, comment: str) -> ChartRole | None:
        r = org.roles.get(role_id)
        return ChartRole(role_id=r.id, code=r.code, title=r.title, comment=comment) if r else None

    out: list[ChartPosition] = []
    for x in positions:
        pairs = org.position_roles.get(x.id, [])
        role_ids = [r for r, _ in pairs]
        incompatible = {
            rid: list(org.roles[rid].incompatible_role_ids) for rid in role_ids if rid in org.roles
        }
        out.append(
            ChartPosition(
                id=x.id,
                code=x.code,
                title=x.title,
                org_unit=x.org_unit,
                is_manager=x.is_manager,
                headcount=x.headcount,
                holders=[
                    u.display_name
                    for u in org.users.values()
                    if u.position_id == x.id and u.status == "active"
                ],
                roles=[cr for r, c in pairs if (cr := chart_role(r, c))],
                sod_conflict=bool(sod_conflicts(role_ids, incompatible)),
            )
        )
    used = {r for x in positions for r, _ in org.position_roles.get(x.id, [])}
    units: dict[str, list[str]] = {}
    for x in positions:
        units.setdefault(x.org_unit or "–", []).append(x.id)

    def chart_tree(line: str) -> ChartTree:
        t = tree([(x.id, getattr(x, f"reports_to_{line}_id")) for x in positions])
        return ChartTree(roots=t.roots, children=t.children, separate=t.separate)

    return OrgChartOut(
        positions=out,
        disciplinary=chart_tree("disciplinary"),
        functional=chart_tree("functional"),
        units=[ChartUnit(unit=u, position_ids=ids) for u, ids in units.items()],
        matrix_roles=[
            cr
            for r in sorted(org.roles.values(), key=lambda r: r.code)
            if r.id in used and (cr := chart_role(r.id, ""))
        ],
    )


async def position_view(db: AsyncSession, position_id: str, p: Principal) -> PositionOut:
    _need(p, "org:read")
    org = await load_org(db)
    x = org.positions.get(position_id)
    if x is None:
        raise ProblemError("not_found", "Position not found")
    role_ids = [r for r, _ in org.position_roles.get(x.id, [])]
    incompatible = {
        rid: list(org.roles[rid].incompatible_role_ids) for rid in role_ids if rid in org.roles
    }
    refs = [
        x.reports_to_disciplinary_id,
        x.reports_to_functional_id,
        x.deputy_position_id,
        *role_ids,
    ]
    return PositionOut(
        **_pos_fields(x, org),
        id=x.id,
        custom=x.custom,
        code=x.code,
        status=x.status,
        doc_version=x.doc_version,
        version=x.version,
        created_at=x.created_at,
        updated_at=x.updated_at,
        rights=common.rights("position", x, org, p),
        holders=[
            PersonRefOut(id=u.id, name=u.display_name)
            for u in org.users.values()
            if u.position_id == x.id
        ],
        sod_conflicts=[list(pair) for pair in sod_conflicts(role_ids, incompatible)],
        workflow=await common.workflow_out(db, "position", x.id, org),
        released=x.released,
        labels={r: org.label(r) for r in refs if r and r != "n/a"},
    )


async def create_position(db: AsyncSession, title: str, p: Principal) -> PositionOut:
    _need(p, "org:manage")
    code = next_code(await elements.codes(db, Position), "ST")
    await elements.insert(db, Position(id=code, code=code, title=title))
    await audit.record(
        db, p.user_id, "create", "position", code, [{"key": "title", "from": None, "to": title}]
    )
    await db.commit()
    return await position_view(db, code, p)


async def update_position(
    db: AsyncSession, position_id: str, patch: ElementPatch, if_match: str | None, p: Principal
) -> PositionOut:
    org = await load_org(db)
    x = await common.get_or_404(db, Position, position_id)
    current_roles = _pos_fields(x, org)["roles"]
    changes = await common.save_element(
        db,
        "position",
        x,
        PositionFields,
        patch.values,
        common.expected_version(if_match, patch.version),
        p,
        org,
        before_extra={"roles": current_roles},
    )
    roles = next((c["to"] for c in changes if c["key"] == "roles"), None)
    if roles is not None:
        await org_repo.replace_position_roles(
            db, position_id, [(r["role_id"], r.get("comment", "")) for r in roles]
        )
    await db.commit()
    db.expire_all()
    return await position_view(db, position_id, p)


async def delete_position(db: AsyncSession, position_id: str, p: Principal) -> None:
    _need(p, "org:manage")
    await common.get_or_404(db, Position, position_id)
    await elements.remove(db, Position, position_id)
    await audit.record(db, p.user_id, "delete", "position", position_id)
    await db.commit()


async def position_workflow(
    db: AsyncSession, position_id: str, body: WorkflowAction, if_match: str | None, p: Principal
) -> PositionOut:
    org = await load_org(db)
    x = await common.get_or_404(db, Position, position_id)
    await common.workflow_action(
        db,
        "position",
        x,
        PositionFields,
        body.action,
        body.comment,
        body.target_status,
        common.expected_version(if_match, body.version),
        p,
        org,
    )
    await db.commit()
    db.expire_all()
    return await position_view(db, position_id, p)


# ---- history (both kinds) ----------------------------------------------------------------------


async def history(db: AsyncSession, kind: str, id_: str, p: Principal) -> list[Revision]:
    _need(p, "org:read")
    return await common.revisions(db, kind, id_, await load_org(db))


async def state(db: AsyncSession, kind: str, id_: str, revision_id: int, p: Principal) -> StateView:
    _need(p, "org:read")
    org = await load_org(db)
    if kind == "role":
        r = await common.get_or_404(db, Role, id_)
        current = common.state_of(r, RoleFields)
    else:
        x = await common.get_or_404(db, Position, id_)
        current = _pos_fields(x, org) | dict(x.custom or {})
    return await common.state_after(db, kind, id_, revision_id, current, org)
