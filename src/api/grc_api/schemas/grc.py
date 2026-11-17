from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from grc_api.schemas.common import Rights, WorkflowEntryOut

Level = Literal["low", "medium", "high"]


class RiskAction(BaseModel):
    """Treatment action with the person responsible for it."""

    text: str = Field(default="", max_length=2000)
    owner_user_id: str | None = None


class RiskFields(BaseModel):
    """Editable fields of a risk. The title is derived from the first sentence of the description."""

    description: str = ""
    department: str = ""
    category: str = ""
    activity: str = ""
    process_ids: list[str] = Field(default_factory=list)
    compliance_obligation: str = ""
    cause: str = Field(default="", description="cause and consequence")
    owner_user_id: str | None = None
    treatment_status: str = "Identified"
    consequence_type: str = ""
    likelihood: int = Field(default=0, ge=0, le=4, description="0 = not assessed, 1..4")
    likelihood_reason: str = ""
    impact: int = Field(default=0, ge=0, le=4, description="0 = not assessed, 1..4")
    impact_reason: str = ""
    treatment: str = ""
    actions: list[RiskAction] = Field(default_factory=list)
    assessment_reason: str = ""
    last_assessment: date | None = None
    next_review: date | None = None
    review_note: str = ""
    affected_assets: str = ""
    protection_goals: list[str] = Field(default_factory=list)
    interested_parties: str = ""
    entity: str = ""
    source_ref: str = ""
    iso_refs: list[str] = Field(default_factory=list)


class Assessment(BaseModel):
    score: int = Field(description="likelihood × impact (0 while not assessed)")
    level: Level
    high: bool = Field(description="higher risk: needs treatment or documented acceptance")


class RiskOut(RiskFields):
    id: str
    code: str
    title: str
    status: str
    doc_version: str
    version: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    assessment: Assessment
    rights: Rights
    workflow: list[WorkflowEntryOut]
    released: dict[str, Any] | None
    labels: dict[str, str] = Field(description="display names of referenced ids")


class RiskListItem(BaseModel):
    id: str
    code: str
    title: str
    department: str
    owner_name: str
    likelihood: int
    impact: int
    score: int
    level: Level
    treatment_status: str
    status: str
    is_owner: bool


class OpportunityFields(BaseModel):
    title: str = ""
    description: str = ""
    category: str = ""
    progress_status: str = "Identified"
    owner_role_id: str | None = None
    benefit: str = ""
    likelihood: int = Field(default=0, ge=0, le=5)
    benefit_score: int = Field(default=0, ge=0, le=5)
    measures: str = ""
    next_review: date | None = None
    iso_refs: list[str] = Field(default_factory=list)


class OpportunityOut(OpportunityFields):
    id: str
    code: str
    status: str
    doc_version: str
    version: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    potential: int = Field(description="likelihood × benefit")
    rights: Rights
    workflow: list[WorkflowEntryOut]
    released: dict[str, Any] | None
    labels: dict[str, str]


class OpportunityListItem(BaseModel):
    id: str
    code: str
    title: str
    category: str
    owner_role_title: str
    potential: int
    progress_status: str
    status: str
    is_owner: bool
