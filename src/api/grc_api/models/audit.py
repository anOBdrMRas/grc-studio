"""Audit log (who changed what, field by field) and the approval workflow log."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from grc_api.db import Base


class AuditEntry(Base):
    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_target", "kind", "entity_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actor_id: Mapped[str] = mapped_column(String(80), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(80), nullable=False)
    # [{"key": …, "from": …, "to": …}]
    changes: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    vars: Mapped[dict[str, str]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )


class WorkflowEntry(Base):
    __tablename__ = "workflow_entries"
    __table_args__ = (Index("ix_workflow_target", "kind", "entity_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(80), nullable=False)
    # submitted | approved | rejected | reopened | status
    step: Mapped[str] = mapped_column(String(20), nullable=False)
    by_user_id: Mapped[str] = mapped_column(String(40), nullable=False)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False)
