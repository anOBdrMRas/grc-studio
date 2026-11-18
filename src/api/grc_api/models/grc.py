"""GRC elements: risks and opportunities (approval workflow), controls, KPI and step links."""

from datetime import date
from typing import Any

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, UniqueConstraint
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


class Control(Versioned, Base):
    """Internal control (ICS), Statement of Applicability (ISO 27001 Annex A). No approval workflow."""

    __tablename__ = "controls"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    title: Mapped[str] = text_col()
    description: Mapped[str] = text_col()
    objective: Mapped[str] = text_col()
    key_control: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    control_type: Mapped[str] = text_col()
    automation: Mapped[str] = text_col()
    frequency: Mapped[str] = text_col()
    owner_role_id: Mapped[str | None] = mapped_column(String(40))
    executor_role_id: Mapped[str | None] = mapped_column(String(40))
    evidence: Mapped[str] = text_col()
    mitigates_risk_ids: Mapped[list[str]] = str_list()
    annex_a: Mapped[list[str]] = str_list()
    soa_applicable: Mapped[str] = text_col()
    implementation: Mapped[str] = text_col()
    soa_justification: Mapped[str] = text_col()
    test_method: Mapped[str] = text_col()
    design_effectiveness: Mapped[str] = text_col()
    operating_effectiveness: Mapped[str] = text_col()
    last_test: Mapped[date | None] = mapped_column(Date)
    next_test: Mapped[date | None] = mapped_column(Date)
    test_result: Mapped[str] = text_col()
    iso_refs: Mapped[list[str]] = str_list()


class Kpi(Versioned, Base):
    """Key performance indicator (ISO 9001 6.2 / 9.1, ISO 27001 9.1, ISO 37301 9.1)."""

    __tablename__ = "kpis"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    title: Mapped[str] = text_col()
    description: Mapped[str] = text_col()
    objective: Mapped[str] = text_col()
    formula: Mapped[str] = text_col()
    unit: Mapped[str] = text_col()
    # "higher": bigger is better, "lower": smaller is better
    direction: Mapped[str] = mapped_column(
        String(10), nullable=False, default="higher", server_default="higher"
    )
    target: Mapped[float] = mapped_column(Float, nullable=False, default=0, server_default="0")
    warning: Mapped[float] = mapped_column(Float, nullable=False, default=0, server_default="0")
    critical: Mapped[float] = mapped_column(Float, nullable=False, default=0, server_default="0")
    frequency: Mapped[str] = text_col()
    data_source: Mapped[str] = text_col()
    owner_role_id: Mapped[str | None] = mapped_column(String(40))
    evaluator_role_id: Mapped[str | None] = mapped_column(String(40))
    iso_refs: Mapped[list[str]] = str_list()


class KpiMeasurement(Base):
    """One measured value of a KPI; one value per date."""

    __tablename__ = "kpi_measurements"
    __table_args__ = (UniqueConstraint("kpi_id", "date", name="uq_kpi_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kpi_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("kpis.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    by_user_id: Mapped[str | None] = mapped_column(String(40))


class StepLink(Base):
    """A risk, opportunity, control or KPI assigned to a process step (BPMN element)."""

    __tablename__ = "step_links"
    __table_args__ = (
        UniqueConstraint("process_id", "element_id", "kind", "target_id", name="uq_step_link"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    process_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("processes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    element_id: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[str] = mapped_column(String(40), nullable=False, index=True)


class Audit(Versioned, Base):
    """Audit (ISO 19011; ISO 9001 / 27001 / 37301 9.2; certification audits after ISO/IEC 17021-1).

    `audit_status` is the planning status of the audit, not the approval workflow.
    """

    __tablename__ = "audits"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    title: Mapped[str] = text_col()
    description: Mapped[str] = text_col()
    audit_type: Mapped[str] = text_col()
    cert_stage: Mapped[str] = text_col()
    program_year: Mapped[str] = text_col()
    audit_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="Planned", server_default="Planned"
    )
    standards: Mapped[list[str]] = str_list()
    objective: Mapped[str] = text_col()
    criteria: Mapped[list[str]] = str_list()
    process_ids: Mapped[list[str]] = str_list()
    audited_role_ids: Mapped[list[str]] = str_list()
    sites: Mapped[str] = text_col()
    lead_auditor_user_id: Mapped[str | None] = mapped_column(String(40))
    external_lead_auditor: Mapped[str] = text_col()
    team_user_ids: Mapped[list[str]] = str_list()
    external_org: Mapped[str] = text_col()
    auditee_contact_user_id: Mapped[str | None] = mapped_column(String(40))
    planned_date: Mapped[date | None] = mapped_column(Date)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    report_date: Mapped[date | None] = mapped_column(Date)
    report_document: Mapped[str] = text_col()
    certificate_valid_until: Mapped[date | None] = mapped_column(Date)
    next_audit_due: Mapped[date | None] = mapped_column(Date)
    verdict: Mapped[str] = text_col()
    summary: Mapped[str] = text_col()
    strengths: Mapped[str] = text_col()


class AuditFinding(Versioned, Base):
    """Finding of an audit with its corrective action (ISO 9001 10.2, ISO 19011 6.4.8)."""

    __tablename__ = "audit_findings"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    audit_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    finding_type: Mapped[str] = text_col()
    clause: Mapped[str] = text_col()
    description: Mapped[str] = text_col()
    evidence: Mapped[str] = text_col()
    process_id: Mapped[str | None] = mapped_column(String(40))
    element_id: Mapped[str] = text_col()
    risk_ids: Mapped[list[str]] = str_list()
    control_ids: Mapped[list[str]] = str_list()
    responsible_role_id: Mapped[str | None] = mapped_column(String(40))
    responsible_user_id: Mapped[str | None] = mapped_column(String(40))
    root_cause: Mapped[str] = text_col()
    corrective_action: Mapped[str] = text_col()
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="Open", server_default="Open"
    )
    verified_at: Mapped[date | None] = mapped_column(Date)
    verified_by_user_id: Mapped[str | None] = mapped_column(String(40))
    verification_result: Mapped[str] = text_col()
