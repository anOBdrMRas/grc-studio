from datetime import datetime

from pydantic import BaseModel, Field


class CheckItemOut(BaseModel):
    kind: str
    id: str
    label: str
    detail: str
    vars: dict[str, str] | None = Field(
        description="when set, `detail` is a message id to translate with these values"
    )
    element_id: str


class CheckOut(BaseModel):
    key: str
    label: str = Field(description="English message id")
    module: str
    items: list[CheckItemOut]


class StatusCounts(BaseModel):
    draft: int = 0
    review: int = 0
    released: int = 0
    archived: int = 0
    total: int = 0


class ReviewItem(BaseModel):
    kind: str
    id: str
    code: str
    title: str
    submitted_by: str
    submitted_at: datetime | None
    comment: str = Field("", description="comment of the business approval")
    owners: list[str] = Field(default_factory=list, description="names of the owners")
    doc_version: str = ""
    version: int = Field(0, description="row version, for approving or rejecting")


class WorkItem(BaseModel):
    """A draft with its owners; `rejected` holds the reason when the I&A team sent it back."""

    kind: str
    id: str
    code: str
    title: str
    owners: list[str]
    rejected: str = ""


class ReleasedItem(BaseModel):
    kind: str
    id: str
    code: str
    title: str
    doc_version: str
    by: str
    at: datetime


class Situation(BaseModel):
    """Figures for the GRC situation picture that the element lists do not carry."""

    activities: int = Field(description="activities in all process diagrams")
    role_coverage: int = Field(description="% of activities with a role that is R or A")
    findings_by_type: dict[str, int]
    findings_open: int
    findings_overdue: int


class CockpitOut(BaseModel):
    checks: list[CheckOut]
    workflow: dict[str, StatusCounts] = Field(description="module → elements per status")
    grades: dict[str, int] = Field(description="module → % of elements without findings")
    review_queue: list[ReviewItem]
    in_work: list[WorkItem] = Field(description="drafts at their owners, rejected first")
    recently_released: list[ReleasedItem] = Field(description="latest ten I&A approvals")
    situation: Situation
