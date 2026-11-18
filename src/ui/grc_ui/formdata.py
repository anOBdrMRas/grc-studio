"""Turns submitted form fields into API values, using the form definitions."""

from typing import Any

from starlette.datastructures import FormData

from grc_ui.forms import Section

SKIP = {"readonly", "status", "risk_eval", "risk_guide", "mandate_state"}


def values_from_form(
    sections: list[Section], form: FormData, editable_owner: bool
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for sec in sections:
        for f in sec["fields"]:
            key, kind = f["key"], f["kind"]
            if kind in SKIP or (f.get("owner") and not editable_owner):
                continue
            if kind == "bool":
                out[key] = form.get(key) == "on"
            elif kind in ("multiselect", "refs", "iso"):
                out[key] = [str(v) for v in form.getlist(key) if v]
            elif kind == "scale":
                raw = str(form.get(key) or "0").strip()
                out[key] = int(raw) if raw.isdigit() else 0
            elif kind == "risk_actions":
                texts = form.getlist("actions.text")
                owners = form.getlist("actions.owner_user_id")
                out[key] = [
                    {"text": str(t).strip(), "owner_user_id": str(o) or None}
                    for t, o in zip(texts, owners, strict=False)
                    if str(t).strip()
                ]
            elif kind == "decimal" and f.get("nullable") and not str(form.get(key) or "").strip():
                out[key] = None
            elif kind == "decimal":
                raw = str(form.get(key) or "0").strip().replace(",", ".")
                try:
                    out[key] = float(raw)
                except ValueError:
                    out[key] = 0.0
            elif kind == "number":
                raw = str(form.get(key) or "0").strip()
                out[key] = int(raw) if raw.lstrip("-").isdigit() else 0
            elif kind == "iso_one":
                out[key] = str(form.get(key) or "")
            elif kind in ("date", "ref"):
                out[key] = str(form.get(key) or "") or None
            elif kind == "position_roles":
                role_ids = form.getlist("roles.role_id")
                comments = form.getlist("roles.comment")
                out[key] = [
                    {"role_id": str(r), "comment": str(c)}
                    for r, c in zip(role_ids, comments, strict=False)
                    if r
                ]
            else:
                out[key] = str(form.get(key) or "")
    return out
