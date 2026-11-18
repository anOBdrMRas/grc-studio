from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from grc_api.schemas.common import Rights, WorkflowEntryOut

State = Literal["draft", "future", "pending", "active", "expired", "revoked"]


class MandateFields(BaseModel):
    """Editable fields. Status and acceptance are set by the approval steps only."""

    title: str = ""
    description: str = ""
    mandate_type: str = ""
    legal_basis: str = ""
    recipient_user_id: str | None = None
    granted_by_user_id: str | None = None
    granted_by_body: str = ""
    role_id: str | None = None
    position_id: str | None = None
    scope: str = ""
    powers: str = ""
    budget: str = ""
    amount_limit: int = Field(default=0, ge=0)
    representation: str = ""
    sub_delegation_allowed: bool = False
    valid_from: date | None = None
    valid_until: date | None = None
    document: str = ""
    register_entry: str = ""
    registered_at: date | None = None
    supervision: str = ""
    supervision_frequency: str = ""
    last_supervision: date | None = None
    next_supervision: date | None = None


class CheckOut(BaseModel):
    """A legal-certainty finding; `message` is an English message id, `vars` fill its placeholders."""

    message: str
    vars: dict[str, str]
    kind: Literal["role", "position", "mandate"]
    element_id: str
    user_id: str | None
    role_id: str | None
    position_id: str | None
    mandate_id: str | None


class MandateActions(BaseModel):
    can_grant: bool
    can_accept: bool
    can_decline: bool
    can_revoke: bool


class MandateOut(MandateFields):
    custom: dict[str, Any] = Field(
        default_factory=dict, description="values of the custom fields (content administration)"
    )
    id: str
    code: str
    status: str
    state: State = Field(description="effective state: granted, valid and accepted")
    accepted_at: date | None
    revoked_at: date | None
    version: int
    created_at: datetime
    updated_at: datetime
    rights: Rights
    actions: MandateActions
    workflow: list[WorkflowEntryOut]
    checks: list[CheckOut]
    labels: dict[str, str]


class MandateListItem(BaseModel):
    id: str
    code: str
    title: str
    mandate_type: str
    recipient_name: str
    recipient_user_id: str | None
    granted_by_user_id: str | None
    state: State
    is_owner: bool


class MandateAction(BaseModel):
    action: Literal["grant", "accept", "decline", "revoke"]
    comment: str = ""
    version: int | None = None
