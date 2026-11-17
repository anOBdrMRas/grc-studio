"""Approval workflow rules (pure domain)."""

import pytest

from grc_api.domain.workflow import Actor, WorkflowError, bump, reopens, transition

OWNER = Actor("U-1", is_owner=True, can_manage=False, can_approve=False, can_set_status=False)
IA = Actor("U-2", is_owner=False, can_manage=True, can_approve=True, can_set_status=True)
ADMIN = Actor("U-3", is_owner=False, can_manage=True, can_approve=False, can_set_status=True)
OTHER = Actor("U-4", is_owner=False, can_manage=False, can_approve=False, can_set_status=False)


def test_first_release_is_1_0_then_minor_steps() -> None:
    assert bump("0.1", ever_released=False) == "1.0"
    assert bump("1.0", ever_released=True) == "1.1"
    assert bump("1.9", ever_released=True) == "2.0"
    assert bump("x", ever_released=False) == "1.0"


def test_owner_submits_draft() -> None:
    t = transition("draft", "submit", OWNER, "0.1", ever_released=False, submitted_by=None)
    assert (t.status, t.step) == ("review", "submitted")


def test_stranger_cannot_submit() -> None:
    with pytest.raises(WorkflowError) as e:
        transition("draft", "submit", OTHER, "0.1", ever_released=False, submitted_by=None)
    assert e.value.code == "forbidden"


def test_only_ia_approves_and_version_is_bumped() -> None:
    t = transition("review", "approve", IA, "0.1", ever_released=False, submitted_by="U-1")
    assert (t.status, t.doc_version, t.clears_released) == ("released", "1.0", True)
    with pytest.raises(WorkflowError) as e:
        transition("review", "approve", ADMIN, "0.1", ever_released=False, submitted_by="U-1")
    assert e.value.code == "forbidden"


def test_four_eyes_principle() -> None:
    with pytest.raises(WorkflowError) as e:
        transition("review", "approve", IA, "0.1", ever_released=False, submitted_by=IA.user_id)
    assert e.value.code == "four_eyes"


def test_send_back_needs_comment() -> None:
    with pytest.raises(WorkflowError):
        transition(
            "review", "reject", IA, "0.1", ever_released=False, submitted_by="U-1", comment=" "
        )
    t = transition(
        "review",
        "reject",
        IA,
        "0.1",
        ever_released=False,
        submitted_by="U-1",
        comment="Bitte ergänzen",
    )
    assert t.status == "draft"


def test_set_status_needs_permission_and_target() -> None:
    assert (
        transition(
            "draft",
            "set_status",
            ADMIN,
            "0.1",
            ever_released=False,
            submitted_by=None,
            target="archived",
        ).status
        == "archived"
    )
    with pytest.raises(WorkflowError):
        transition(
            "draft",
            "set_status",
            OWNER,
            "0.1",
            ever_released=False,
            submitted_by=None,
            target="released",
        )
    with pytest.raises(WorkflowError):
        transition("draft", "set_status", ADMIN, "0.1", ever_released=False, submitted_by=None)


def test_wrong_state() -> None:
    with pytest.raises(WorkflowError) as e:
        transition("released", "submit", OWNER, "1.0", ever_released=True, submitted_by=None)
    assert e.value.code == "workflow_state"


def test_owner_edit_reopens_released() -> None:
    assert reopens("released", can_manage=False)
    assert not reopens("released", can_manage=True)
    assert not reopens("draft", can_manage=False)
