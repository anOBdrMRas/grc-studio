"""Approval workflow: draft → business approval (owner) → I&A review → released.

The functions decide; the services persist. A transition returns the new status and version.
"""

from dataclasses import dataclass
from typing import Literal

Stage = Literal["draft", "review", "released", "archived"]
Action = Literal["submit", "approve", "reject", "set_status"]


class WorkflowError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class Actor:
    user_id: str
    is_owner: bool
    can_manage: bool
    can_approve: bool
    can_set_status: bool


@dataclass(frozen=True)
class Transition:
    status: Stage
    doc_version: str
    step: str
    clears_released: bool = False


def bump(version: str, ever_released: bool) -> str:
    """First release is 1.0, later ones 1.1, 1.2 …"""
    try:
        n = float(version.replace(",", "."))
    except ValueError:
        return "1.0"
    if not ever_released and n < 1:
        return "1.0"
    return f"{round(n + 0.1, 1):.1f}"


def transition(
    status: Stage,
    action: Action,
    actor: Actor,
    doc_version: str,
    *,
    ever_released: bool,
    submitted_by: str | None,
    comment: str = "",
    target: Stage | None = None,
) -> Transition:
    if action == "submit":
        if status != "draft":
            raise WorkflowError("workflow_state", "Only a draft can be submitted")
        if not (actor.is_owner or actor.can_manage):
            raise WorkflowError("forbidden", "Only the owner gives the business approval")
        return Transition("review", doc_version, "submitted")
    if action in ("approve", "reject"):
        if status != "review":
            raise WorkflowError("workflow_state", "The element is not in the I&A review")
        if not actor.can_approve:
            raise WorkflowError("forbidden", "Only the I&A team gives the quality approval")
        if submitted_by == actor.user_id:
            raise WorkflowError("four_eyes", "Four-eyes principle: you gave the business approval")
        if action == "reject":
            if not comment.strip():
                raise WorkflowError("invalid", "A comment is required to send it back")
            return Transition("draft", doc_version, "rejected")
        return Transition(
            "released", bump(doc_version, ever_released), "approved", clears_released=True
        )
    if not actor.can_set_status:
        raise WorkflowError("forbidden", "Only the administration sets the status")
    if target is None:
        raise WorkflowError("invalid", "Target status missing")
    return Transition(target, doc_version, "status")


def reopens(status: Stage, can_manage: bool) -> bool:
    """A released element edited by its owner goes back to draft; managers (admin, I&A) keep it released."""
    return status == "released" and not can_manage
