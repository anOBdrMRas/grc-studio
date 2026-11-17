"""Delegations: approval steps, effective state, legal-certainty checks."""

from datetime import date

import pytest

from grc_api.domain import mandates as md

TODAY = date(2026, 11, 17)
GRANTOR = md.Actor("U-1", is_grantor=True, is_recipient=False, can_manage=False)
RECIPIENT = md.Actor("U-2", is_grantor=False, is_recipient=True, can_manage=False)
OTHER = md.Actor("U-3", is_grantor=False, is_recipient=False, can_manage=False)
MANAGER = md.Actor("U-4", is_grantor=False, is_recipient=False, can_manage=True)


def test_grant_accept_flow() -> None:
    assert md.transition("draft", False, "grant", GRANTOR).status == "granted"
    step = md.transition("granted", False, "accept", RECIPIENT)
    assert (step.status, step.accepted) == ("granted", True)


@pytest.mark.parametrize(
    ("status", "accepted", "action", "actor", "code"),
    [
        ("draft", False, "grant", OTHER, "forbidden"),
        ("draft", False, "accept", RECIPIENT, "workflow_state"),
        ("granted", False, "accept", GRANTOR, "forbidden"),
        ("granted", True, "accept", RECIPIENT, "workflow_state"),
        ("granted", False, "decline", OTHER, "forbidden"),
        ("revoked", True, "revoke", MANAGER, "workflow_state"),
        ("granted", True, "revoke", RECIPIENT, "forbidden"),
    ],
)
def test_refused_steps(
    status: str, accepted: bool, action: str, actor: md.Actor, code: str
) -> None:
    with pytest.raises(md.MandateError) as e:
        md.transition(status, accepted, action, actor)  # type: ignore[arg-type]
    assert e.value.code == code


def test_decline_returns_to_draft_and_revoke() -> None:
    step = md.transition("granted", True, "decline", RECIPIENT)
    assert (step.status, step.accepted) == ("draft", False)
    assert md.transition("granted", True, "revoke", MANAGER).status == "revoked"


@pytest.mark.parametrize(
    ("status", "valid_from", "valid_until", "accepted_at", "expected"),
    [
        ("draft", None, None, None, "draft"),
        ("revoked", None, None, TODAY, "revoked"),
        ("granted", None, date(2026, 1, 1), TODAY, "expired"),
        ("granted", date(2026, 12, 1), None, TODAY, "future"),
        ("granted", None, None, None, "pending"),
        ("granted", date(2026, 1, 1), None, date(2026, 1, 2), "active"),
    ],
)
def test_state(
    status: str,
    valid_from: date | None,
    valid_until: date | None,
    accepted_at: date | None,
    expected: str,
) -> None:
    assert md.state(status, valid_from, valid_until, accepted_at, TODAY) == expected


def mandate(**kw: object) -> md.MandateInfo:
    base: dict[str, object] = {
        "id": "DV-1",
        "label": "DV-1 Test",
        "mandate_type": "Appointment / designation",
        "state": "active",
        "recipient_user_id": "U-2",
        "role_id": "RO-1",
        "document": "doc",
        "registered_at": TODAY,
        "valid_until": None,
        "supervision": "yes",
        "next_supervision": None,
        "representation": "",
        "amount_limit": 0,
    }
    return md.MandateInfo(**(base | kw))  # type: ignore[arg-type]


PERSONS = {"U-2": md.PersonInfo("U-2", "Anna", True, "ST-1")}
ROLE = md.RoleInfo("RO-1", "DPO", "Appointment / designation", True, "Authority", ("U-2",))
POS = md.PositionInfo("ST-1", "Buyer", "Commercial power of attorney", 10000, ("U-2",))


def messages(found: list[md.Issue]) -> list[str]:
    return [i.message for i in found]


def test_role_without_mandate() -> None:
    found = md.issues([], PERSONS, [ROLE], [], TODAY)
    assert messages(found) == ["{role}: {user} has no effective {type}."]
    assert found[0].role_id == "RO-1"


def test_role_mandate_without_document_and_notice() -> None:
    found = md.issues([mandate(document="", registered_at=None)], PERSONS, [ROLE], [], TODAY)
    assert set(messages(found)) == {
        "{role}: {type} for {user} without a written document.",
        "{role}: notification to {authority} for {user} not documented.",
    }


def test_pending_and_expired() -> None:
    assert messages(md.issues([mandate(state="pending")], PERSONS, [ROLE], [], TODAY))[0] == (
        "{role}: {user} has not accepted the {type}."
    )
    assert messages(md.issues([mandate(state="expired")], PERSONS, [ROLE], [], TODAY))[0] == (
        "{role}: the {type} for {user} has expired."
    )


def test_mandate_findings() -> None:
    m = mandate(
        mandate_type="Prokura (general commercial power)",
        role_id=None,
        next_supervision=date(2026, 1, 1),
        valid_until=date(2026, 12, 1),
        amount_limit=50000,
    )
    found = messages(md.issues([m], PERSONS, [], [POS], TODAY))
    assert "{mandate}: supervision overdue (due {date})." in found
    assert "{mandate}: expires on {date}." in found
    assert "{mandate}: exceeds the target power of attorney of the position {position}." in found
    assert (
        "{mandate}: amount limit {amount} EUR above the limit of the position ({limit} EUR)."
        in found
    )


def test_leaver_and_sole_payment_authority() -> None:
    persons = {"U-2": md.PersonInfo("U-2", "Anna", False, None)}
    m = mandate(
        mandate_type="Bank / payment authority", representation="Sole representation", role_id=None
    )
    found = messages(md.issues([m], persons, [], [], TODAY))
    assert "{mandate}: {user} has left or is inactive – revoke it." in found
    assert "{mandate}: sole authority for payments – four-eyes principle not ensured." in found


def test_position_target_power_missing() -> None:
    found = md.issues([], PERSONS, [], [POS], TODAY)
    assert messages(found) == ["Position {position} provides for {type}, {user} has none."]
    ok = mandate(mandate_type="Commercial power of attorney", role_id=None)
    assert md.issues([ok], PERSONS, [], [POS], TODAY) == []
