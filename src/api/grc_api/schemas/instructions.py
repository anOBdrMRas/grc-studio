from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from grc_api.schemas.common import Rights, WorkflowEntryOut
from grc_api.schemas.grc import Usage


class WorkInstructionFields(BaseModel):
    title: str = ""
    description: str = Field("", description="short description")
    owner_user_id: str | None = None
    content: str = Field("", description="rich text (HTML); sanitised by the API")
    next_review: date | None = None


class WorkInstructionOut(WorkInstructionFields):
    custom: dict[str, Any] = Field(default_factory=dict)
    id: str
    code: str
    status: str
    doc_version: str
    version: int
    created_at: datetime
    updated_at: datetime
    rights: Rights
    used_in: list[Usage] = Field(description="process steps the work instruction refers to")
    workflow: list[WorkflowEntryOut]
    released: dict[str, Any] | None
    labels: dict[str, str]


class WorkInstructionListItem(BaseModel):
    id: str
    code: str
    title: str
    description: str
    owner_name: str
    steps: int = Field(description="number of process steps it is assigned to")
    status: str
    doc_version: str
    is_owner: bool
