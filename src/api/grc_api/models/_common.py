"""Columns shared by all editable elements."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column


class Versioned:
    """Optimistic concurrency: every change is UPDATE … WHERE version = :v."""

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Approvable:
    """Approval workflow: draft → review (business approval given) → released; archived."""

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", server_default="draft"
    )
    doc_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="0.1", server_default="0.1"
    )
    next_review: Mapped[date | None] = mapped_column(Date)
    # released state kept while a changed draft waits for approval
    released: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


def text_col() -> Mapped[str]:
    return mapped_column(Text, nullable=False, default="", server_default="")


def str_list() -> Mapped[list[str]]:
    return mapped_column(ARRAY(String), nullable=False, default=list, server_default="{}")
