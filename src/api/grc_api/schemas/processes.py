from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from grc_api.schemas.common import Rights, WorkflowEntryOut


class ProcessFields(BaseModel):
    title: str = ""
    description: str = ""
    category: str = "Core process"
    owner_role_id: str | None = None
    area: str = ""
    landscape_order: int = 0
    inputs: str = ""
    outputs: str = ""
    resources: str = ""
    standards: list[str] = Field(default_factory=list)
    next_review: date | None = None


class StepRole(BaseModel):
    role_id: str
    code: str
    title: str
    raci: str


LinkKind = Literal["instruction", "risk", "opportunity", "control", "kpi"]


class StepLinkOut(BaseModel):
    kind: LinkKind
    target_id: str
    code: str
    title: str


class IcsGap(BaseModel):
    """A risk of the step without a mitigating control in the same step."""

    risk_id: str
    suggestions: list[str] = Field(description="controls mitigating the risk elsewhere")


class ProcessRef(BaseModel):
    process_id: str
    code: str
    title: str


class CallerRef(ProcessRef):
    element_id: str
    element_name: str


class CallLinkIn(BaseModel):
    target_process_id: str | None = Field(None, description="None removes the link")
    version: int | None = None


class ProcessOut(ProcessFields):
    custom: dict[str, Any] = Field(
        default_factory=dict, description="values of the custom fields (content administration)"
    )
    id: str
    code: str
    status: str
    doc_version: str
    version: int
    created_at: datetime
    updated_at: datetime
    rights: Rights
    owners: list[str]
    steps: dict[str, list[StepRole]] = Field(description="element id → roles with RACI")
    links: dict[str, list[StepLinkOut]] = Field(
        description="element id → work instructions, risks, opportunities, controls and KPI"
    )
    ics_gaps: dict[str, list[IcsGap]] = Field(description="element id → risks without control")
    activities: dict[str, str] = Field(
        default_factory=dict, description="activities of the diagram (steps): element id → name"
    )
    step_notes: dict[str, str] = Field(
        default_factory=dict, description="element id → description of the step"
    )
    call_activities: dict[str, str] = Field(description="call activities: element id → name")
    calls: dict[str, ProcessRef] = Field(description="call activity → called process")
    called_by: list[CallerRef] = Field(
        description="call activities of other processes calling this"
    )
    workflow: list[WorkflowEntryOut]
    released: dict[str, Any] | None
    labels: dict[str, str]


class ProcessListItem(BaseModel):
    id: str
    code: str
    title: str
    category: str
    area: str
    landscape_order: int
    status: str
    owner_role_title: str
    is_owner: bool
    my_steps: int = Field(0, description="steps where the person holds an assigned role")


class DiagramOut(BaseModel):
    xml: str
    version: int


class DiagramIn(BaseModel):
    xml: str = Field(min_length=20, max_length=5_000_000)
    version: int | None = None


class StepLinkIn(BaseModel):
    kind: LinkKind
    target_id: str
    version: int | None = None


class StepNoteIn(BaseModel):
    text: str = Field("", max_length=20000, description="description of the step; empty removes it")
    version: int | None = None


class StepRoleIn(BaseModel):
    role_id: str
    raci: str = Field(default="R", pattern="^[RACI]$")
    version: int | None = None
