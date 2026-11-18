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


class CockpitOut(BaseModel):
    checks: list[CheckOut]
    workflow: dict[str, StatusCounts] = Field(description="module → elements per status")
    grades: dict[str, int] = Field(description="module → % of elements without findings")
    review_queue: list[ReviewItem]
