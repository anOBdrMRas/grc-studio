"""Turns submitted form fields into API values, using the form definitions."""

from typing import Any

from starlette.datastructures import FormData

from grc_ui.forms import Section

SKIP = {"readonly", "status"}


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
            elif kind == "number":
                raw = str(form.get(key) or "0").strip()
                out[key] = int(raw) if raw.lstrip("-").isdigit() else 0
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
