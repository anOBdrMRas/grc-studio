"""I&A cockpit: quality checks, quality grade, workflow status and review queue."""

from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.domain import audits as ad
from grc_api.domain import quality as q
from grc_api.domain import risk as rk
from grc_api.domain.bpmn import activities
from grc_api.domain.org import sod_conflicts
from grc_api.errors import ProblemError
from grc_api.models import Audit, Control, Mandate, Opportunity, Process, Risk
from grc_api.repositories import audit as audit_log
from grc_api.repositories import elements
from grc_api.repositories import processes as proc_repo
from grc_api.schemas.quality import (
    CheckItemOut,
    CheckOut,
    CockpitOut,
    ReleasedItem,
    ReviewItem,
    Situation,
    StatusCounts,
    WorkItem,
)
from grc_api.services import audits as audit_svc
from grc_api.services import mandates as mandate_svc
from grc_api.services.context import OrgData, load_org


def _label(e: object) -> str:
    return f"{getattr(e, 'code', '')} {getattr(e, 'title', '')}".strip()


async def snapshot(db: AsyncSession, org: OrgData) -> q.Snapshot:
    processes = await elements.list_all(db, Process)
    ra_by_process: dict[str, set[str]] = {}
    for s in await proc_repo.assignments(db):
        if s.raci in ("R", "A"):
            ra_by_process.setdefault(s.process_id, set()).add(s.element_id)
    controls = await elements.list_all(db, Control)
    audits = await elements.list_all(db, Audit)
    findings = await audit_svc.all_findings(db)
    today = date.today()
    audit_codes = {a.id: a.code for a in audits}
    conflicts = {a.id: len(await audit_svc.independence_of(db, a, org)) for a in audits}
    holders_of_position: dict[str, int] = {}
    for u in org.users.values():
        if u.status == "active" and u.position_id:
            holders_of_position[u.position_id] = holders_of_position.get(u.position_id, 0) + 1
    incompatible = {r.id: list(r.incompatible_role_ids) for r in org.roles.values()}
    mandate_issues = mandate_svc.run_checks(org, await elements.list_all(db, Mandate), today)
    return q.Snapshot(
        processes=[
            q.ProcessRec(
                p.id,
                _label(p),
                p.owner_role_id,
                p.description,
                p.next_review,
                tuple(activities(p.xml)),
                frozenset(ra_by_process.get(p.id, set())),
            )
            for p in processes
        ],
        roles=[
            q.RoleRec(
                r.id,
                _label(r),
                r.role_owner_user_id,
                r.responsibilities,
                r.authorities,
                len(org.role_holders(r.id)),
                r.mandatory,
                r.next_review,
            )
            for r in org.roles.values()
        ],
        positions=[
            q.PositionRec(
                p.id,
                _label(p),
                holders_of_position.get(p.id, 0),
                p.reports_to_disciplinary_id
                if p.reports_to_disciplinary_id not in (None, "", "n/a")
                else None,
                p.purpose,
                p.tasks,
                p.next_review,
                tuple(
                    (org.roles[a].title, org.roles[b].title)
                    for a, b in sod_conflicts(
                        [rid for rid, _ in org.position_roles.get(p.id, [])], incompatible
                    )
                    if a in org.roles and b in org.roles
                ),
            )
            for p in org.positions.values()
        ],
        risks=[
            q.RiskRec(
                r.id,
                _label(r),
                r.owner_user_id,
                rk.score(r.likelihood, r.impact),
                r.description,
                r.cause,
                r.department,
                r.likelihood_reason,
                r.impact_reason,
                r.treatment,
                tuple((str(a.get("text", "")), a.get("owner_user_id")) for a in r.actions),
                r.treatment_status,
                r.next_review,
            )
            for r in await elements.list_all(db, Risk)
        ],
        opportunities=[
            q.OpportunityRec(o.id, _label(o), o.owner_role_id, o.measures)
            for o in await elements.list_all(db, Opportunity)
        ],
        controls=[
            q.ControlRec(
                c.id,
                _label(c),
                c.owner_role_id,
                tuple(c.mitigates_risk_ids),
                c.operating_effectiveness,
                c.key_control,
                c.next_test,
            )
            for c in controls
        ],
        audits=[
            q.AuditRec(
                a.id,
                a.code,
                _label(a),
                a.audit_type,
                a.audit_status,
                a.start_date or a.planned_date,
                a.report_date,
                tuple(a.standards),
                a.certificate_valid_until,
                conflicts[a.id],
            )
            for a in audits
        ],
        findings=[
            q.FindingRec(
                f.audit_id,
                audit_codes.get(f.audit_id, f.audit_id),
                f.code,
                f.finding_type,
                ad.is_open(f.finding_type, f.status),
                f.due_date,
            )
            for f in findings
        ],
        users=[
            q.UserRec(u.id, u.display_name, u.status == "active", u.position_id)
            for u in org.users.values()
        ],
        org_issues=[q.OrgIssue(i.kind, i.element_id, i.message, i.vars) for i in mandate_issues],
    )


