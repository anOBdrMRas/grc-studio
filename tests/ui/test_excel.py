"""Excel codec: export and import are inverse; headers in German or English; clear errors."""

import io

import pytest
from openpyxl import Workbook, load_workbook

from grc_ui import excel
from grc_ui.forms import FORMS
from grc_ui.i18n import current_language

LK = excel.Lookups(
    people={"U-001": "Anna Berger", "U-002": "Max Muster", "U-003": "Max Muster"},
    lists={
        "risk_categories": ["Quality", "Financial", "Strategic"],
        "treatment_statuses": ["Identified", "Assessed"],
        "protection_goals": ["Confidentiality", "Integrity", "Availability"],
        "consequence_types": ["Economic loss"],
        "treatments": ["Reduce", "Accept"],
        "risk_departments": ["Finance"],
        "risk_entities": ["CDE"],
        "assessment_reasons": ["Other"],
        "role_types": ["Functional role"],
        "org_units": ["Generic"],
        "mandate_types": ["None"],
    },
)
RISK = {
    "code": "R-001",
    "description": "Erster Satz. Zweiter Satz.",
    "category": "Financial",
    "likelihood": 3,
    "impact": 4,
    "owner_user_id": "U-001",
    "protection_goals": ["Integrity", "Availability"],
    "actions": [
        {"text": "Freigabe sperren", "owner_user_id": "U-001"},
        {"text": "Schulung", "owner_user_id": None},
    ],
    "process_ids": ["P-001", "P-002"],
    "next_review": "2027-01-31",
    "iso_refs": ["9001:6.1"],
}


@pytest.fixture(params=["de", "en"])
def lang(request: pytest.FixtureRequest):  # type: ignore[no-untyped-def]
    token = current_language.set(request.param)
    yield request.param
    current_language.reset(token)


def test_round_trip(lang: str) -> None:
    content = excel.workbook([excel.SheetData("Risks", FORMS["risk"], [RISK])], [], LK)
    rows, unknown = excel.read_rows(content, FORMS["risk"], LK)
    assert unknown == []
    (row,) = rows
    assert row.code == "R-001"
    assert row.errors == []
    for key in (
        "description",
        "category",
        "likelihood",
        "impact",
        "owner_user_id",
        "protection_goals",
        "actions",
        "process_ids",
        "next_review",
        "iso_refs",
    ):
        assert row.values[key] == RISK[key], key
    assert excel.changes(RISK, row.values) == {}


def test_headers_in_the_other_language_are_recognised() -> None:
    token = current_language.set("en")
    try:
        content = excel.workbook([excel.SheetData("Risks", FORMS["risk"], [RISK])], [], LK)
    finally:
        current_language.reset(token)
    token = current_language.set("de")
    try:
        rows, unknown = excel.read_rows(content, FORMS["risk"], LK)
    finally:
        current_language.reset(token)
    assert unknown == []
    assert rows[0].values["category"] == "Financial"


def _sheet(headers: list[str], *rows: list[object]) -> bytes:
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_errors_per_row_and_unknown_columns() -> None:
    content = _sheet(
        [
            "ID",
            "Risikokategorie",
            "Wahrscheinlichkeit",
            "Risikoeigner",
            "Nächste Überprüfung",
            "Fantasie",
        ],
        ["R-1", "Gibt es nicht", "x", "Max Muster", "31.01.2027", "egal"],
        ["", "Qualität", 2, "U-002", "", ""],
    )
    token = current_language.set("de")
    try:
        rows, unknown = excel.read_rows(content, FORMS["risk"], LK)
    finally:
        current_language.reset(token)
    assert unknown == ["Fantasie"]
    first, second = rows
    assert len(first.errors) == 3  # unknown value, not a number, name not unique
    assert second.errors == []
    assert second.values == {
        "category": "Quality",
        "likelihood": 2,
        "owner_user_id": "U-002",
        "next_review": None,
    }


