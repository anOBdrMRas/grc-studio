"""Forms with the content administration applied: additional dropdown values and custom fields.

The configuration comes from the API (`GET /api/v1/content`); its rules (keys, types, which
values are allowed) are checked there. Here it only shapes the forms, lists and Excel columns.
"""

import copy
from dataclasses import dataclass, field
from typing import Any

from grc_client import GrcClient
from grc_ui.forms import FORMS, Section
from grc_ui.i18n import N_

NEW_SECTION = N_("Additional details")
TYPE_LABELS = {
    "text": N_("Text"),
    "textarea": N_("Long text"),
    "number": N_("Number"),
    "date": N_("Date"),
    "bool": N_("Yes/no"),
    "select": N_("Dropdown"),
    "multiselect": N_("Multiple choice"),
    "user": N_("Person"),
}
# how a custom field is shown and read in the forms
FIELD_KIND = {
    "text": "text",
    "textarea": "textarea",
    "number": "decimal",
    "date": "date",
    "bool": "bool",
    "select": "select",
    "multiselect": "multiselect",
    "user": "ref",
}
EXTENDABLE = frozenset({"select", "multiselect"})


@dataclass
class Content:
    version: int = 0
    fields: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    options: dict[str, list[str]] = field(default_factory=dict)
    base_lists: dict[str, list[Any]] = field(default_factory=dict)

    def active(self, kind: str) -> list[dict[str, Any]]:
        return [f for f in self.fields.get(kind, []) if not f.get("removed")]

    @property
    def lists(self) -> dict[str, list[Any]]:
        """The value lists plus one list per extended dropdown and per custom dropdown."""
        out = dict(self.base_lists)
        for kind, sections in FORMS.items():
            for sec in sections:
                for f in sec["fields"]:
                    extra = self.options.get(f"{kind}.{f['key']}")
                    if extra and f["kind"] in EXTENDABLE:
                        base = list(self.base_lists.get(f["options"], []))
                        out[f"{kind}.{f['key']}"] = base + [x for x in extra if x not in base]
        for kind, fields in self.fields.items():
            for c in fields:
                out[f"custom:{kind}.{c['key']}"] = list(c.get("options") or [])
        return out

    def labels(self, kind: str) -> dict[str, str]:
        """Labels of all fields, hidden custom fields included (for the history)."""
        out = {f["key"]: f["label"] for s in FORMS[kind] for f in s["fields"]}
        return out | {c["key"]: c["label"] for c in self.fields.get(kind, [])}

    def sections(self, kind: str) -> list[Section]:
        """The form of a module with the configuration applied."""
        out = copy.deepcopy(FORMS[kind])
        for sec in out:
            for f in sec["fields"]:
                if f["kind"] in EXTENDABLE and self.options.get(f"{kind}.{f['key']}"):
                    f["options"] = f"{kind}.{f['key']}"
        for c in self.active(kind):
            target = next((s for s in out if s["title"] == c.get("section")), None)
            if target is None:
                target = next((s for s in out if s["title"] == NEW_SECTION), None)
                if target is None:
                    target = {"title": NEW_SECTION, "fields": []}
                    out.append(target)
            target["fields"].append(field_def(kind, c))
        return out


def field_def(kind: str, c: dict[str, Any]) -> dict[str, Any]:
    f: dict[str, Any] = {
        "key": c["key"],
        "label": c["label"],
        "kind": FIELD_KIND[c["type"]],
        "custom": True,
    }
    if c["type"] in EXTENDABLE:
        f["options"] = f"custom:{kind}.{c['key']}"
        f["empty"] = True
    if c["type"] == "number":
        f["nullable"] = True  # empty stays empty (no 0 for elements never filled in)
    if c["type"] == "user":
        f["ref"] = "people"
    if c["type"] == "textarea":
        f["wide"] = True
    return f


async def load(api: GrcClient, base_lists: dict[str, list[Any]]) -> Content:
    data = await api.content_get()
    return Content(
        version=data["version"],
        fields={k: [dict(f) for f in v] for k, v in data["fields"].items()},
        options={k: list(v) for k, v in data["options"].items()},
        base_lists=base_lists,
    )


def flat(item: dict[str, Any]) -> dict[str, Any]:
    """An element with its custom values next to the standard ones (as the forms expect)."""
    return item | dict(item.get("custom") or {})
