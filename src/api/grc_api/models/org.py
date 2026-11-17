"""Organisation: persons, roles, positions and the roles of a position."""

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from grc_api.db import Base
from grc_api.models._common import Approvable, Versioned, str_list, text_col


class User(Versioned, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    last_name: Mapped[str] = text_col()
    first_name: Mapped[str] = text_col()
    # "first name last name", kept for lists and references
    display_name: Mapped[str] = text_col()
    division: Mapped[str] = text_col()
    department: Mapped[str] = text_col()
    position_id: Mapped[str | None] = mapped_column(String(40))
    position_since: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str] = text_col()
    system_roles: Mapped[list[str]] = str_list()
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    email: Mapped[str] = text_col()
    # local accounts (prepared; demo sign-in needs none)
    username: Mapped[str | None] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str | None] = mapped_column(Text)
    failed_logins: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )


class Role(Versioned, Approvable, Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    title: Mapped[str] = text_col()
    description: Mapped[str] = text_col()
    role_type: Mapped[str] = text_col()
    org_unit: Mapped[str] = text_col()
    mandatory: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    compliance_relevant: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    role_owner_user_id: Mapped[str | None] = mapped_column(String(40))
    responsibilities: Mapped[str] = text_col()
    authorities: Mapped[str] = text_col()
    competencies: Mapped[str] = text_col()
    trainings: Mapped[str] = text_col()
    incompatible_role_ids: Mapped[list[str]] = str_list()
    required_mandate: Mapped[str] = text_col()
    written_form: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    authority_notice: Mapped[str] = text_col()
    iso_refs: Mapped[list[str]] = str_list()
    last_review: Mapped[date | None] = mapped_column(Date)


class Position(Versioned, Approvable, Base):
    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    title: Mapped[str] = text_col()
    description: Mapped[str] = text_col()
    org_unit: Mapped[str] = text_col()
    is_manager: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    headcount: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    location: Mapped[str] = text_col()
    purpose: Mapped[str] = text_col()
    tasks: Mapped[str] = text_col()
    authorities: Mapped[str] = text_col()
    signing_authority: Mapped[str] = text_col()
    approval_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    qualification: Mapped[str] = text_col()
    experience: Mapped[str] = text_col()
    competencies: Mapped[str] = text_col()
    trainings: Mapped[str] = text_col()
    screening_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    nda_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    reports_to_disciplinary_id: Mapped[str | None] = mapped_column(String(40))
    reports_to_functional_id: Mapped[str | None] = mapped_column(String(40))
    deputy_position_id: Mapped[str | None] = mapped_column(String(40))
    deputy_inducted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    iso_refs: Mapped[list[str]] = str_list()
    last_review: Mapped[date | None] = mapped_column(Date)


class PositionRole(Base):
    __tablename__ = "position_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    position_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("positions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    comment: Mapped[str] = text_col()
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


class Mandate(Versioned, Base):
    """Delegation or power of attorney given to a person (appointment, delegation of duties, Prokura …).

    Its approval is its own: granted by the grantor, accepted by the recipient (see domain.mandates).
    """

    __tablename__ = "mandates"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    title: Mapped[str] = text_col()
    description: Mapped[str] = text_col()
    mandate_type: Mapped[str] = text_col()
    legal_basis: Mapped[str] = text_col()
    recipient_user_id: Mapped[str | None] = mapped_column(String(40), index=True)
    granted_by_user_id: Mapped[str | None] = mapped_column(String(40))
    granted_by_body: Mapped[str] = text_col()
    role_id: Mapped[str | None] = mapped_column(String(40))
    position_id: Mapped[str | None] = mapped_column(String(40))
    scope: Mapped[str] = text_col()
    powers: Mapped[str] = text_col()
    budget: Mapped[str] = text_col()
    amount_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    representation: Mapped[str] = text_col()
    sub_delegation_allowed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # draft → granted → (accepted_at set) … revoked
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", server_default="draft"
    )
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    revoked_at: Mapped[date | None] = mapped_column(Date)
    document: Mapped[str] = text_col()
    accepted_at: Mapped[date | None] = mapped_column(Date)
    register_entry: Mapped[str] = text_col()
    registered_at: Mapped[date | None] = mapped_column(Date)
    supervision: Mapped[str] = text_col()
    supervision_frequency: Mapped[str] = text_col()
    last_supervision: Mapped[date | None] = mapped_column(Date)
    next_supervision: Mapped[date | None] = mapped_column(Date)
