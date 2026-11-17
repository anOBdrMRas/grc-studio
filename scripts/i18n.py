"""Translations: the message id is the English text, German lives in locale/de/LC_MESSAGES/messages.po.

uv run python scripts/i18n.py extract   # write messages.pot and add new ids to the German catalogue
uv run python scripts/i18n.py missing   # list ids without German translation (fails when there are any)
"""

import ast
import re
import sys
from pathlib import Path

from babel.messages.catalog import Catalog
from babel.messages.pofile import read_po, write_po

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "src/ui/grc_ui"
LOCALE = UI / "locale"
DE = LOCALE / "de/LC_MESSAGES/messages.po"
API_CATALOGS = ROOT / "src/api/grc_api/domain/catalogs.py"
API_ISO = ROOT / "src/api/grc_api/domain/iso.py"

CALL = re.compile(r"""\b(?:_|N_|gettext)\(\s*(["'])((?:\\.|(?!\1).)*)\1""", re.S)
# values shown through _(variable): option lists of the API, history actions, notes of the API
EXTRA = [
    "Created",
    "Edited",
    "Approval workflow",
    "Diagram changed",
    "Assignment in process step",
    "Deleted",
    "Signed in",
    "{role} assigned to step {step}",
    "{role} removed from step {step}",
    "{item} assigned to step {step}",
    "{item} removed from step {step}",
    "measurement",
    "RACI of {role} in step {step}: {raci}",
    "submitted",
    "approved",
    "rejected",
    "reopened",
    "status",
    "Status",
    "Version",
    "employee",
    "ia",
    "admin",
]


def literal(s: str) -> str:
    return str(ast.literal_eval(f'"{s}"')) if "\\" in s else s


def extract() -> list[str]:
    ids: dict[str, None] = {}
    for f in sorted([*UI.rglob("*.html"), *UI.rglob("*.py")]):
        for m in CALL.finditer(f.read_text(encoding="utf-8")):
            ids[literal(m.group(2))] = None
    tree = ast.parse(API_CATALOGS.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.List):
            for e in node.elts:
                if (
                    isinstance(e, ast.Constant)
                    and isinstance(e.value, str)
                    and not re.fullmatch(r"[A-Z]|ISO \d+", e.value)
                ):
                    ids[e.value] = None
    for m in re.finditer(
        r'\(\s*"[^"]+",\s*"ISO (?:9001|37301|14001)",\s*"[^"]+",\s*"((?:\\.|[^"\\])*)",?\s*\)',
        API_ISO.read_text(encoding="utf-8"),
    ):
        ids[literal(m.group(1))] = None
    for e in EXTRA:
        ids[e] = None
    return [i for i in ids if i.strip()]


def load(path: Path) -> Catalog:
    if not path.exists():
        return Catalog(locale="de")
    with path.open("rb") as f:
        return read_po(f, locale="de")


def save(path: Path, cat: Catalog) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        write_po(f, cat, width=0, sort_output=True, omit_header=False)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "missing"
    ids = extract()
    if cmd == "extract":
        pot = Catalog(project="GRC Studio")
        for i in ids:
            pot.add(i)
        save(LOCALE / "messages.pot", pot)
        de = load(DE)
        for i in ids:
            if i not in de:
                de.add(i, "")
        save(DE, de)
        print(f"{len(ids)} message ids")
        return 0
    de = load(DE)
    missing = [i for i in ids if not (de.get(i) and de.get(i).string)]
    for i in missing:
        print("missing:", i)
    print(f"{len(missing)} without German translation")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
