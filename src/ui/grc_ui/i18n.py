"""gettext catalogues (.po), compiled in memory at start. The message id is the English text."""

import logging
from contextvars import ContextVar
from functools import lru_cache
from pathlib import Path

from babel.messages.pofile import read_po

LOCALE_DIR = Path(__file__).with_name("locale")
LANGUAGES = {"de": "Deutsch", "en": "English"}
current_language: ContextVar[str] = ContextVar("current_language", default="de")
log = logging.getLogger("grc_ui")


@lru_cache
def catalogue(lang: str) -> dict[str, str]:
    path = LOCALE_DIR / lang / "LC_MESSAGES" / "messages.po"
    if not path.exists():
        return {}
    try:
        with path.open("rb") as f:
            cat = read_po(f)
    except Exception:  # a broken catalogue is logged and left out, never down the page
        log.exception("broken catalogue %s", path)
        return {}
    return {str(m.id): str(m.string) for m in cat if m.id and m.string and not m.fuzzy}


def gettext(message: str) -> str:
    lang = current_language.get()
    if lang == "en" or not message:
        return message
    return catalogue(lang).get(message, message)


def N_(message: str) -> str:  # noqa: N802
    """Marks a message id for extraction; translated later with gettext."""
    return message


_ = gettext
