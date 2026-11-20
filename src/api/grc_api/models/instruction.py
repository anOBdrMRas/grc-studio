"""Work instructions: how a process step is carried out (ISO 9001 7.5 documented information)."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from grc_api.db import Base
from grc_api.models._common import Approvable, Versioned, text_col


class WorkInstruction(Versioned, Approvable, Base):
    """Owned by a person, assigned to process steps (step links of kind "instruction").

    `content` is rich text (HTML, sanitised by the API; images embedded as data URLs).
    """

    __tablename__ = "work_instructions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    title: Mapped[str] = text_col()
    description: Mapped[str] = text_col()
    owner_user_id: Mapped[str | None] = mapped_column(String(40))
    content: Mapped[str] = text_col()
