"""Audits and findings: open/overdue findings, who may change what, auditor independence (pure)."""

from dataclasses import dataclass
from datetime import date

POSITIVE = "Positive finding"
CLOSED = "Closed"
# statuses the responsible person may set; verifying and closing stay with the auditors
RESPONSIBLE_STATUSES = frozenset({"Open", "In progress", "Implemented"})
RESPONSIBLE_FIELDS = frozenset({"root_cause", "corrective_action", "status"})


def is_open(finding_type: str, status: str) -> bool:
    return finding_type != POSITIVE and status != CLOSED


def is_overdue(finding_type: str, status: str, due: date | None, today: date) -> bool:
    return is_open(finding_type, status) and due is not None and due < today


def responsible_may_change(changes: dict[str, object]) -> bool:
    """The responsible person documents cause and action and reports progress up to 'Implemented'."""
    return set(changes) <= RESPONSIBLE_FIELDS and (
        "status" not in changes or changes["status"] in RESPONSIBLE_STATUSES
    )


@dataclass(frozen=True)
class AuditedProcess:
    id: str
    owner_role_id: str | None
    # roles that are responsible (R) or accountable (A) in one of its steps
    ra_role_ids: frozenset[str]


@dataclass(frozen=True)
class Conflict:
    user_id: str
    process_id: str
    role_id: str


def independence(
    auditors: list[str], roles_of: dict[str, set[str]], processes: list[AuditedProcess]
) -> list[Conflict]:
    """ISO 19011 4 e) / 7.2: an auditor who owns an audited process or is R/A in it audits own work."""
    out: list[Conflict] = []
    for user_id in dict.fromkeys(a for a in auditors if a):
        held = roles_of.get(user_id, set())
        for p in processes:
            if p.owner_role_id in held:
                out.append(Conflict(user_id, p.id, p.owner_role_id))
            elif hit := sorted(held & p.ra_role_ids):
                out.append(Conflict(user_id, p.id, hit[0]))
    return out
