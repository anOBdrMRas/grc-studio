"""Excel export and import of the modules (deviation-free: all rules stay in the API).

Columns come from the form definitions (forms.py). Headers are written in the current language
and recognised in German and English on import. Elements are referred to by their ID, persons by
their name (or ID); list values are joined with "; ", treatment actions and the roles of a
position use one line per entry ("text | person", "role ID | comment").
"""

import io
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from grc_ui.forms import Section
from grc_ui.i18n import catalogue, gettext

# kinds that are not columns: computed or set by workflows
NOT_EXPORTED = frozenset({"status", "risk_eval", "risk_guide", "mandate_state"})
# exported for information, never imported
READ_ONLY = frozenset({"readonly"})
SEP = "; "
LANGS = ("en", "de")


def columns(sections: list[Section]) -> list[dict[str, Any]]:
    """The fields of a form that become columns; the ID always comes first."""
    fields = [f for s in sections for f in s["fields"] if f["kind"] not in NOT_EXPORTED]
    ids = [f for f in fields if f["key"] == "code"]
    rest = [f for f in fields if f["key"] != "code"]
    return (ids or [{"key": "code", "label": "ID", "kind": "readonly"}]) + rest


def translations(message: str) -> set[str]:
    """A message id and its translations (for recognising headers and values)."""
    out = {message}
    for lang in LANGS:
        out.add(catalogue(lang).get(message, message))
    return {x.strip().casefold() for x in out if x}


@dataclass
class Lookups:
    """What import and export need to turn ids into readable values and back."""

    people: dict[str, str] = field(default_factory=dict)  # id → name
    lists: dict[str, list[str]] = field(default_factory=dict)  # catalogue key → values

    def person_id(self, text: str) -> str:
        t = text.strip()
        if t in self.people:
            return t
        hits = [pid for pid, name in self.people.items() if name.casefold() == t.casefold()]
        if len(hits) == 1:
            return hits[0]
        raise ValueError(
            gettext("Person not found: {name}").format(name=t)
            if not hits
            else gettext("Name not unique: {name} – use the user ID").format(name=t)
        )

    def option(self, list_key: str, text: str) -> str:
        t = text.strip()
        for value in self.lists.get(list_key, []):
            if t.casefold() in translations(value):
                return value
        raise ValueError(gettext("Unknown value: {value}").format(value=t))


# ---- export ------------------------------------------------------------------------------------


def encode(f: dict[str, Any], v: Any, lk: Lookups) -> Any:
    kind = f["kind"]
    if v is None or v == "" or v == []:
        return None
    if kind == "bool":
        return gettext("Yes") if v else gettext("No")
    if kind == "select":
        return gettext(str(v))
    if kind == "multiselect":
        return SEP.join(gettext(str(x)) for x in v)
    if kind == "ref":
        return lk.people.get(v, v) if f.get("ref") == "people" else v
    if kind == "refs":
        return SEP.join(lk.people.get(x, x) if f.get("ref") == "people" else x for x in v)
    if kind == "iso":
        return SEP.join(v)
    if kind == "risk_actions":
        return "\n".join(
            f"{a.get('text', '')} | {lk.people.get(a.get('owner_user_id') or '', '')}".rstrip(" |")
            for a in v
        )
    if kind == "position_roles":
        return "\n".join(f"{r.get('role_id', '')} | {r.get('comment', '')}".rstrip(" |") for r in v)
    if kind in ("number", "scale", "decimal"):
        return v
    return str(v)


def _sheet(ws: Worksheet, headers: list[str], rows: Iterable[list[Any]]) -> None:
    ws.append(headers)
    for row in rows:
        ws.append(row)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="0A2F4D")
        cell.alignment = Alignment(vertical="top", wrap_text=True)
    ws.freeze_panes = "B2"
    for i, h in enumerate(headers, start=1):
        width = max(
            [len(str(h)), *(len(str(c.value or "")) for c in ws[get_column_letter(i)][1:50])]
        )
        ws.column_dimensions[get_column_letter(i)].width = min(max(width + 2, 10), 60)
    for cells in ws.iter_rows(min_row=2):
        for cell in cells:
            cell.alignment = Alignment(vertical="top", wrap_text=True)


def sheet_title(title: str) -> str:
    """Excel allows 31 characters and no []:*?/\\ in sheet names."""
    clean = "".join(" " if c in "[]:*?/\\" else c for c in title)
    return clean[:31]


@dataclass
class SheetData:
    title: str
    sections: list[Section]
    items: list[dict[str, Any]]


@dataclass
class ExtraSheet:
    """Additional table (measured values, findings, step assignments): export only."""

    title: str
    headers: list[str]
    rows: list[list[Any]]


