"""GRC elements: risks and opportunities (approval workflow)."""

from datetime import date
from typing import Any

from sqlalchemy import Date, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from grc_api.db import Base
from grc_api.models._common import Approvable, Versioned, str_list, text_col


class Risk(Versioned, Approvable, Base):
    """Risk register entry (ISO 37301 4.6, ISO 27001 6.1.2, ISO 9001 6.1)."""

    __tablename__ = "risks"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    # list label: first sentence of the description (set by the service)
    title: Mapped[str] = text_col()
    description: Mapped[str] = text_col()
    department: Mapped[str] = text_col()
    category: Mapped[str] = text_col()
    activity: Mapped[str] = text_col()
    process_ids: Mapped[list[str]] = str_list()
    compliance_obligation: Mapped[str] = text_col()
    cause: Mapped[str] = text_col()
    owner_user_id: Mapped[str | None] = mapped_column(String(40))
    treatment_status: Mapped[str] = text_col()
    consequence_type: Mapped[str] = text_col()
    likelihood: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    likelihood_reason: Mapped[str] = text_col()
    impact: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    impact_reason: Mapped[str] = text_col()
    treatment: Mapped[str] = text_col()
    # [{"text": …, "owner_user_id": …}]
    actions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    assessment_reason: Mapped[str] = text_col()
    last_assessment: Mapped[date | None] = mapped_column(Date)
    review_note: Mapped[str] = text_col()
    affected_assets: Mapped[str] = text_col()
    protection_goals: Mapped[list[str]] = str_list()
    interested_parties: Mapped[str] = text_col()
    entity: Mapped[str] = text_col()
    source_ref: Mapped[str] = text_col()
    iso_refs: Mapped[list[str]] = str_list()
    created_by_user_id: Mapped[str | None] = mapped_column(String(40))


class Opportunity(Versioned, Approvable, Base):
    """Opportunity (ISO 9001 6.1, ISO 37301 6.1)."""

    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    title: Mapped[str] = text_col()
    description: Mapped[str] = text_col()
    category: Mapped[str] = text_col()
    benefit: Mapped[str] = text_col()
    likelihood: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    benefit_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    measures: Mapped[str] = text_col()
    owner_role_id: Mapped[str | None] = mapped_column(String(40))
    progress_status: Mapped[str] = text_col()
    iso_refs: Mapped[list[str]] = str_list()
    created_by_user_id: Mapped[str | None] = mapped_column(String(40))
