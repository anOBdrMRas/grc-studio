"""Rendering of assistant answers: [[kind:id|label]] links become links into the application."""

import re

from markupsafe import Markup, escape

from grc_ui.i18n import N_

LINK = re.compile(r"\[\[([a-z]+):([^|\]]+)\|([^\]]+)\]\]")
BOLD = re.compile(r"\*\*(.+?)\*\*")
BASES = {
    "processes": "/processes/",
    "role": "/roles/",
    "position": "/positions/",
    "mandate": "/delegations/",
    "risk": "/risks/",
    "opportunity": "/opportunities/",
    "control": "/controls/",
    "kpi": "/kpi/",
    "audit": "/audits/",
}
KIND_LABELS = {
    "processes": N_("Process"),
    "step": N_("Process step"),
    "role": N_("Role"),
    "position": N_("Position"),
    "mandate": N_("Delegation"),
    "risk": N_("Risk"),
    "opportunity": N_("Opportunity"),
    "control": N_("Control"),
    "kpi": N_("KPI"),
    "audit": N_("Audit"),
}
ERRORS = {
    "ai_auth": N_("The AI service did not accept the API key. Please tell the administration."),
    "ai_busy": N_("The AI service is busy right now. Please try again in a moment."),
    "ai_refused": N_("The AI did not answer this question."),
    "ai_rejected": N_("The AI service rejected the request."),
    "ai_unavailable": N_("The AI service cannot be reached right now."),
}


def href(kind: str, id_: str) -> str:
    if kind == "step":
        process_id, _, element = id_.partition("/")
        return f"/processes/{process_id}?step={element}"
    return BASES.get(kind, "/") + id_


def answer_html(text: str) -> Markup:
    """Escaped text with links and **bold**; line breaks are kept by the template (pre-line)."""
    out: list[str] = []
    last = 0
    for m in LINK.finditer(text):
        out.append(_plain(text[last : m.start()]))
        kind, id_, label = m.group(1), m.group(2).strip(), m.group(3).strip()
        if kind in KIND_LABELS:
            out.append(
                f'<a class="link link-secondary font-medium" href="{escape(href(kind, id_))}">'
                f"{escape(label)}</a>"
            )
        else:
            out.append(_plain(label))
        last = m.end()
    out.append(_plain(text[last:]))
    return Markup("".join(out))  # noqa: S704 - every part is escaped above


def _plain(s: str) -> str:
    return BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", str(escape(s)))
