"""Audits and their findings with corrective actions."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.domain import audits as ad
from grc_api.domain.codes import next_code
from grc_api.errors import ProblemError
from grc_api.models import Audit, AuditFinding, Process
from grc_api.repositories import audit as audit_log
from grc_api.repositories import elements
from grc_api.repositories import processes as proc_repo
from grc_api.schemas.audits import (
    AuditFields,
    AuditListItem,
    AuditOut,
    FindingCreate,
    FindingFields,
    FindingOut,
    Independence,
)
from grc_api.schemas.common import ElementPatch, Revision, StateView
from grc_api.services import common
from grc_api.services.context import OrgData, load_org


def _need(p: Principal, perm: str) -> None:
    if not p.can(perm):
        raise ProblemError("forbidden", f"Permission {perm} required")


async def _findings(db: AsyncSession, audit_id: str | None = None) -> list[AuditFinding]:
    stmt = select(AuditFinding).order_by(AuditFinding.code)
    if audit_id:
        stmt = stmt.where(AuditFinding.audit_id == audit_id)
    return list((await db.execute(stmt)).scalars())


def _is_responsible(f: AuditFinding, org: OrgData, p: Principal) -> bool:
    return f.responsible_user_id == p.user_id or (
        f.responsible_role_id is not None and f.responsible_role_id in org.roles_of(p.user_id)
    )


def _finding_out(f: AuditFinding, can_edit_audit: bool, org: OrgData, p: Principal) -> FindingOut:
    today = date.today()
    return FindingOut(
        **common.fields_of(f, FindingFields),
        id=f.id,
        code=f.code,
        version=f.version,
        open=ad.is_open(f.finding_type, f.status),
        overdue=ad.is_overdue(f.finding_type, f.status, f.due_date, today),
        can_edit=can_edit_audit,
        is_responsible=_is_responsible(f, org, p),
    )


async def _independence(db: AsyncSession, a: Audit, org: OrgData) -> list[Independence]:
    processes = []
    labels = {}
    for pid in a.process_ids:
        x = await elements.get(db, Process, pid)
        if x is None:
            continue
        labels[x.id] = f"{x.code} {x.title}"
        ra = frozenset(
            s.role_id for s in await proc_repo.assignments(db, x.id) if s.raci in ("R", "A")
        )
        processes.append(ad.AuditedProcess(x.id, x.owner_role_id, ra))
    auditors = [a.lead_auditor_user_id or "", *a.team_user_ids]
    found = ad.independence(auditors, {u: org.roles_of(u) for u in auditors if u}, processes)
    return [
        Independence(
            user_id=c.user_id,
            user_name=org.name(c.user_id),
            process_id=c.process_id,
            process_label=labels.get(c.process_id, c.process_id),
            role_label=org.label(c.role_id),
        )
        for c in found
    ]


async def list_audits(db: AsyncSession, p: Principal) -> list[AuditListItem]:
    _need(p, "grc:read")
    org = await load_org(db)
    open_by_audit: dict[str, int] = {}
    for f in await _findings(db):
        if ad.is_open(f.finding_type, f.status):
            open_by_audit[f.audit_id] = open_by_audit.get(f.audit_id, 0) + 1
    return [
        AuditListItem(
            id=a.id,
            code=a.code,
            title=a.title,
            audit_type=a.audit_type,
            audit_status=a.audit_status,
            when=a.start_date or a.planned_date,
            open_findings=open_by_audit.get(a.id, 0),
            is_owner=p.user_id in org.owners("audit", a),
        )
        for a in await elements.list_all(db, Audit)
    ]


async def audit_view(db: AsyncSession, audit_id: str, p: Principal) -> AuditOut:
    _need(p, "grc:read")
    org = await load_org(db)
    a = await common.get_or_404(db, Audit, audit_id)
    rights = common.rights("audit", a, org, p)
    findings = await _findings(db, a.id)
    people = [a.lead_auditor_user_id, a.auditee_contact_user_id, *a.team_user_ids]
    people += [x for f in findings for x in (f.responsible_user_id, f.verified_by_user_id)]
    roles = [*a.audited_role_ids, *(f.responsible_role_id for f in findings)]
    processes = {x.id: f"{x.code} {x.title}" for x in await elements.list_all(db, Process)}
    labels = {x: org.label(x) for x in [*people, *roles] if x}
    labels |= {
        x: processes.get(x, x) for x in [*a.process_ids, *(f.process_id for f in findings)] if x
    }
    return AuditOut(
        **common.fields_of(a, AuditFields),
        id=a.id,
        code=a.code,
        version=a.version,
        created_at=a.created_at,
        updated_at=a.updated_at,
        rights=rights,
        findings=[_finding_out(f, rights.can_edit, org, p) for f in findings],
        independence=await _independence(db, a, org),
        labels=labels,
    )


async def create_audit(db: AsyncSession, title: str, p: Principal) -> AuditOut:
    _need(p, "grc:manage")
    code = next_code(await elements.codes(db, Audit), "AU")
    await elements.insert(
        db, Audit(id=code, code=code, title=title, program_year=str(date.today().year))
    )
    await audit_log.record(
        db, p.user_id, "create", "audit", code, [{"key": "title", "from": None, "to": title}]
    )
    await db.commit()
    return await audit_view(db, code, p)


async def update_audit(
    db: AsyncSession, audit_id: str, patch: ElementPatch, if_match: str | None, p: Principal
) -> AuditOut:
    org = await load_org(db)
    a = await common.get_or_404(db, Audit, audit_id)
    await common.save_element(
        db,
        "audit",
        a,
        AuditFields,
        patch.values,
        common.expected_version(if_match, patch.version),
        p,
        org,
    )
    await db.commit()
    db.expire_all()
    return await audit_view(db, audit_id, p)


async def delete_audit(db: AsyncSession, audit_id: str, p: Principal) -> None:
    _need(p, "grc:manage")
    await common.get_or_404(db, Audit, audit_id)
    await elements.remove(db, Audit, audit_id)
    await audit_log.record(db, p.user_id, "delete", "audit", audit_id)
    await db.commit()


# ---- findings ----------------------------------------------------------------------------------


async def _audit_rights(
    db: AsyncSession, audit_id: str, p: Principal
) -> tuple[Audit, OrgData, bool]:
    org = await load_org(db)
    a = await common.get_or_404(db, Audit, audit_id)
    return a, org, common.rights("audit", a, org, p).can_edit


async def create_finding(
    db: AsyncSession, audit_id: str, body: FindingCreate, p: Principal
) -> AuditOut:
    a, _, can_edit = await _audit_rights(db, audit_id, p)
    if not can_edit:
        raise ProblemError("forbidden", "Only the auditors record findings")
    code = next_code(await elements.codes(db, AuditFinding), "F")
    await elements.insert(
        db, AuditFinding(id=code, code=code, audit_id=a.id, description=body.description)
    )
    await audit_log.record(
        db,
        p.user_id,
        "update",
        "audit",
        a.id,
        [{"key": f"finding {code}", "from": None, "to": body.description}],
        "Finding {code} recorded",
        {"code": code},
    )
    await db.commit()
    return await audit_view(db, a.id, p)


async def update_finding(
    db: AsyncSession,
    audit_id: str,
    finding_id: str,
    patch: ElementPatch,
    if_match: str | None,
    p: Principal,
) -> AuditOut:
    a, org, can_edit = await _audit_rights(db, audit_id, p)
    f = await common.get_or_404(db, AuditFinding, finding_id)
    if f.audit_id != a.id:
        raise ProblemError("not_found", "Finding not found")
    before = common.fields_of(f, FindingFields)
    after = common.validate_merge(FindingFields, before, patch.values)
    changed = {k: v for k, v in after.items() if before.get(k) != v}
    if not changed:
        return await audit_view(db, a.id, p)
    if not can_edit and not (_is_responsible(f, org, p) and ad.responsible_may_change(changed)):
        raise ProblemError("forbidden", "You may not change this finding")
    version = common.expected_version(if_match, patch.version)
    values = {k: common.to_column(FindingFields, k, v) for k, v in changed.items()}
    if not await elements.update_versioned(db, AuditFinding, f.id, version[0], values):
        raise common.stale(version[1])
    await audit_log.record(
        db,
        p.user_id,
        "update",
        "audit",
        a.id,
        [{"key": f"{f.code}: {k}", "from": before.get(k), "to": v} for k, v in changed.items()],
        "Finding {code} changed",
        {"code": f.code},
    )
    await db.commit()
    db.expire_all()
    return await audit_view(db, a.id, p)


async def delete_finding(
    db: AsyncSession, audit_id: str, finding_id: str, p: Principal
) -> AuditOut:
    a, _, can_edit = await _audit_rights(db, audit_id, p)
    f = await common.get_or_404(db, AuditFinding, finding_id)
    if f.audit_id != a.id:
        raise ProblemError("not_found", "Finding not found")
    if not can_edit:
        raise ProblemError("forbidden", "Only the auditors delete findings")
    await elements.remove(db, AuditFinding, f.id)
    await audit_log.record(
        db, p.user_id, "update", "audit", a.id, [], "Finding {code} deleted", {"code": f.code}
    )
    await db.commit()
    db.expire_all()
    return await audit_view(db, a.id, p)


async def history(db: AsyncSession, audit_id: str, p: Principal) -> list[Revision]:
    _need(p, "grc:read")
    return await common.revisions(db, "audit", audit_id, await load_org(db))


async def state(db: AsyncSession, audit_id: str, revision_id: int, p: Principal) -> StateView:
    _need(p, "grc:read")
    a = await common.get_or_404(db, Audit, audit_id)
    return await common.state_after(
        db, "audit", audit_id, revision_id, common.fields_of(a, AuditFields), await load_org(db)
    )


async def all_findings(db: AsyncSession) -> list[AuditFinding]:
    return await _findings(db)
