from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PersonRef(BaseModel):
    id: str
    name: str


class WorkflowEntryOut(BaseModel):
    step: str
    by_user_id: str
    by_name: str
    at: datetime
    comment: str
    status: str


class Rights(BaseModel):
    """What the signed-in person may do with this element (decided by the API)."""

    can_edit: bool
    can_manage: bool
    can_delete: bool
    is_owner: bool
    can_submit: bool
    can_approve: bool
    can_set_status: bool
    owner_fields: list[str] = Field(description="fields only managers may change")


class Change(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key: str
    from_: Any = Field(default=None, alias="from")
    to: Any = None


class Revision(BaseModel):
    id: int
    at: datetime
    actor_id: str
    actor_name: str
    action: str
    changes: list[Change]
    note: str
    vars: dict[str, str]


class ElementPatch(BaseModel):
    """Changed fields; the version is checked (If-Match header or this field)."""

    version: int | None = None
    values: dict[str, Any]


class WorkflowAction(BaseModel):
    action: str = Field(pattern="^(submit|approve|reject|set_status)$")
    comment: str = ""
    target_status: str | None = Field(default=None, pattern="^(draft|review|released|archived)$")
    version: int | None = None


class CreateElement(BaseModel):
    title: str = Field("", max_length=300, description="may be empty: the form opens next")


class StateView(BaseModel):
    """Fields of an element right after a recorded change (read-only)."""

    revision_id: int
    at: datetime
    actor_name: str
    values: dict[str, Any]