def test_dates_in_german_format_and_booleans() -> None:
    content = _sheet(
        ["ID", "Title", "Mandatory role"], ["RO-1", "Rolle", "Ja"], ["RO-2", "Andere", "no"]
    )
    rows, _ = excel.read_rows(content, FORMS["role"], LK)
    assert [r.values["mandatory"] for r in rows] == [True, False]
    assert excel.decode({"kind": "date"}, "31.01.2027", LK) == "2027-01-31"


def test_not_an_excel_file() -> None:
    with pytest.raises(ValueError):
        excel.read_rows(b"no excel", FORMS["role"], LK)


def test_sheet_titles_are_valid() -> None:
    assert (
        excel.sheet_title("Delegations & powers of attorney: a/b")
        == "Delegations & powers of attorne"
    )
    assert len(excel.sheet_title("x" * 50)) == 31


def test_export_all_sheets_have_headers() -> None:
    content = excel.workbook(
        [
            excel.SheetData(k, FORMS[k], [])
            for k in ("role", "position", "user", "process", "kpi", "audit", "mandate")
        ],
        [excel.ExtraSheet("Extra", ["A", "B"], [[1, 2]])],
        LK,
    )
    wb = load_workbook(io.BytesIO(content))
    assert len(wb.worksheets) == 8
    assert all(ws.max_row >= 1 for ws in wb.worksheets)


def test_custom_fields_and_extra_values_in_forms_and_excel() -> None:
    from grc_ui.content import NEW_SECTION, Content, flat

    cfg = Content(
        version=1,
        fields={
            "risk": [
                {"key": "x_budget", "label": "Budget", "type": "number", "section": ""},
                {"key": "x_agency", "label": "Agency", "type": "select", "options": ["A", "B"]},
                {"key": "x_gone", "label": "Gone", "type": "text", "removed": True},
            ]
        },
        options={"risk.category": ["Supply chain"]},
        base_lists=dict(LK.lists),
    )
    sections = cfg.sections("risk")
    assert sections[-1]["title"] == NEW_SECTION
    assert [f["key"] for f in sections[-1]["fields"]] == ["x_budget", "x_agency"]
    category = next(f for s in sections for f in s["fields"] if f["key"] == "category")
    assert category["options"] == "risk.category"
    lists = cfg.lists
    assert lists["risk.category"] == ["Quality", "Financial", "Strategic", "Supply chain"]
    assert lists["custom:risk.x_agency"] == ["A", "B"]
    assert cfg.labels("risk")["x_gone"] == "Gone"
    # the forms of the code are not changed by the configuration
    assert all(f["key"] != "x_budget" for s in FORMS["risk"] for f in s["fields"])

    lk = excel.Lookups(people=LK.people, lists=lists)
    item = flat(RISK | {"category": "Supply chain", "custom": {"x_budget": 5, "x_agency": "B"}})
    data = excel.workbook([excel.SheetData("Risks", sections, [item])], [], lk)
    rows, unknown = excel.read_rows(data, sections, lk)
    assert unknown == []
    assert rows[0].errors == []
    assert rows[0].values["category"] == "Supply chain"
    assert rows[0].values["x_budget"] == 5
    assert rows[0].values["x_agency"] == "B"


def test_empty_custom_number_stays_empty() -> None:
    from starlette.datastructures import FormData

    from grc_ui.content import field_def
    from grc_ui.formdata import values_from_form

    f = field_def("risk", {"key": "x_n", "label": "N", "type": "number"})
    sections = [{"title": "T", "fields": [f]}]
    assert values_from_form(sections, FormData([("x_n", "")]), True) == {"x_n": None}
    assert values_from_form(sections, FormData([("x_n", "2,5")]), True) == {"x_n": 2.5}
    assert excel.decode(f, None, LK) is None
    assert excel.changes({"x_b": None}, {"x_b": False}) == {}
