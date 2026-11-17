"""Interface without a running API: templates, security headers, sign-in redirect, form parsing."""

from fastapi.testclient import TestClient
from starlette.datastructures import FormData

from grc_ui.formdata import values_from_form
from grc_ui.forms import FORMS
from grc_ui.main import app
from grc_ui.security import CSP
from grc_ui.templating import env


def test_all_templates_compile() -> None:
    names = env.list_templates(extensions=["html"])
    assert len(names) > 20
    for name in names:
        env.get_template(name)


def test_security_headers_and_csp() -> None:
    r = TestClient(app).get("/static/favicon.svg")
    assert r.status_code == 200
    assert r.headers["Content-Security-Policy"] == CSP
    assert "'unsafe-inline'" not in CSP.split("script-src")[1].split(";")[0]
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["X-Content-Type-Options"] == "nosniff"


def test_pages_need_sign_in() -> None:
    r = TestClient(app, follow_redirects=False).get("/roles")
    assert r.status_code in (302, 303)
    assert r.headers["location"].endswith("/login")


def test_htmx_requests_redirect_via_header() -> None:
    r = TestClient(app, follow_redirects=False).get("/roles", headers={"HX-Request": "true"})
    assert r.headers.get("HX-Redirect", r.headers.get("location", "")).endswith("/login")


def test_form_values() -> None:
    form = FormData(
        [
            ("title", "Rolle"),
            ("mandatory", "on"),
            ("iso_refs", "ISO 9001 5.3"),
            ("iso_refs", ""),
            ("iso_refs", "ISO 37301 5.3.2"),
            ("role_owner_user_id", ""),
        ]
    )
    values = values_from_form(FORMS["role"], form, editable_owner=True)
    assert values["title"] == "Rolle"
    assert values["mandatory"] is True
    assert values["compliance_relevant"] is False
    assert values["iso_refs"] == ["ISO 9001 5.3", "ISO 37301 5.3.2"]
    assert values["role_owner_user_id"] is None


def test_owner_fields_kept_when_not_editable() -> None:
    values = values_from_form(
        FORMS["role"],
        FormData([("title", "x"), ("role_owner_user_id", "U-001")]),
        editable_owner=False,
    )
    assert "role_owner_user_id" not in values


def test_risk_form_values() -> None:
    form = FormData(
        [
            ("likelihood", "3"),
            ("impact", "x"),
            ("actions.text", "Zweitlieferant"),
            ("actions.owner_user_id", "U-003"),
            ("actions.text", "  "),
            ("actions.owner_user_id", ""),
            ("process_ids", "P-001"),
            ("assessment", "ignored"),
        ]
    )
    values = values_from_form(FORMS["risk"], form, editable_owner=True)
    assert values["likelihood"] == 3
    assert values["impact"] == 0
    assert values["actions"] == [{"text": "Zweitlieferant", "owner_user_id": "U-003"}]
    assert values["process_ids"] == ["P-001"]
    assert "assessment" not in values
    assert "scale_guide" not in values


def test_kpi_form_decimals() -> None:
    form = FormData([("target", "99,5"), ("warning", "x"), ("critical", "95")])
    values = values_from_form(FORMS["kpi"], form, editable_owner=True)
    assert values["target"] == 99.5
    assert values["warning"] == 0.0
    assert values["critical"] == 95.0


def test_number_filter() -> None:
    from grc_ui.templating import num

    assert num(99.0) == "99"
    assert num(2.40) == "2.4"
    assert num(10.05) == "10.05"


def test_sparkline_scales_into_the_box() -> None:
    from grc_ui.charts import HEIGHT, sparkline

    s = sparkline([1.0, 2.0, 3.0], target=3.0)
    assert s is not None
    ys = [y for _, y in s["dots"]]
    assert ys[0] > ys[-1]  # higher values are drawn higher
    assert all(0 <= y <= HEIGHT for y in ys)
    assert sparkline([]) is None


def test_check_text_translates_type_and_amounts() -> None:
    from grc_ui.i18n import current_language
    from grc_ui.templating import check_text

    check = {
        "message": "{mandate}: amount limit {amount} EUR above the limit of the position ({limit} EUR).",
        "vars": {"mandate": "DV-8", "amount": "25000", "limit": "10000", "user": "Anna"},
    }
    token = current_language.set("de")
    try:
        assert (
            check_text(check)
            == "DV-8: Betragsgrenze 25.000 EUR über dem Limit der Stelle (10.000 EUR)."
        )
        role = {
            "message": "{role}: {user} has no effective {type}.",
            "vars": {"role": "DPO", "user": "Anna", "type": "Appointment / designation"},
        }
        assert check_text(role) == "„DPO“: Anna hat keine wirksame Bestellung / Benennung."
    finally:
        current_language.reset(token)
