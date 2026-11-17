"""Browser tests against a running stack (API + interface + demo data).

E2E_BASE_URL=http://localhost:8080 uv run pytest -m e2e
They change data: run them against a fresh demo database only.
"""

import os
import re
from collections.abc import Iterator

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
