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


LinkKind = Literal["risk", "opportunity", "control", "kpi"]


class StepLinkOut(BaseModel):
    kind: LinkKind
    target_id: str
    code: str
    title: str


class IcsGap(BaseModel):
    """A risk of the step without a mitigating control in the same step."""

    risk_id: str
    suggestions: list[str] = Field(description="controls mitigating the risk elsewhere")


class ProcessOut(ProcessFields):
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
        description="element id → risks, opportunities, controls and KPI"
    )
    ics_gaps: dict[str, list[IcsGap]] = Field(description="element id → risks without control")
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


class StepRoleIn(BaseModel):
    role_id: str
    raci: str = Field(default="R", pattern="^[RACI]$")
    version: int | None = None
