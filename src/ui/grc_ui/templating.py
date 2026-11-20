"""Jinja environment and render(): every page gets me, csrf_token, can() and the navigation."""

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from grc_ui.assistant import ERRORS as AI_ERRORS
from grc_ui.assistant import KIND_LABELS, answer_html
from grc_ui.assistant import href as assistant_href
from grc_ui.i18n import LANGUAGES, current_language, gettext
from grc_ui.icons import icon
from grc_ui.nav import is_active, nav_for
from grc_ui.session import UiContext

BASE = Path(__file__).parent
STATIC = BASE / "static"


@lru_cache
def _fingerprint(path: str) -> str:
    f = STATIC / path
    return hashlib.sha256(f.read_bytes()).hexdigest()[:10] if f.exists() else "0"


def asset_url(path: str) -> str:
    return f"/static/{path}?v={_fingerprint(path)}"


def _ngettext(s: str, p: str, n: int) -> str:
    return gettext(s if n == 1 else p)


env = Environment(
    loader=FileSystemLoader(BASE / "templates"),
    autoescape=select_autoescape(["html"]),
    undefined=StrictUndefined,
    extensions=["jinja2.ext.i18n"],
    trim_blocks=True,
    lstrip_blocks=True,
)
env.install_gettext_callables(gettext, _ngettext, newstyle=True)  # type: ignore[attr-defined]
env.globals.update(icon=icon, asset_url=asset_url, languages=LANGUAGES, is_active=is_active)
env.filters["tojson_attr"] = lambda v: json.dumps(v, ensure_ascii=False)


def num(v: float | int) -> str:
    """A measured value without trailing zeros: 99.0 → 99, 2.40 → 2.4."""
    return f"{float(v):.4f}".rstrip("0").rstrip(".")


env.filters["num"] = num


def check_text(check: dict[str, Any]) -> str:
    """A legal-certainty finding of the API in the current language (catalogue values translated)."""
    sep = "." if current_language.get() == "de" else ","

    def shown(key: str, value: str) -> str:
        if key == "type":
            return gettext(value)
        if key in ("amount", "limit") and value.isdigit():
            return f"{int(value):,}".replace(",", sep)
        return value

    values = {k: shown(k, v) for k, v in check["vars"].items()}
    return gettext(check["message"]).format(**values)


env.filters["check_text"] = check_text
env.filters["answer_html"] = answer_html
env.globals.update(assistant_href=assistant_href, kind_labels=KIND_LABELS, ai_errors=AI_ERRORS)


def rt_labels() -> dict[str, str]:
    """Button labels of the rich text editor in the current language."""
    return {
        "formatting": gettext("Formatting"),
        "paragraph": gettext("Paragraph style"),
        "content": gettext("Content"),
        "text": gettext("Text"),
        "h1": gettext("Heading 1"),
        "h2": gettext("Heading 2"),
        "h3": gettext("Heading 3"),
        "bold": gettext("Bold"),
        "italic": gettext("Italic"),
        "underline": gettext("Underline"),
        "strike": gettext("Strikethrough"),
        "highlight": gettext("Highlight"),
        "bullet": gettext("Bullet list"),
        "ordered": gettext("Numbered list"),
        "quote": gettext("Quote / note"),
        "left": gettext("Align left"),
        "center": gettext("Centre"),
        "right": gettext("Align right"),
        "link": gettext("Link"),
        "linkPrompt": gettext("Link address (empty = remove link)"),
        "image": gettext("Insert image"),
        "table": gettext("Insert table"),
        "addRow": gettext("Insert row below"),
        "addCol": gettext("Insert column right"),
        "delRow": gettext("Delete row"),
        "delCol": gettext("Delete column"),
        "header": gettext("Header row on/off"),
        "delTable": gettext("Delete table"),
        "undo": gettext("Undo"),
        "redo": gettext("Redo"),
    }


env.globals["rt_labels"] = rt_labels
env.tests["startingwith"] = lambda s, prefix: str(s).startswith(prefix)


def render(
    request: Request,
    template: str,
    ctx: UiContext | None = None,
    status: int = 200,
    headers: dict[str, str] | None = None,
    **kw: Any,
) -> HTMLResponse:
    perms = ctx.permissions if ctx else frozenset()
    data = {
        "request": request,
        "path": request.url.path,
        "me": ctx.me if ctx else None,
        "csrf_token": ctx.me["csrf_token"] if ctx else "",
        "can": (lambda p: p in perms),
        "nav": nav_for(perms),
        "lang": current_language.get(),
        "hx": request.headers.get("HX-Request") == "true",
        **kw,
    }
    html = env.get_template(template).render(data)
    return HTMLResponse(html, status_code=status, headers=headers)


def toast(kind: str, message: str, *events: str) -> dict[str, str]:
    """HX-Trigger header for a toast in the page, plus further events (one header holds them all)."""
    triggers: dict[str, object] = {e: True for e in events}
    triggers["toast"] = {"kind": kind, "message": message}
    return {"HX-Trigger": json.dumps(triggers)}
