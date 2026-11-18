"""Content administration: custom fields and additional dropdown values per module.

Administrators add fields ("x_…" keys) and dropdown values; standard fields and values stay as they
are so existing data remains valid. A custom field is never deleted, only hidden (`removed`): its
stored values are kept. Its type cannot change, since stored values would no longer fit.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from typing import Any

KINDS = (
    "process",
    "risk",
    "opportunity",
    "control",
    "role",
    "position",
    "mandate",
    "kpi",
    "audit",
    "user",
)
TYPES = ("text", "textarea", "number", "date", "bool", "select", "multiselect", "user")
WITH_OPTIONS = frozenset({"select", "multiselect"})
PREFIX = "x_"
KEY_RE = re.compile(r"^x_[a-z0-9_]{1,40}$")
MAX_FIELDS = 50
MAX_OPTIONS = 100
MAX_TEXT = 200


class ContentError(ValueError):
    """An invalid configuration or value; the message is shown to the administrator."""


@dataclass
class CustomField:
    key: str
    label: str
    type: str
    section: str = ""
    options: list[str] = field(default_factory=list)
    removed: bool = False


@dataclass
class Config:
    fields: dict[str, list[CustomField]] = field(default_factory=dict)
    # additional values of standard dropdowns, key "kind.field"
    options: dict[str, list[str]] = field(default_factory=dict)

    def active(self, kind: str) -> dict[str, CustomField]:
        return {f.key: f for f in self.fields.get(kind, []) if not f.removed}

    def all_fields(self, kind: str) -> dict[str, CustomField]:
        return {f.key: f for f in self.fields.get(kind, [])}


def is_custom(key: str) -> bool:
    return key.startswith(PREFIX)


def custom_key(label: str, existing: set[str]) -> str:
    """Key for a new field from its label, unique in its module."""
    text = label.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(a, b)
    ascii_ = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    base = PREFIX + (re.sub(r"[^a-z0-9]+", "_", ascii_).strip("_")[:30] or "field")
    key, n = base, 2
    while key in existing:
        key, n = f"{base}_{n}", n + 1
    return key


def _clean_list(values: list[str]) -> list[str]:
    out: list[str] = []
    for v in values:
        t = str(v).strip()[:MAX_TEXT]
        if t and t not in out:
            out.append(t)
    if len(out) > MAX_OPTIONS:
        raise ContentError(f"At most {MAX_OPTIONS} values per field")
    return out


def from_json(data: dict[str, Any] | None) -> Config:
    """The stored document (trusted: it was checked by `checked` before it was saved)."""
    data = data or {}
    return Config(
        fields={k: [CustomField(**f) for f in v] for k, v in (data.get("fields") or {}).items()},
        options={k: list(v) for k, v in (data.get("options") or {}).items()},
    )


def to_json(cfg: Config) -> dict[str, Any]:
    return {
        "fields": {
            k: [
                {
                    "key": f.key,
                    "label": f.label,
                    "type": f.type,
                    "section": f.section,
                    "options": f.options,
                    "removed": f.removed,
                }
                for f in v
            ]
            for k, v in cfg.fields.items()
            if v
        },
        "options": {k: v for k, v in cfg.options.items() if v},
    }


def checked(new: Config, old: Config, standard_keys: dict[str, set[str]]) -> Config:
    """Validates a new configuration against the stored one; assigns keys to new fields.

    `standard_keys` are the field keys of each module (dropdown values may only extend those).
    """
    out = Config()
    for kind, fields in new.fields.items():
        if kind not in KINDS:
            raise ContentError(f"Unknown module: {kind}")
        if len(fields) > MAX_FIELDS:
            raise ContentError(f"At most {MAX_FIELDS} custom fields per module")
        before = old.all_fields(kind)
        taken = set(before) | {f.key for f in fields if f.key}
        seen: set[str] = set()
        result: list[CustomField] = []
        for f in fields:
            label = f.label.strip()[:MAX_TEXT]
            if not label:
                raise ContentError("Every field needs a label")
            if f.type not in TYPES:
                raise ContentError(f"Unknown field type: {f.type}")
            key = f.key or custom_key(label, taken)
            taken.add(key)
            if not KEY_RE.match(key):
                raise ContentError(f"Invalid field key: {key}")
            if key in seen:
                raise ContentError(f"Field key used twice: {key}")
            seen.add(key)
            if key in before and before[key].type != f.type:
                raise ContentError(f"The type of an existing field cannot change: {label}")
            options = _clean_list(f.options) if f.type in WITH_OPTIONS else []
            if f.type in WITH_OPTIONS and not options and not f.removed:
                raise ContentError(f"A dropdown field needs values: {label}")
            result.append(
                CustomField(key, label, f.type, f.section.strip()[:MAX_TEXT], options, f.removed)
            )
        out.fields[kind] = result
    # a field that existed is kept (hidden at most): its stored values remain readable
    for kind in old.fields:
        keys = {f.key for f in out.fields.get(kind, [])}
        missing = [f for f in old.fields[kind] if f.key not in keys]
        if missing:
            out.fields.setdefault(kind, []).extend(
                CustomField(f.key, f.label, f.type, f.section, f.options, True) for f in missing
            )
    for name, values in new.options.items():
        kind, _, key = name.partition(".")
        if kind not in KINDS or key not in standard_keys.get(kind, set()):
            raise ContentError(f"Unknown dropdown field: {name}")
        out.options[name] = _clean_list(values)
    return out


def value(f: CustomField, raw: Any, current: Any = None) -> Any:
    """A value for a custom field as stored; raises ContentError if it does not fit the type."""
    t = f.type
    if raw is None or raw == "":
        return [] if t == "multiselect" else (False if t == "bool" else None)
    if t in ("text", "textarea", "user"):
        if not isinstance(raw, str):
            raise ContentError(f"{f.label}: text expected")
        return raw[:10_000]
    if t == "number":
        if isinstance(raw, bool) or not isinstance(raw, int | float):
            raise ContentError(f"{f.label}: number expected")
        return int(raw) if isinstance(raw, float) and raw.is_integer() else raw
    if t == "bool":
        if not isinstance(raw, bool):
            raise ContentError(f"{f.label}: yes or no expected")
        return raw
    if t == "date":
        try:
            return date.fromisoformat(str(raw)).isoformat()
        except ValueError as exc:
            raise ContentError(f"{f.label}: date expected (YYYY-MM-DD)") from exc
    if t == "select":
        # a value that was removed from the list stays valid where it is already stored
        if raw not in f.options and raw != current:
            raise ContentError(f"{f.label}: unknown value {raw}")
        return raw
    if t == "multiselect":
        if not isinstance(raw, list):
            raise ContentError(f"{f.label}: list expected")
        kept = set(current or [])
        bad = [x for x in raw if x not in f.options and x not in kept]
        if bad:
            raise ContentError(f"{f.label}: unknown value {bad[0]}")
        return [str(x) for x in raw]
    raise ContentError(f"Unknown field type: {t}")


def values(cfg: Config, kind: str, raw: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Checked custom values of an element: only active fields can be written."""
    fields = cfg.active(kind)
    out: dict[str, Any] = {}
    for k, v in raw.items():
        f = fields.get(k)
        if f is None:
            raise ContentError(f"Unknown field: {k}")
        out[k] = value(f, v, current.get(k))
    return out
