"""Content administration: custom fields, additional dropdown values, custom values of elements."""

from typing import Any

import httpx

from tests.api.conftest import Login

RISK_FIELDS = [
    {"label": "Budget (EUR)", "type": "number", "section": "Assessment"},
    {"label": "Rating agency", "type": "select", "options": ["A", "B"]},
    {"label": "Contact", "type": "user"},
]


async def _configure(admin: httpx.AsyncClient, **extra: Any) -> dict[str, Any]:
    cur = (await admin.get("/api/v1/content")).json()
    r = await admin.put(
        "/api/v1/content",
        json={"version": cur["version"], "fields": {"risk": RISK_FIELDS}} | extra,
    )
    assert r.status_code == 200, r.text
    return dict(r.json())


async def test_only_admins_maintain_the_content(login: Login) -> None:
    employee = await login("U-004")
    cur = (await employee.get("/api/v1/content")).json()
    assert cur == cur | {"version": 0, "fields": {}, "options": {}}
    r = await employee.put("/api/v1/content", json={"version": 0, "fields": {}})
    assert r.status_code == 403
    ia = await login("U-013")
    assert (await ia.put("/api/v1/content", json={"version": 0})).status_code == 403


async def test_keys_are_assigned_and_kept(login: Login) -> None:
    admin = await login("U-001")
    cfg = await _configure(admin, options={"risk.category": ["Supply chain"]})
    keys = [f["key"] for f in cfg["fields"]["risk"]]
    assert keys == ["x_budget_eur", "x_rating_agency", "x_contact"]
    assert cfg["options"] == {"risk.category": ["Supply chain"]}
    assert cfg["version"] == 1
    # a field left out is not deleted but hidden; its type cannot change
    r = await admin.put(
        "/api/v1/content",
        json={"version": 1, "fields": {"risk": [cfg["fields"]["risk"][0] | {"type": "text"}]}},
    )
    assert r.status_code == 422
    r = await admin.put(
        "/api/v1/content", json={"version": 1, "fields": {"risk": [cfg["fields"]["risk"][0]]}}
    )
    fields = {f["key"]: f for f in r.json()["fields"]["risk"]}
    assert fields["x_rating_agency"]["removed"] is True
    assert fields["x_budget_eur"]["removed"] is False
    # stale version
    r = await admin.put("/api/v1/content", json={"version": 1, "fields": {}})
    assert r.status_code == 409
    # unknown dropdown field
    r = await admin.put("/api/v1/content", json={"version": 2, "options": {"risk.nope": ["x"]}})
    assert r.status_code == 422


async def test_custom_values_are_checked_and_recorded(login: Login) -> None:
    admin = await login("U-001")
    await _configure(admin)
    ia = await login("U-013")
    risk = (await ia.get("/api/v1/risks/R-001")).json()
    assert risk["custom"] == {}
    bad = await ia.patch(
        "/api/v1/risks/R-001",
        json={"version": risk["version"], "values": {"x_budget_eur": "a lot"}},
    )
    assert bad.status_code == 422
    unknown = await ia.patch(
        "/api/v1/risks/R-001", json={"version": risk["version"], "values": {"x_nope": "1"}}
    )
    assert unknown.status_code == 422
    wrong_option = await ia.patch(
        "/api/v1/risks/R-001",
        json={"version": risk["version"], "values": {"x_rating_agency": "C"}},
    )
    assert wrong_option.status_code == 422
    nobody = await ia.patch(
        "/api/v1/risks/R-001",
        json={"version": risk["version"], "values": {"x_contact": "U-999"}},
    )
    assert nobody.status_code == 422
    r = await ia.patch(
        "/api/v1/risks/R-001",
        json={
            "version": risk["version"],
            "values": {"x_budget_eur": 25000, "x_rating_agency": "A", "x_contact": "U-002"},
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["custom"] == {
        "x_budget_eur": 25000,
        "x_rating_agency": "A",
        "x_contact": "U-002",
    }
    first = r.json()
    r = await ia.patch(
        "/api/v1/risks/R-001",
        json={"version": first["version"], "values": {"x_budget_eur": 30000}},
    )
    assert r.status_code == 200, r.text
    hist = (await ia.get("/api/v1/risks/R-001/history")).json()
    entry = next(h for h in hist if {c["key"] for c in h["changes"]} >= {"x_contact"})
    assert {"x_budget_eur", "x_rating_agency"} <= {c["key"] for c in entry["changes"]}
    # the state after that change shows the value it set, not the later one
    state = (await ia.get(f"/api/v1/risks/R-001/history/{entry['id']}")).json()
    assert state["values"]["x_budget_eur"] == 25000


async def test_custom_values_of_users(login: Login) -> None:
    admin = await login("U-001")
    cur = (await admin.get("/api/v1/content")).json()
    r = await admin.put(
        "/api/v1/content",
        json={
            "version": cur["version"],
            "fields": {"user": [{"label": "Badge number", "type": "text"}]},
        },
    )
    assert r.status_code == 200, r.text
    u = (await admin.get("/api/v1/users/U-004")).json()
    r = await admin.patch(
        "/api/v1/users/U-004", json={"version": u["version"], "values": {"x_badge_number": "4711"}}
    )
    assert r.status_code == 200, r.text
    assert r.json()["custom"] == {"x_badge_number": "4711"}


async def test_empty_values_of_unfilled_fields_are_no_change(login: Login) -> None:
    admin = await login("U-001")
    await _configure(admin)
    risk = (await admin.get("/api/v1/risks/R-002")).json()
    r = await admin.patch(
        "/api/v1/risks/R-002",
        json={"version": risk["version"], "values": {"x_budget_eur": None}},
    )
    assert r.status_code == 200, r.text
    assert r.json()["custom"] == {}
    assert r.json()["version"] == risk["version"]