def workbook(sheets: list[SheetData], extras: list[ExtraSheet], lk: Lookups) -> bytes:
    wb = Workbook()
    wb.remove(wb.active)  # type: ignore[arg-type]
    for s in sheets:
        cols = columns(s.sections)
        ws = wb.create_sheet(sheet_title(s.title))
        _sheet(
            ws,
            [gettext(c["label"]) for c in cols],
            ([encode(c, item.get(c["key"]), lk) for c in cols] for item in s.items),
        )
    for x in extras:
        _sheet(wb.create_sheet(sheet_title(x.title)), x.headers, x.rows)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---- import ------------------------------------------------------------------------------------


def decode(f: dict[str, Any], raw: Any, lk: Lookups) -> Any:
    """A cell as API value; raises ValueError with a translated message."""
    kind = f["kind"]
    text = (
        ""
        if raw is None
        else (raw.isoformat()[:10] if isinstance(raw, date | datetime) else str(raw)).strip()
    )
    if kind == "bool":
        if not text:
            return False
        if text.casefold() in translations("Yes") | {"1", "true", "x", "ja"}:
            return True
        if text.casefold() in translations("No") | {"0", "false", "nein"}:
            return False
        raise ValueError(gettext("Yes or no expected: {value}").format(value=text))
    if kind in ("number", "scale"):
        if not text:
            return 0
        try:
            return int(float(text.replace(",", ".")))
        except ValueError:
            raise ValueError(gettext("Number expected: {value}").format(value=text)) from None
    if kind == "decimal":
        if not text:
            return 0.0
        try:
            return float(text.replace(",", "."))
        except ValueError:
            raise ValueError(gettext("Number expected: {value}").format(value=text)) from None
    if kind == "date":
        if not text:
            return None
        for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
            try:
                return datetime.strptime(text, fmt).date().isoformat()
            except ValueError:
                continue
        raise ValueError(gettext("Date expected (YYYY-MM-DD): {value}").format(value=text))
    if kind == "select":
        return lk.option(f["options"], text) if text else ""
    if kind == "multiselect":
        return [lk.option(f["options"], x) for x in _split(text)]
    if kind == "ref":
        if not text:
            return None
        return lk.person_id(text) if f.get("ref") == "people" else text
    if kind == "refs":
        return [lk.person_id(x) if f.get("ref") == "people" else x for x in _split(text)]
    if kind == "iso":
        return _split(text)
    if kind == "risk_actions":
        out = []
        for line in text.splitlines():
            if not line.strip():
                continue
            act, _, person = line.partition("|")
            out.append(
                {
                    "text": act.strip(),
                    "owner_user_id": lk.person_id(person) if person.strip() else None,
                }
            )
        return out
    if kind == "position_roles":
        out = []
        for line in text.splitlines():
            if not line.strip():
                continue
            role, _, comment = line.partition("|")
            out.append({"role_id": role.strip(), "comment": comment.strip()})
        return out
    return text


def _split(text: str) -> list[str]:
    return [x.strip() for x in text.replace("\n", ";").split(";") if x.strip()]


@dataclass
class Row:
    number: int  # row in the sheet (for messages)
    code: str
    values: dict[str, Any]
    errors: list[str]


def read_rows(content: bytes, sections: list[Section], lk: Lookups) -> tuple[list[Row], list[str]]:
    """Rows of the first sheet whose headers match the form; unknown columns are reported."""
    try:
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:  # any unreadable upload is a user error, not a crash
        raise ValueError(gettext("The file is not an Excel workbook (.xlsx).")) from exc
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = next(rows, None)
    if not header:
        raise ValueError(gettext("The sheet is empty."))
    cols = columns(sections)
    by_label: dict[str, dict[str, Any]] = {}
    for col in cols:
        for name in translations(col["label"]) | {
            col["key"].casefold(),
            "id" if col["key"] == "code" else "",
        }:
            if name:
                by_label.setdefault(name, col)
    mapping: list[dict[str, Any] | None] = []
    unknown: list[str] = []
    for h in header:
        hit = by_label.get(str(h or "").strip().casefold())
        mapping.append(hit)
        if hit is None and h:
            unknown.append(str(h))
    out = []
    for n, raw in enumerate(rows, start=2):
        if not raw or all(v is None or str(v).strip() == "" for v in raw):
            continue
        values: dict[str, Any] = {}
        errors: list[str] = []
        code = ""
        for target, cell in zip(mapping, raw, strict=False):
            if target is None:
                continue
            if target["key"] == "code":
                code = str(cell or "").strip()
                continue
            if target["kind"] in READ_ONLY:
                continue
            try:
                values[target["key"]] = decode(target, cell, lk)
            except ValueError as exc:
                errors.append(f"{gettext(target['label'])}: {exc}")
        out.append(Row(n, code, values, errors))
    return out, unknown


def _same(a: Any, b: Any) -> bool:
    """Equal for the import preview: empty values alike, numbers by value."""
    empty: tuple[Any, ...] = (None, "", [])
    if a in empty and b in empty:
        return True
    if isinstance(a, int | float) and isinstance(b, int | float):
        return float(a) == float(b)
    return bool(a == b)


def changes(current: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    """Only the values that differ from the stored element."""
    return {k: v for k, v in values.items() if not _same(current.get(k), v)}
