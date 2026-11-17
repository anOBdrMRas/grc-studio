from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from grc_api.schemas.common import Rights, WorkflowEntryOut

Level = Literal["low", "medium", "high"]


class Usage(BaseModel):
    """A process step the element is assigned to."""

    process_id: str
    process_label: str
    element_id: str
    element_name: str


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
    used_in: list[Usage]
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
    actions: list[RiskAction]
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
    used_in: list[Usage]
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


class ControlFields(BaseModel):
    title: str = ""
    description: str = ""
    objective: str = ""
    key_control: bool = False
    control_type: str = ""
    automation: str = ""
    frequency: str = ""
    owner_role_id: str | None = None
    executor_role_id: str | None = None
    evidence: str = ""
    mitigates_risk_ids: list[str] = Field(default_factory=list)
    annex_a: list[str] = Field(default_factory=list, description="ISO 27001 Annex A clause ids")
    soa_applicable: str = ""
    implementation: str = ""
    soa_justification: str = ""
    test_method: str = ""
    design_effectiveness: str = "Not tested"
    operating_effectiveness: str = "Not tested"
    last_test: date | None = None
    next_test: date | None = None
    test_result: str = ""
    iso_refs: list[str] = Field(default_factory=list)


class ControlOut(ControlFields):
    id: str
    code: str
    version: int
    created_at: datetime
    updated_at: datetime
    rights: Rights
    used_in: list[Usage]
    labels: dict[str, str]


class ControlListItem(BaseModel):
    id: str
    code: str
    title: str
    control_type: str
    key_control: bool
    operating_effectiveness: str
    is_owner: bool


Traffic = Literal["green", "yellow", "red", "none"]


class KpiFields(BaseModel):
    title: str = ""
    description: str = ""
    objective: str = ""
    formula: str = ""
    unit: str = ""
    direction: str = Field(default="higher", pattern="^(higher|lower)$")
    target: float = 0
    warning: float = 0
    critical: float = 0
    frequency: str = ""
    data_source: str = ""
    owner_role_id: str | None = None
    evaluator_role_id: str | None = None
    iso_refs: list[str] = Field(default_factory=list)


class Measurement(BaseModel):
    date: date
    value: float


class MeasurementIn(Measurement):
    pass


class KpiOut(KpiFields):
    id: str
    code: str
    version: int
    created_at: datetime
    updated_at: datetime
    measurements: list[Measurement]
    traffic: Traffic = Field(description="traffic light of the latest value")
    can_measure: bool = Field(description="may record measured values")
    rights: Rights
    used_in: list[Usage]
    labels: dict[str, str]


class KpiListItem(BaseModel):
    id: str
    code: str
    title: str
    unit: str
    last_value: float | None
    traffic: Traffic = Field(description="traffic light of the latest value")
    is_owner: bool
