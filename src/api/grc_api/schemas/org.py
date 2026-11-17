from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from grc_api.schemas.common import PersonRef, Rights, WorkflowEntryOut


class RoleFields(BaseModel):
    title: str = ""
    description: str = ""
    role_type: str = "Functional role"
    org_unit: str = "Generic"
    mandatory: bool = False
    compliance_relevant: bool = False
    role_owner_user_id: str | None = None
    responsibilities: str = ""
    authorities: str = ""
    competencies: str = ""
    trainings: str = ""
    incompatible_role_ids: list[str] = Field(default_factory=list)
    required_mandate: str = "None"
    written_form: bool = False
    authority_notice: str = ""
    iso_refs: list[str] = Field(default_factory=list)
    last_review: date | None = None
    next_review: date | None = None


class Holder(BaseModel):
    user: PersonRef
    position_id: str
    position_title: str


class RoleOut(RoleFields):
    id: str
    code: str
    status: str
    doc_version: str
    version: int
    created_at: datetime
    updated_at: datetime
    rights: Rights
    holders: list[Holder]
    positions: list[dict[str, str]] = Field(
        description="positions holding this role: id, code, title, comment"
    )
    workflow: list[WorkflowEntryOut]
    released: dict[str, Any] | None
    labels: dict[str, str] = Field(description="display names of referenced ids")


class RoleListItem(BaseModel):
    id: str
    code: str
    title: str
    role_type: str
    mandatory: bool
    holders: list[str]
    status: str
    is_owner: bool


class PositionRoleIn(BaseModel):
    role_id: str
    comment: str = ""


class PositionFields(BaseModel):
    title: str = ""
    description: str = ""
    org_unit: str = "Generic"
    is_manager: bool = False
    headcount: int = 1
    location: str = ""
    purpose: str = ""
    tasks: str = ""
    authorities: str = ""
    signing_authority: str = "None"
    approval_limit: int = 0
    qualification: str = ""
    experience: str = ""
    competencies: str = ""
    trainings: str = ""
    screening_required: bool = False
    nda_required: bool = False
    reports_to_disciplinary_id: str | None = None
    reports_to_functional_id: str | None = None
    deputy_position_id: str | None = None
    deputy_inducted: bool = False
    iso_refs: list[str] = Field(default_factory=list)
    last_review: date | None = None
    next_review: date | None = None
    roles: list[PositionRoleIn] = Field(default_factory=list)


class PositionOut(PositionFields):
    id: str
    code: str
    status: str
    doc_version: str
    version: int
    created_at: datetime
    updated_at: datetime
    rights: Rights
    holders: list[PersonRef]
    sod_conflicts: list[list[str]] = Field(
        description="pairs of incompatible role ids on this position"
    )
    workflow: list[WorkflowEntryOut]
    released: dict[str, Any] | None
    labels: dict[str, str]


class PositionListItem(BaseModel):
    id: str
    code: str
    title: str
    org_unit: str
    holders: list[str]
    status: str
    is_owner: bool
