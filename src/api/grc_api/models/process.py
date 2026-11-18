"""Processes (BPMN) and the roles assigned to their steps."""

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from grc_api.db import Base
from grc_api.models._common import Approvable, Versioned, str_list, text_col


class Process(Versioned, Approvable, Base):
    __tablename__ = "processes"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    title: Mapped[str] = text_col()
    description: Mapped[str] = text_col()
    category: Mapped[str] = text_col()
    owner_role_id: Mapped[str | None] = mapped_column(String(40))
    area: Mapped[str] = text_col()
    landscape_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    inputs: Mapped[str] = text_col()
    outputs: Mapped[str] = text_col()
    resources: Mapped[str] = text_col()
    standards: Mapped[list[str]] = str_list()
    xml: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    # call activities of the diagram → called process (element id → process id)
    call_links: Mapped[dict[str, str]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )


class StepAssignment(Base):
    """A role taking part in a process step, with its RACI letter."""

    __tablename__ = "step_assignments"
    __table_args__ = (UniqueConstraint("process_id", "element_id", "role_id", name="uq_step_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    process_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    element_id: Mapped[str] = mapped_column(String(120), nullable=False)
    role_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    raci: Mapped[str] = mapped_column(String(1), nullable=False, default="R", server_default="R")
