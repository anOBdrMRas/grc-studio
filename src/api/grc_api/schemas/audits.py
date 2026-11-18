from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from grc_api.schemas.common import Rights


class AuditFields(BaseModel):
    title: str = ""
    description: str = ""
    audit_type: str = ""
    cert_stage: str = ""
    program_year: str = ""
    audit_status: str = "Planned"
    standards: list[str] = Field(default_factory=list)
    objective: str = ""
    criteria: list[str] = Field(default_factory=list, description="ISO clause ids")
    process_ids: list[str] = Field(default_factory=list)
    audited_role_ids: list[str] = Field(default_factory=list)
    sites: str = ""
    lead_auditor_user_id: str | None = None
    external_lead_auditor: str = ""
    team_user_ids: list[str] = Field(default_factory=list)
    external_org: str = ""
    auditee_contact_user_id: str | None = None
    planned_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    report_date: date | None = None
    report_document: str = ""
    certificate_valid_until: date | None = None
    next_audit_due: date | None = None
    verdict: str = ""
    summary: str = ""
    strengths: str = ""


class FindingFields(BaseModel):
    finding_type: str = "Observation"
    clause: str = ""
    description: str = ""
    evidence: str = ""
    process_id: str | None = None
    element_id: str = ""
    risk_ids: list[str] = Field(default_factory=list)
    control_ids: list[str] = Field(default_factory=list)
    responsible_role_id: str | None = None
    responsible_user_id: str | None = None
    root_cause: str = ""
    corrective_action: str = ""
    due_date: date | None = None
    status: str = "Open"
    verified_at: date | None = None
    verified_by_user_id: str | None = None
    verification_result: str = ""


class FindingOut(FindingFields):
    id: str
    code: str
    version: int
    open: bool
    overdue: bool
    can_edit: bool = Field(description="may change every field (auditors, I&A)")
    is_responsible: bool = Field(description="may document cause, action and progress")


class Independence(BaseModel):
    user_id: str
    user_name: str
    process_id: str
    process_label: str
    role_label: str


class AuditOut(AuditFields):
    custom: dict[str, Any] = Field(
        default_factory=dict, description="values of the custom fields (content administration)"
    )
    id: str
    code: str
    version: int
    created_at: datetime
    updated_at: datetime
    rights: Rights
    findings: list[FindingOut]
    independence: list[Independence]
    labels: dict[str, str]


class AuditListItem(BaseModel):
    id: str
    code: str
    title: str
    audit_type: str
    audit_status: str
    when: date | None = Field(description="start date, else planned date")
    open_findings: int
    is_owner: bool


class FindingCreate(BaseModel):
    description: str = Field(default="", max_length=4000)