WORKFLOW_KINDS = {
    "process": Process,
    "risk": Risk,
    "opportunity": Opportunity,
}


async def cockpit(db: AsyncSession, p: Principal) -> CockpitOut:
    if not p.can("cockpit:read"):
        raise ProblemError("forbidden", "Permission cockpit:read required")
    org = await load_org(db)
    snap = await snapshot(db, org)
    found = q.checks(snap, date.today())
    collections: dict[str, list[Any]] = {
        "process": await elements.list_all(db, Process),
        "role": list(org.roles.values()),
        "position": list(org.positions.values()),
        "risk": await elements.list_all(db, Risk),
        "opportunity": await elements.list_all(db, Opportunity),
    }
    workflow: dict[str, StatusCounts] = {}
    queue: list[ReviewItem] = []
    in_work: list[WorkItem] = []
    released: list[ReleasedItem] = []
    for kind, items in collections.items():
        counts = StatusCounts(total=len(items))
        for e in items:
            setattr(counts, e.status, getattr(counts, e.status) + 1)
            entries = await audit_log.workflow(db, kind, e.id)
            owners = [org.name(u) for u in org.owners(kind, e)]
            last_approval = next((w for w in reversed(entries) if w.step == "approved"), None)
            if last_approval:
                released.append(
                    ReleasedItem(
                        kind=kind,
                        id=e.id,
                        code=e.code,
                        title=e.title,
                        doc_version=e.doc_version,
                        by=org.name(last_approval.by_user_id),
                        at=last_approval.at,
                    )
                )
            if e.status == "review":
                sub = next((w for w in reversed(entries) if w.step == "submitted"), None)
                queue.append(
                    ReviewItem(
                        kind=kind,
                        id=e.id,
                        code=e.code,
                        title=e.title,
                        submitted_by=org.name(sub.by_user_id) if sub else "",
                        submitted_at=sub.at if sub else None,
                        comment=sub.comment if sub else "",
                        owners=owners,
                        doc_version=e.doc_version,
                        version=e.version,
                    )
                )
            elif e.status == "draft":
                last = entries[-1] if entries else None
                in_work.append(
                    WorkItem(
                        kind=kind,
                        id=e.id,
                        code=e.code,
                        title=e.title,
                        owners=owners,
                        rejected=last.comment if last and last.step == "rejected" else "",
                    )
                )
        workflow[kind] = counts
    ids = {kind: [e.id for e in items] for kind, items in collections.items()}
    ids["control"] = [c.id for c in snap.controls]
    return CockpitOut(
        checks=[
            CheckOut(
                key=c.key,
                label=c.label,
                module=c.module,
                items=[
                    CheckItemOut(
                        kind=i.kind,
                        id=i.id,
                        label=i.label,
                        detail=i.detail,
                        vars=i.vars,
                        element_id=i.element_id,
                    )
                    for i in c.items
                ],
            )
            for c in found
        ],
        workflow=workflow,
        grades=q.grades(found, ids),
        review_queue=sorted(
            queue, key=lambda r: r.submitted_at.isoformat() if r.submitted_at else ""
        ),
        in_work=sorted(in_work, key=lambda w: (not w.rejected, w.kind, w.code)),
        recently_released=sorted(released, key=lambda r: r.at, reverse=True)[:10],
        situation=_situation(snap, date.today()),
    )


def _situation(snap: q.Snapshot, today: date) -> Situation:
    steps = sum(len(p.activities) for p in snap.processes)
    covered = sum(1 for p in snap.processes for el, _ in p.activities if el in p.ra_elements)
    open_findings = [f for f in snap.findings if f.open]
    by_type: dict[str, int] = {}
    for f in open_findings:
        by_type[f.finding_type] = by_type.get(f.finding_type, 0) + 1
    return Situation(
        activities=steps,
        role_coverage=round(100 * covered / steps) if steps else 100,
        findings_by_type=by_type,
        findings_open=len(open_findings),
        findings_overdue=sum(1 for f in open_findings if f.due_date and f.due_date < today),
    )
