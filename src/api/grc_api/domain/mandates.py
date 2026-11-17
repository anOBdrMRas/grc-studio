"""Delegations and powers of attorney: approval steps, effective state and legal-certainty checks (pure).

A mandate is granted by the grantor and becomes effective only when the recipient has accepted it
and it is within its validity. The checks compare the mandates with the roles that need a formal
transfer, with the target powers of positions and with the persons' situation.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

Status = Literal["draft", "granted", "revoked"]
State = Literal["draft", "future", "pending", "active", "expired", "revoked"]
Action = Literal["grant", "accept", "decline", "revoke"]

DUTY_DELEGATION = "Delegation of duties"
PAYMENT_AUTHORITY = "Bank / payment authority"
DEPUTY = "Deputy"
SOLE = "Sole representation"
# powers of attorney that can be compared with the target authority of a position
POWER_RANK = {
    "None": 0,
    "Commercial power of attorney": 1,
    "Prokura (general commercial power)": 2,
    "Statutory representation (officer)": 3,
}
GRANTABLE_TARGETS = ("Commercial power of attorney", "Prokura (general commercial power)")
EXPIRY_WARNING = timedelta(days=60)


class MandateError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class Actor:
    user_id: str
    is_grantor: bool
    is_recipient: bool
    can_manage: bool


@dataclass(frozen=True)
class Step:
    status: Status
    step: str
    accepted: bool | None = None  # True: set accepted_at, False: clear it, None: keep


def transition(status: Status, accepted: bool, action: Action, actor: Actor) -> Step:
    """Grant (grantor or management), accept or decline (recipient), revoke (grantor or management)."""
    if action == "grant":
        if status != "draft":
            raise MandateError("workflow_state", "Only a draft can be granted")
        if not (actor.is_grantor or actor.can_manage):
            raise MandateError("forbidden", "Only the grantor grants the mandate")
        return Step("granted", "granted")
    if action in ("accept", "decline"):
        if status != "granted":
            raise MandateError("workflow_state", "The mandate has not been granted")
        if action == "accept":
            if not actor.is_recipient:
                raise MandateError("forbidden", "Only the recipient accepts the mandate")
            if accepted:
                raise MandateError("workflow_state", "The mandate is already accepted")
            return Step("granted", "accepted", accepted=True)
        if not (actor.is_recipient or actor.is_grantor or actor.can_manage):
            raise MandateError("forbidden", "Only the persons involved return the mandate")
        return Step("draft", "declined", accepted=False)
    if status == "revoked":
        raise MandateError("workflow_state", "The mandate is already revoked")
    if not (actor.is_grantor or actor.can_manage):
        raise MandateError("forbidden", "Only the grantor revokes the mandate")
    return Step("revoked", "revoked")


def state(
    status: str,
    valid_from: date | None,
    valid_until: date | None,
    accepted_at: date | None,
    today: date,
) -> State:
    """Effective state: granted, within its validity and accepted by the recipient."""
    if status == "revoked":
        return "revoked"
    if status != "granted":
        return "draft"
    if valid_until and valid_until < today:
        return "expired"
    if valid_from and valid_from > today:
        return "future"
    if not accepted_at:
        return "pending"
    return "active"


LIVE: frozenset[State] = frozenset({"active", "pending", "future"})


# ---- legal-certainty checks ---------------------------------------------------------------------


@dataclass(frozen=True)
class MandateInfo:
    id: str
    label: str
    mandate_type: str
    state: State
    recipient_user_id: str | None
    role_id: str | None
    document: str
    registered_at: date | None
    valid_until: date | None
    supervision: str
    next_supervision: date | None
    representation: str
    amount_limit: int


@dataclass(frozen=True)
class PersonInfo:
    id: str
    name: str
    active: bool
    position_id: str | None


@dataclass(frozen=True)
class RoleInfo:
    id: str
    title: str
    required_mandate: str
    written_form: bool
    authority_notice: str
    holders: tuple[str, ...]


@dataclass(frozen=True)
class PositionInfo:
    id: str
    title: str
    signing_authority: str
    approval_limit: int
    holders: tuple[str, ...]


@dataclass(frozen=True)
class Issue:
    """A finding; `message` is an English message id with {placeholders} filled from `vars`."""

    message: str
    kind: Literal["role", "position", "mandate"]
    element_id: str
    vars: dict[str, str] = field(default_factory=dict)
    user_id: str | None = None
    role_id: str | None = None
    position_id: str | None = None
    mandate_id: str | None = None


def issues(
    mandates: list[MandateInfo],
    persons: dict[str, PersonInfo],
    roles: list[RoleInfo],
    positions: list[PositionInfo],
    today: date,
) -> list[Issue]:
    out: list[Issue] = []
    name = {p.id: p.name for p in persons.values()}

    # roles that need a formal transfer: every holder needs an effective mandate
    for role in roles:
        if not role.required_mandate or role.required_mandate == "None":
            continue
        for uid in role.holders:
            own = [
                m
                for m in mandates
                if m.role_id == role.id
                and m.recipient_user_id == uid
                and m.mandate_type == role.required_mandate
            ]
            v = {"role": role.title, "user": name.get(uid, uid), "type": role.required_mandate}

            def on_role(message: str, extra: dict[str, str], mandate: MandateInfo | None) -> Issue:
                return Issue(
                    message,
                    kind="role",
                    element_id=role.id,  # noqa: B023 - used right away
                    vars=v | extra,  # noqa: B023
                    user_id=uid,  # noqa: B023
                    role_id=role.id,  # noqa: B023
                    mandate_id=mandate.id if mandate else None,
                )

            by_state = {m.state: m for m in reversed(own)}
            if active := by_state.get("active"):
                if role.written_form and not active.document:
                    out.append(
                        on_role("{role}: {type} for {user} without a written document.", {}, active)
                    )
                if role.authority_notice and not active.registered_at:
                    out.append(
                        on_role(
                            "{role}: notification to {authority} for {user} not documented.",
                            {"authority": role.authority_notice},
                            active,
                        )
                    )
            elif pending := by_state.get("pending"):
                out.append(on_role("{role}: {user} has not accepted the {type}.", {}, pending))
            elif expired := by_state.get("expired"):
                out.append(on_role("{role}: the {type} for {user} has expired.", {}, expired))
            else:
                out.append(on_role("{role}: {user} has no effective {type}.", {}, None))

    role_holders = {r.id: set(r.holders) for r in roles}
    pos_by_id = {p.id: p for p in positions}
    for m in mandates:
        if m.state not in LIVE:
            continue
        person = persons.get(m.recipient_user_id or "")
        v = {"mandate": m.label, "user": person.name if person else ""}

        def on_mandate(message: str, extra: dict[str, str] | None = None) -> Issue:
            return Issue(
                message,
                kind="mandate",
                element_id=m.id,  # noqa: B023 - used right away
                vars=v | (extra or {}),  # noqa: B023
                user_id=m.recipient_user_id,  # noqa: B023
                role_id=m.role_id,  # noqa: B023
                mandate_id=m.id,  # noqa: B023
            )

        if person is None:
            out.append(on_mandate("{mandate}: no recipient set."))
            continue
        if not person.active:
            out.append(on_mandate("{mandate}: {user} has left or is inactive – revoke it."))
        if m.state == "active" and m.valid_until and m.valid_until <= today + EXPIRY_WARNING:
            out.append(
                on_mandate("{mandate}: expires on {date}.", {"date": m.valid_until.isoformat()})
            )
        if m.state == "active" and m.next_supervision and m.next_supervision < today:
            out.append(
                on_mandate(
                    "{mandate}: supervision overdue (due {date}).",
                    {"date": m.next_supervision.isoformat()},
                )
            )
        if m.state == "active" and m.mandate_type == DUTY_DELEGATION and not m.supervision:
            out.append(on_mandate("{mandate}: delegation of duties without defined supervision."))
        if m.mandate_type == PAYMENT_AUTHORITY and m.representation == SOLE:
            out.append(
                on_mandate(
                    "{mandate}: sole authority for payments – four-eyes principle not ensured."
                )
            )
        if (
            m.role_id in role_holders
            and person.id not in role_holders[m.role_id]
            and m.mandate_type != DEPUTY
        ):
            out.append(
                on_mandate("{mandate}: {user} no longer holds the role (change of position?).")
            )
        pos = pos_by_id.get(person.position_id or "")
        if pos is None:
            continue
        if POWER_RANK.get(m.mandate_type, -1) > POWER_RANK.get(pos.signing_authority, 0):
            out.append(
                on_mandate(
                    "{mandate}: exceeds the target power of attorney of the position {position}.",
                    {"position": pos.title},
                )
            )
        if pos.approval_limit > 0 and m.amount_limit > pos.approval_limit:
            out.append(
                on_mandate(
                    "{mandate}: amount limit {amount} EUR above the limit of the position ({limit} EUR).",
                    {"amount": str(m.amount_limit), "limit": str(pos.approval_limit)},
                )
            )

    # positions: their target power of attorney must be granted to every holder
    for p in positions:
        if p.signing_authority not in GRANTABLE_TARGETS:
            continue
        for uid in p.holders:
            has = any(
                m.recipient_user_id == uid
                and m.mandate_type == p.signing_authority
                and m.state in LIVE
                for m in mandates
            )
            if not has:
                out.append(
                    Issue(
                        "Position {position} provides for {type}, {user} has none.",
                        kind="position",
                        element_id=p.id,
                        position_id=p.id,
                        user_id=uid,
                        vars={
                            "position": p.title,
                            "type": p.signing_authority,
                            "user": name.get(uid, uid),
                        },
                    )
                )
    return out
