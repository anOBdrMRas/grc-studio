"""Browser tests against a running stack (API + interface + demo data).

E2E_BASE_URL=http://localhost:8080 uv run pytest -m e2e
They change data: run them against a fresh demo database only.
"""

import os
import re
from collections.abc import Iterator
from pathlib import Path

import pytest

BASE = os.environ.get("E2E_BASE_URL", "")
pytestmark = [pytest.mark.e2e, pytest.mark.skipif(not BASE, reason="E2E_BASE_URL not set")]

if BASE:
    from playwright.sync_api import Browser, Page, expect, sync_playwright
else:  # pragma: no cover
    Page = Browser = object  # type: ignore[misc,assignment]


@pytest.fixture(scope="module")
def browser() -> Iterator["Browser"]:
    with sync_playwright() as pw:
        # E2E_CHROMIUM: a preinstalled browser instead of the one from `playwright install`
        exe = os.environ.get("E2E_CHROMIUM") or None
        b = pw.chromium.launch(executable_path=exe, args=["--no-sandbox"] if exe else [])
        yield b
        b.close()


@pytest.fixture
def page(browser: "Browser") -> Iterator["Page"]:
    ctx = browser.new_context(viewport={"width": 1400, "height": 900}, locale="de-DE")
    p = ctx.new_page()
    errors: list[str] = []
    p.on(
        "console",
        lambda m: (
            errors.append(m.text)
            if m.type == "error" or "Content Security Policy" in m.text
            else None
        ),
    )
    p.on("pageerror", lambda e: errors.append(str(e)))
    p.on("dialog", lambda d: d.accept())
    yield p
    ctx.close()
    assert errors == [], f"browser errors: {errors}"


def sign_in(page: "Page", user_id: str) -> None:
    page.goto(BASE + "/login")
    page.select_option(".login-other select", user_id)
    page.click(".login-other button")
    page.wait_for_url(BASE + "/")


def test_tiles_menubar_and_split_view(page: "Page") -> None:
    page.goto(BASE + "/login")
    expect(page.locator("button.persona")).to_have_count(4)
    sign_in(page, "U-010")
    expect(page.locator(".app-menubar")).to_contain_text("Prozesse")
    page.goto(BASE + "/roles/RO-006")
    expect(page.locator("#list")).to_be_visible()
    expect(page.locator("#detail h2")).to_contain_text("RO-006")


def test_edit_save_and_history(page: "Page") -> None:
    sign_in(page, "U-013")
    page.goto(BASE + "/roles/RO-006")
    page.click("#detail button:has-text('Bearbeiten')")
    page.fill("#f-trainings", "E2E-Schulung")
    page.click("#detail button:has-text('Speichern')")
    expect(page.locator("#toasts")).to_contain_text("Gespeichert")
    expect(page.locator("#detail")).to_contain_text("E2E-Schulung")
    page.click("#detail button:has-text('Änderungshistorie')")
    expect(page.locator("#detail")).to_contain_text("E2E-Schulung")


def test_process_editor_loads_and_saves(page: "Page") -> None:
    sign_in(page, "U-013")
    page.goto(BASE + "/processes/P-008")
    expect(page.locator("#bpmn-canvas .djs-element.djs-shape").first).to_be_visible(timeout=15000)
    shape = (
        page.locator("#bpmn-canvas .djs-element.djs-shape")
        .filter(has_text=re.compile("klassifizieren"))
        .first
    )
    shape.click()
    expect(page.locator("#step-panel")).to_contain_text("klassifizieren")
    box = shape.bounding_box()
    assert box
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2 + 50, steps=5)
    page.mouse.up()
    page.click("[data-action=save-diagram]")
    expect(page.locator("#toasts")).to_contain_text("Diagramm gespeichert")


def test_english_interface(page: "Page") -> None:
    sign_in(page, "U-004")
    page.click("form[action='/language'] button:has-text('EN')")
    expect(page.locator(".app-menubar")).to_contain_text("Processes")
    page.click("form[action='/language'] button:has-text('DE')")


