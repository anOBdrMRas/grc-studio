"""Quality checks of the integrated management system (I&A cockpit) – pure.

Each check has a stable key, an English message id as label, the module it belongs to and the
elements it found. A detail with `vars` (possibly empty) is a message id the interface translates;
without `vars` it is shown as it is (a date, a score, a code).
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

from grc_api.domain import risk as rk

HIGH = rk.HIGH_ABOVE


@dataclass(frozen=True)
class Item:
    kind: str
    id: str
    label: str
    detail: str = ""
    vars: dict[str, str] | None = None
    element_id: str = ""


@dataclass
class Check:
    key: str
    label: str
    module: str
    items: list[Item] = field(default_factory=list)


@dataclass(frozen=True)
class ProcessRec:
    id: str
    label: str
    owner_role_id: str | None
    description: str
    next_review: date | None
    activities: tuple[tuple[str, str], ...]  # (element id, name)
    ra_elements: frozenset[str]  # steps with a role that is R or A


@dataclass(frozen=True)
class RoleRec:
    id: str
    label: str
    owner_user_id: str | None
    responsibilities: str
    authorities: str
    holders: int
    mandatory: bool
    next_review: date | None


@dataclass(frozen=True)
class PositionRec:
    id: str
    label: str
    holders: int
    reports_to: str | None
    purpose: str
    tasks: str
    next_review: date | None
    sod: tuple[tuple[str, str], ...]  # pairs of incompatible role titles


@dataclass(frozen=True)
class RiskRec:
    id: str
    label: str
    owner_user_id: str | None
    score: int
    description: str
    cause: str
    department: str
    likelihood_reason: str
    impact_reason: str
    treatment: str
    actions: tuple[tuple[str, str | None], ...]  # (text, owner)
    treatment_status: str
    next_review: date | None


@dataclass(frozen=True)
class OpportunityRec:
    id: str
    label: str
    owner_role_id: str | None
    measures: str


@dataclass(frozen=True)
class ControlRec:
    id: str
    label: str
    owner_role_id: str | None
    mitigates: tuple[str, ...]
    operating_effectiveness: str
    key_control: bool
    next_test: date | None


@dataclass(frozen=True)
class AuditRec:
    id: str
    code: str
    label: str
    audit_type: str
    audit_status: str
    when: date | None
    report_date: date | None
    standards: tuple[str, ...]
    certificate_valid_until: date | None
    independence_conflicts: int


@dataclass(frozen=True)
class FindingRec:
    audit_id: str
    audit_code: str
    code: str
    finding_type: str
    open: bool
    due_date: date | None


@dataclass(frozen=True)
class UserRec:
    id: str
    label: str
    active: bool
    position_id: str | None


@dataclass(frozen=True)
class OrgIssue:
    """A legal-certainty finding (domain.mandates) to show in the cockpit."""

    kind: str
    id: str
    message: str
    vars: dict[str, str]


@dataclass
class Snapshot:
    processes: list[ProcessRec]
    roles: list[RoleRec]
    positions: list[PositionRec]
    risks: list[RiskRec]
    opportunities: list[OpportunityRec]
    controls: list[ControlRec]
    audits: list[AuditRec]
    findings: list[FindingRec]
    users: list[UserRec]
    org_issues: list[OrgIssue]


def _filled(s: str) -> bool:
    return bool(s and s.strip())


def checks(d: Snapshot, today: date) -> list[Check]:
    in90, in180 = today + timedelta(days=90), today + timedelta(days=180)
    mitigated = {r for c in d.controls for r in c.mitigates}
    return [
        # processes
        Check(
            "proc-owner",
            "Processes without a process owner",
            "process",
            [Item("process", p.id, p.label) for p in d.processes if not p.owner_role_id],
        ),
        Check(
            "proc-content",
            "Processes without purpose & scope",
            "process",
            [Item("process", p.id, p.label) for p in d.processes if not _filled(p.description)],
        ),
        Check(
            "proc-steps",
            "Process steps without responsibility (R/A)",
            "process",
            [
                Item("process", p.id, f"{p.label} › {name}", element_id=el)
                for p in d.processes
                for el, name in p.activities
                if el not in p.ra_elements
            ],
        ),
        # roles
        Check(
            "role-owner",
            "Roles without a role owner",
            "role",
            [Item("role", r.id, r.label) for r in d.roles if not r.owner_user_id],
        ),
        Check(
            "role-content",
            "Roles without responsibilities or authorities",
            "role",
            [
                Item("role", r.id, r.label)
                for r in d.roles
                if not _filled(r.responsibilities) or not _filled(r.authorities)
            ],
        ),
        Check(
            "role-holder",
            "Roles without a holder",
            "role",
            [
                Item(
                    "role",
                    r.id,
                    r.label,
                    "Mandatory role" if r.mandatory else "",
                    {} if r.mandatory else None,
                )
                for r in d.roles
                if r.holders == 0
            ],
        ),
        Check(
            "role-mandate",
            "Mandatory roles without an effective transfer",
            "role",
            [
                Item("role", i.id, i.vars.get("role", i.id), i.message, i.vars)
                for i in d.org_issues
                if i.kind == "role"
            ],
        ),
        Check(
            "sod",
            "Segregation of duties conflicts",
            "role",
            [Item("position", p.id, p.label, f"{a} + {b}") for p in d.positions for a, b in p.sod],
        ),
        # positions
        Check(
            "pos-empty",
            "Vacant positions",
            "position",
            [Item("position", p.id, p.label) for p in d.positions if p.holders == 0],
        ),
        Check(
            "pos-owner",
            "Positions without a superior (no owner)",
            "position",
            [Item("position", p.id, p.label) for p in d.positions if not p.reports_to],
        ),
        Check(
            "pos-content",
            "Positions without purpose or main tasks",
            "position",
            [
                Item("position", p.id, p.label)
                for p in d.positions
                if not _filled(p.purpose) or not _filled(p.tasks)
            ],
        ),
        # risks
        Check(
            "risk-owner",
            "Risks without a risk owner",
            "risk",
            [Item("risk", r.id, r.label) for r in d.risks if not r.owner_user_id],
        ),
        Check(
            "risk-control",
            "Risks without a mitigating control",
            "risk",
            [
                Item("risk", r.id, r.label)
                for r in d.risks
                if r.treatment_status != "Closed" and r.id not in mitigated
            ],
        ),
        Check(
            "risk-high",
            "Higher risks (> 8)",
            "risk",
            [Item("risk", r.id, r.label, str(r.score)) for r in d.risks if r.score > HIGH],
        ),
        Check(
            "risk-content",
            "Risks without description or cause and consequence",
            "risk",
            [
                Item("risk", r.id, r.label)
                for r in d.risks
                if not _filled(r.description) or not _filled(r.cause)
            ],
        ),
        Check(
            "risk-reason",
            "Risks without department or reasons for the assessment",
            "risk",
            [
                Item("risk", r.id, r.label)
                for r in d.risks
                if not _filled(r.department)
                or not _filled(r.likelihood_reason)
                or not _filled(r.impact_reason)
            ],
        ),
        Check(
            "risk-treat",
            "Higher risks (> 8) without actions or responsible persons",
            "risk",
            [
                Item("risk", r.id, r.label, str(r.score))
                for r in d.risks
                if r.score > HIGH
                and r.treatment != "Accept"
                and (
                    not any(_filled(t) for t, _ in r.actions)
                    or any(_filled(t) and not o for t, o in r.actions)
                )
            ],
        ),
        # opportunities
        Check(
            "opp-owner",
            "Opportunities without a responsible role",
            "opportunity",
            [Item("opportunity", o.id, o.label) for o in d.opportunities if not o.owner_role_id],
        ),
        Check(
            "opp-measures",
            "Opportunities without measures to seize them",
            "opportunity",
            [
                Item("opportunity", o.id, o.label)
                for o in d.opportunities
                if not _filled(o.measures)
            ],
        ),
        # controls
        Check(
            "ctl-owner",
            "Controls without a control owner",
            "control",
            [Item("control", c.id, c.label) for c in d.controls if not c.owner_role_id],
        ),
        Check(
            "ctl-risk",
            "Controls without a risk addressed",
            "control",
            [Item("control", c.id, c.label) for c in d.controls if not c.mitigates],
        ),
        Check(
            "ctl-weak",
            "Controls not (fully) effective or not tested",
            "control",
            [
                Item("control", c.id, c.label, c.operating_effectiveness or "Not tested", {})
                for c in d.controls
                if c.operating_effectiveness != "Effective"
            ],
        ),
        Check(
            "ctl-key",
            "Key controls not effective",
            "control",
            [
                Item("control", c.id, c.label, c.operating_effectiveness or "Not tested", {})
                for c in d.controls
                if c.key_control and c.operating_effectiveness != "Effective"
            ],
        ),
        # reviews
        Check(
            "review",
            "Overdue reviews",
            "other",
            [
                *(
                    Item("process", p.id, p.label, p.next_review.isoformat())
                    for p in d.processes
                    if p.next_review and p.next_review < today
                ),
                *(
                    Item("role", r.id, r.label, r.next_review.isoformat())
                    for r in d.roles
                    if r.next_review and r.next_review < today
                ),
                *(
                    Item("position", p.id, p.label, p.next_review.isoformat())
                    for p in d.positions
                    if p.next_review and p.next_review < today
                ),
                *(
                    Item("risk", r.id, r.label, r.next_review.isoformat())
                    for r in d.risks
                    if r.next_review and r.next_review < today
                ),
                *(
                    Item("control", c.id, c.label, c.next_test.isoformat())
                    for c in d.controls
                    if c.next_test and c.next_test < today
                ),
            ],
        ),
        # audits and certificates
        Check(
            "audit-upcoming",
            "Upcoming audits (90 days)",
            "audit",
            [
                Item("audit", a.id, a.label, a.when.isoformat())
                for a in sorted(d.audits, key=lambda x: x.when or date.max)
                if a.audit_status not in ("Completed", "Cancelled")
                and a.when is not None
                and today <= a.when <= in90
            ],
        ),
        Check(
            "audit-findings-open",
            "Open audit findings",
            "audit",
            [
                Item("audit", f.audit_id, f"{f.audit_code} · {f.code}", f.finding_type, {})
                for f in d.findings
                if f.open
            ],
        ),
        Check(
            "audit-findings-overdue",
            "Overdue audit findings",
            "audit",
            [
                Item("audit", f.audit_id, f"{f.audit_code} · {f.code}", f.due_date.isoformat())
                for f in d.findings
                if f.open and f.due_date and f.due_date < today
            ],
        ),
        Check(
            "audit-cert",
            "Certificates expired or expiring (< 180 days)",
            "audit",
            _certificates(d, today, in180),
        ),
        Check(
            "audit-report",
            "Conducted audits without a report",
            "audit",
            [
                Item("audit", a.id, a.label, a.when.isoformat() if a.when else "")
                for a in d.audits
                if a.audit_status == "Conducted" and not a.report_date
            ],
        ),
        Check(
            "audit-independence",
            "Audits where auditors audit their own work",
            "audit",
            [
                Item("audit", a.id, a.label, str(a.independence_conflicts))
                for a in d.audits
                if a.independence_conflicts
            ],
        ),
        # delegations and persons
        Check(
            "mandate",
            "Delegations & powers of attorney requiring action",
            "mandate",
            [
                Item(
                    i.kind,
                    i.id,
                    i.vars.get("mandate") or i.vars.get("position", i.id),
                    i.message,
                    i.vars,
                )
                for i in d.org_issues
                if i.kind in ("mandate", "position")
            ],
        ),
        Check(
            "user-nopos",
            "Active users without a position",
            "user",
            [Item("user", u.id, u.label) for u in d.users if u.active and not u.position_id],
        ),
        Check(
            "user-inactive",
            "Inactive users with a position",
            "user",
            [Item("user", u.id, u.label) for u in d.users if not u.active and u.position_id],
        ),
    ]


def _certificates(d: Snapshot, today: date, until: date) -> list[Item]:
    """Only the most recent certificate per standard counts."""
    certs = [
        a for a in d.audits if a.audit_type == "Certification audit" and a.certificate_valid_until
    ]
    latest = [
        a
        for a in certs
        if not any(
            b is not a
            and b.certificate_valid_until
            and a.certificate_valid_until
            and b.certificate_valid_until > a.certificate_valid_until
            and set(b.standards) & set(a.standards)
            for b in certs
        )
    ]
    out = []
    for a in latest:
        valid = a.certificate_valid_until
        if valid is None or valid > until:
            continue
        label = f"{', '.join(a.standards)} – {a.label}"
        if valid < today:
            out.append(Item("audit", a.id, label, "expired on {date}", {"date": valid.isoformat()}))
        else:
            out.append(Item("audit", a.id, label, valid.isoformat()))
    return out


GRADED = ("process", "role", "position", "risk", "opportunity", "control")


def grades(found: list[Check], ids: dict[str, list[str]]) -> dict[str, int]:
    """Share (in %) of the elements of a module without a quality finding."""
    out: dict[str, int] = {}
    for module in GRADED:
        hit = {
            i.id
            for c in found
            if c.module == module or c.key == "review"
            for i in c.items
            if i.kind == module
        }
        all_ids = ids.get(module, [])
        out[module] = (
            round((len(all_ids) - len([x for x in all_ids if x in hit])) / len(all_ids) * 100)
            if all_ids
            else 100
        )
    return out
