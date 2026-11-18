"""Delegations and powers of attorney, and the legal-certainty checks across the organisation."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.domain import mandates as md
from grc_api.domain.codes import next_code
from grc_api.errors import ProblemError
from grc_api.models import Mandate
from grc_api.repositories import audit, elements
from grc_api.schemas.common import ElementPatch, Revision, StateView
from grc_api.schemas.mandates import (
    CheckOut,
    MandateAction,
    MandateActions,
    MandateFields,
    MandateListItem,
    MandateOut,
)
from grc_api.services import common
from grc_api.services.context import OrgData, load_org

PREFIX = "DV"


def _need(p: Principal, perm: str) -> None:
    if not p.can(perm):
        raise ProblemError("forbidden", f"Permission {perm} required")


def effective(m: Mandate, today: date | None = None) -> md.State:
    return md.state(m.status, m.valid_from, m.valid_until, m.accepted_at, today or date.today())


def _actor(m: Mandate, p: Principal) -> md.Actor:
    return md.Actor(
        user_id=p.user_id,
        is_grantor=m.granted_by_user_id == p.user_id,
        is_recipient=m.recipient_user_id == p.user_id,
        can_manage=p.can("org:manage"),
    )


def _possible(m: Mandate, p: Principal, action: md.Action) -> bool:
    try:
        md.transition(m.status, m.accepted_at is not None, action, _actor(m, p))  # type: ignore[arg-type]
    except md.MandateError:
        return False
    return True


# ---- checks ------------------------------------------------------------------------------------


def run_checks(org: OrgData, mandates: list[Mandate], today: date | None = None) -> list[md.Issue]:
    day = today or date.today()
    persons = {
        u.id: md.PersonInfo(u.id, u.display_name, u.status == "active", u.position_id)
        for u in org.users.values()
    }
    roles = [
        md.RoleInfo(
            r.id,
            r.title,
            r.required_mandate,
            r.written_form,
            r.authority_notice,
            tuple(org.role_holders(r.id)),
        )
        for r in org.roles.values()
    ]
    positions = [
        md.PositionInfo(
            x.id,
            x.title,
            x.signing_authority,
            x.approval_limit,
            tuple(
                u.id for u in org.users.values() if u.position_id == x.id and u.status == "active"
            ),
        )
        for x in org.positions.values()
    ]
    infos = [
        md.MandateInfo(
            id=m.id,
            label=f"{m.code} {m.title}",
            mandate_type=m.mandate_type,
            state=effective(m, day),
            recipient_user_id=m.recipient_user_id,
            role_id=m.role_id,
            document=m.document,
            registered_at=m.registered_at,
            valid_until=m.valid_until,
            supervision=m.supervision,
            next_supervision=m.next_supervision,
            representation=m.representation,
            amount_limit=m.amount_limit,
        )
        for m in mandates
    ]
    return md.issues(infos, persons, roles, positions, day)


def _out(i: md.Issue) -> CheckOut:
    return CheckOut(
        message=i.message,
        vars=i.vars,
        kind=i.kind,
        element_id=i.element_id,
        user_id=i.user_id,
        role_id=i.role_id,
        position_id=i.position_id,
        mandate_id=i.mandate_id,
    )


async def checks(
    db: AsyncSession,
    p: Principal,
    *,
    user_id: str | None = None,
    role_id: str | None = None,
    position_id: str | None = None,
    mandate_id: str | None = None,
) -> list[CheckOut]:
    """All findings, or those concerning one person, role, position or delegation."""
    _need(p, "org:read")
    found = run_checks(await load_org(db), await elements.list_all(db, Mandate))
    return [
        _out(i)
        for i in found
        if (user_id is None or i.user_id == user_id)
        and (
            role_id is None
            or i.role_id == role_id
            or (i.kind == "role" and i.element_id == role_id)
        )
        and (position_id is None or i.position_id == position_id)
        and (mandate_id is None or i.mandate_id == mandate_id)
    ]


# ---- delegations -------------------------------------------------------------------------------


async def list_mandates(db: AsyncSession, p: Principal) -> list[MandateListItem]:
    _need(p, "org:read")
    org = await load_org(db)
    return [
        MandateListItem(
            id=m.id,
            code=m.code,
            title=m.title,
            mandate_type=m.mandate_type,
            recipient_name=org.name(m.recipient_user_id) if m.recipient_user_id else "",
            recipient_user_id=m.recipient_user_id,
            granted_by_user_id=m.granted_by_user_id,
            state=effective(m),
            is_owner=p.user_id in org.owners("mandate", m),
        )
        for m in await elements.list_all(db, Mandate)
    ]


async def mandate_view(db: AsyncSession, mandate_id: str, p: Principal) -> MandateOut:
    _need(p, "org:read")
    org = await load_org(db)
    m = await common.get_or_404(db, Mandate, mandate_id)
    found = run_checks(org, await elements.list_all(db, Mandate))
    refs = [m.recipient_user_id, m.granted_by_user_id, m.role_id, m.position_id]
    return MandateOut(
        **common.fields_of(m, MandateFields),
        id=m.id,
        custom=m.custom,
        code=m.code,
        status=m.status,
        state=effective(m),
        accepted_at=m.accepted_at,
        revoked_at=m.revoked_at,
        version=m.version,
        created_at=m.created_at,
        updated_at=m.updated_at,
        rights=common.rights("mandate", m, org, p),
        actions=MandateActions(
            can_grant=_possible(m, p, "grant"),
            can_accept=_possible(m, p, "accept"),
            can_decline=_possible(m, p, "decline"),
            can_revoke=_possible(m, p, "revoke"),
        ),
        workflow=await common.workflow_out(db, "mandate", m.id, org),
        checks=[_out(i) for i in found if i.mandate_id == m.id],
        labels={x: org.label(x) for x in refs if x},
    )


async def create_mandate(db: AsyncSession, title: str, p: Principal) -> MandateOut:
    _need(p, "org:manage")
    code = next_code(await elements.codes(db, Mandate), PREFIX)
    await elements.insert(db, Mandate(id=code, code=code, title=title))
    await audit.record(
        db, p.user_id, "create", "mandate", code, [{"key": "title", "from": None, "to": title}]
    )
    await db.commit()
    return await mandate_view(db, code, p)


async def update_mandate(
    db: AsyncSession, mandate_id: str, patch: ElementPatch, if_match: str | None, p: Principal
) -> MandateOut:
    org = await load_org(db)
    m = await common.get_or_404(db, Mandate, mandate_id)
    await common.save_element(
        db,
        "mandate",
        m,
        MandateFields,
        patch.values,
        common.expected_version(if_match, patch.version),
        p,
        org,
    )
    await db.commit()
    db.expire_all()
    return await mandate_view(db, mandate_id, p)


async def delete_mandate(db: AsyncSession, mandate_id: str, p: Principal) -> None:
    _need(p, "org:manage")
    await common.get_or_404(db, Mandate, mandate_id)
    await elements.remove(db, Mandate, mandate_id)
    await audit.record(db, p.user_id, "delete", "mandate", mandate_id)
    await db.commit()


async def mandate_workflow(
    db: AsyncSession, mandate_id: str, body: MandateAction, if_match: str | None, p: Principal
) -> MandateOut:
    m = await common.get_or_404(db, Mandate, mandate_id)
    try:
        step = md.transition(m.status, m.accepted_at is not None, body.action, _actor(m, p))
    except md.MandateError as exc:
        raise ProblemError(exc.code, exc.detail) from exc
    today = date.today()
    values: dict[str, object] = {"status": step.status}
    if step.accepted is True:
        values["accepted_at"] = today
    elif step.accepted is False:
        values["accepted_at"] = None
    if body.action == "grant" and m.valid_from is None:
        values["valid_from"] = today
    if body.action == "revoke":
        values["revoked_at"] = today
    version = common.expected_version(if_match, body.version)
    if not await elements.update_versioned(db, Mandate, m.id, version[0], values):
        raise common.stale(version[1])
    await audit.add_workflow(db, "mandate", m.id, step.step, p.user_id, body.comment, step.status)
    changes = [
        {"key": k, "from": common.jsonable(getattr(m, k)), "to": common.jsonable(v)}
        for k, v in values.items()
        if common.jsonable(getattr(m, k)) != common.jsonable(v)
    ]
    await audit.record(db, p.user_id, "workflow", "mandate", m.id, changes, step.step)
    await db.commit()
    db.expire_all()
    return await mandate_view(db, mandate_id, p)


async def history(db: AsyncSession, mandate_id: str, p: Principal) -> list[Revision]:
    _need(p, "org:read")
    return await common.revisions(db, "mandate", mandate_id, await load_org(db))


async def state(db: AsyncSession, mandate_id: str, revision_id: int, p: Principal) -> StateView:
    _need(p, "org:read")
    m = await common.get_or_404(db, Mandate, mandate_id)
    return await common.state_after(
        db,
        "mandate",
        mandate_id,
        revision_id,
        common.state_of(m, MandateFields),
        await load_org(db),
    )