def test_risk_recorded_assessed_and_released(page: "Page") -> None:
    sign_in(page, "U-004")
    page.goto(BASE + "/risks")
    expect(page.locator(".risk-cell")).to_have_count(16)
    page.fill("input[name=title]", "E2E: Lieferant liefert verspätet. Produktion steht.")
    page.click("form[hx-post='/risks'] button")
    page.wait_for_url(re.compile(r"/risks/R-\d+\?edit=1"))
    url = page.url.split("?")[0]
    page.select_option("#f-likelihood", "3")
    page.select_option("#f-impact", "4")
    page.click("#detail button:has-text('Maßnahme')")
    page.locator("#rows-actions input").last.fill("Zweitlieferant qualifizieren")
    page.click("#detail button:has-text('Speichern')")
    expect(page.locator("#detail")).to_contain_text("Höheres Risiko")
    page.click("#detail button:has-text('Fachlich freigeben')")
    expect(page.locator("#detail")).to_contain_text("Qualitätsfreigabe durch das I&A-Team")
    sign_in(page, "U-013")
    page.goto(url)
    page.click("#detail button:has-text('Qualität freigeben')")
    expect(page.locator("#detail")).to_contain_text("1.0")


def test_risk_matrix_filters_the_list(page: "Page") -> None:
    sign_in(page, "U-004")
    page.goto(BASE + "/risks?l=3&i=4")
    expect(page.locator(".risk-cell[aria-current=true]")).to_have_count(1)
    for title in page.locator("#list tbody tr").all_inner_texts():
        assert title
    page.click("text=Alle anzeigen")
    expect(page.locator(".risk-cell[aria-current=true]")).to_have_count(0)


def test_control_assigned_to_step_closes_ics_gap(page: "Page") -> None:
    sign_in(page, "U-013")
    page.goto(BASE + "/processes/P-001?step=Task_Bestellung")
    expect(page.locator("#step-panel")).to_contain_text("IKS-Prüfung", timeout=15000)
    form = page.locator("#step-panel form:has(input[name=kind][value=control])")
    form.locator("select").select_option("K-001")
    form.locator("button").click()
    expect(page.locator("#step-panel .alert-warning")).to_have_count(0)


def test_kpi_value_recorded(page: "Page") -> None:
    sign_in(page, "U-013")
    page.goto(BASE + "/kpi/KPI-003")
    page.fill("#detail input[name=date]", "2026-12-31")
    page.fill("#detail input[name=value]", "100")
    page.click("#detail button:has-text('Wert erfassen')")
    expect(page.locator("#detail")).to_contain_text("Ziel erreicht")
    expect(page.locator("#detail .kpi-chart")).to_be_visible()


def test_delegation_granted_and_accepted(page: "Page") -> None:
    sign_in(page, "U-016")
    page.goto(BASE + "/delegations/DV-017")
    page.click("#detail button[value=grant]")
    expect(page.locator("#detail")).to_contain_text("Erteilt (Erteilende/r)")
    sign_in(page, "U-015")
    expect(page.locator("main")).to_contain_text("DV-017")
    page.goto(BASE + "/delegations/DV-017")
    page.click("#detail button[value=accept]")
    expect(page.locator("#detail .wf-chip.done")).to_have_count(3)


def test_checks_on_role(page: "Page") -> None:
    sign_in(page, "U-013")
    page.goto(BASE + "/roles/RO-007")
    expect(page.locator("#detail .alert-warning")).to_contain_text("Prüfungen zur Rechtssicherheit")


def test_ia_cockpit(page: "Page") -> None:
    sign_in(page, "U-013")
    page.goto(BASE + "/ia")
    expect(page.locator("main")).to_contain_text("Qualitätsprüfungen")
    expect(page.locator(".check-tile")).to_have_count(33)
    page.locator("a[href='/audits/AU-005']").first.click()
    expect(page.locator("#detail")).to_contain_text("Unabhängigkeit")


def test_responsible_person_updates_finding(page: "Page") -> None:
    sign_in(page, "U-002")
    page.goto(BASE + "/audits/AU-001")
    page.locator("#detail table button:has-text('Bearbeiten')").first.click()
    expect(page.locator("#modal-body")).to_contain_text("Als verantwortliche Person")
    page.fill("#modal-body #f-corrective_action", "E2E-Maßnahme")
    page.click("#modal-body button:has-text('Speichern')")
    expect(page.locator("#toasts")).to_contain_text("Gespeichert")
    expect(page.locator("#modal[open]")).to_have_count(0)


def test_excel_export_and_import(page: "Page", tmp_path: Path) -> None:
    import io

    from openpyxl import load_workbook

    sign_in(page, "U-013")
    page.goto(BASE + "/opportunities")
    with page.expect_download() as dl:
        page.click("a[href='/opportunities/export.xlsx']")
    wb = load_workbook(io.BytesIO(Path(dl.value.path()).read_bytes()))
    ws = wb.worksheets[0]
    headers = [c.value for c in ws[1]]
    ws.cell(2, headers.index("Bezeichnung") + 1).value = "E2E geändert"
    target = tmp_path / "opps.xlsx"
    wb.save(target)
    page.click("button[hx-get='/opportunities/import']")
    page.set_input_files("#modal-body input[type=file]", str(target))
    page.click("#modal-body button:has-text('Vorschau anzeigen')")
    expect(page.locator("#modal-body")).to_contain_text("1 geändert")
    page.click("#modal-body button:has-text('übernehmen')")
    expect(page.locator("#modal-body")).to_contain_text("gespeichert")


def test_content_administration(page: "Page") -> None:
    sign_in(page, "U-001")
    page.goto(BASE + "/admin/content?m=opportunity")
    add = page.locator("form[hx-post='/admin/content/opportunity/fields']")
    add.locator("input[name=label]").fill("Investition")
    add.locator("select[name=type]").select_option("select")
    add.locator("textarea").fill("Gering\nHoch")
    add.locator("button").click()
    expect(page.locator("#toasts")).to_contain_text("hinzugefügt")
    expect(page.locator("#content-panel")).to_contain_text("x_investition")
    page.goto(BASE + "/opportunities/CH-001?edit=1")
    page.select_option("#f-x_investition", "Hoch")
    page.click("#detail button:has-text('Speichern')")
    expect(page.locator("#toasts")).to_contain_text("Gespeichert")
    expect(page.locator("#detail")).to_contain_text("Weitere Angaben")
    expect(page.locator("#detail")).to_contain_text("Hoch")


def test_assistant_search_on_start_page(page: "Page") -> None:
    sign_in(page, "U-004")
    page.fill("#assistant input[name=question]", "Wo werden Bestellungen freigegeben?")
    page.click("#assistant button:has-text('Fragen')")
    expect(page.locator("#assistant-log a").first).to_be_visible()
    expect(page.locator("#assistant-log")).to_contain_text("Wo werden Bestellungen freigegeben?")


def test_process_draft_without_ai(page: "Page") -> None:
    sign_in(page, "U-013")
    page.goto(BASE + "/processes")
    page.click("button:has-text('Prozess entwerfen')")
    page.fill(
        "#modal-body textarea[name=text]",
        "Retoure erfassen (Vertrieb)\nWare in Ordnung?\nGutschrift erstellen",
    )
    page.click("#modal-body button:has-text('Ohne KI')")
    expect(page.locator("#modal-body input[name='step.name']")).to_have_count(3)
    page.fill("#modal-body input[name=title]", "E2E Retoure")
    page.click("#modal-body button:has-text('Als Entwurf übernehmen')")
    page.wait_for_url(re.compile(r".*/processes/P-\d+"))
    expect(page.locator("main")).to_contain_text("E2E Retoure")


def test_org_chart_and_role_matrix(page: "Page") -> None:
    sign_in(page, "U-004")
    page.goto(BASE + "/positions")
    page.click("a:has-text('Organigramm')")
    expect(page.locator(".org-tree .org-card").first).to_be_visible()
    page.click("a[role=tab]:has-text('Rollenzuordnungsmatrix')")
    expect(page.locator(".role-matrix tbody tr").first).to_contain_text("ST-001")


def test_bpmn_import_and_call_link(page: "Page") -> None:
    sign_in(page, "U-013")
    page.goto(BASE + "/processes/P-003")
    page.click("button[hx-get$='/diagram/import']")
    page.set_input_files(
        "#modal-body input[type=file]",
        str(Path(__file__).parents[1] / "fixtures" / "call_activity.bpmn"),
    )
    page.click("#modal-body button:has-text('Importieren')")
    page.locator("[data-element-id='Call_Beschaffung']").click()
    page.select_option("#step-panel select[name=target_process_id]", "P-001")
    page.click("#step-panel button:has-text('Verknüpfen')")
    expect(page.locator("#step-panel a[href='/processes/P-001']")).to_be_visible()
    with page.expect_download() as dl:
        page.click("button[data-action=export-svg]")
    assert dl.value.suggested_filename == "P-003.svg"
