"""Controls, KPI with measured values, and GRC elements linked to process steps."""

from tests.api.conftest import Login


async def test_controls_managed_by_ia_owned_by_role(login: Login) -> None:
    employee = await login("U-004")
    assert (await employee.post("/api/v1/controls", json={"title": "X"})).status_code == 403
    k = (await employee.get("/api/v1/controls/K-001")).json()
    assert k["rights"]["can_edit"] is False
    assert k["used_in"]
    assert k["labels"]["R-001"].startswith("R-001")
    ia = await login("U-013")
    r = await ia.post("/api/v1/controls", json={"title": "Neue Kontrolle"})
    assert r.status_code == 201
    created = r.json()
    r = await ia.patch(
        f"/api/v1/controls/{created['id']}",
        json={
            "version": created["version"],
            "values": {"annex_a": ["27001:A.5.15"], "mitigates_risk_ids": ["R-001"]},
        },
    )
    assert r.status_code == 200, r.text
    assert "status" not in r.json()  # no approval workflow
    assert (await ia.delete(f"/api/v1/controls/{created['id']}")).status_code == 204


async def test_kpi_traffic_light_and_measurements(login: Login) -> None:
    ia = await login("U-013")
    k = (await ia.get("/api/v1/kpis/KPI-001")).json()
    assert k["traffic"] == "yellow"
    assert k["can_measure"] is True
    r = await ia.put("/api/v1/kpis/KPI-001/measurements", json={"date": "2026-09-30", "value": 100})
    assert r.status_code == 200, r.text
    assert r.json()["traffic"] == "green"
    # one value per date: a second value replaces the first
    r = await ia.put("/api/v1/kpis/KPI-001/measurements", json={"date": "2026-09-30", "value": 90})
    assert r.json()["traffic"] == "red"
    assert [m["value"] for m in r.json()["measurements"]].count(90) == 1
    r = await ia.delete("/api/v1/kpis/KPI-001/measurements/2026-09-30")
    assert r.status_code == 200
    assert r.json()["traffic"] == "yellow"
    items = {x["id"]: x for x in (await ia.get("/api/v1/kpis")).json()}
    assert items["KPI-003"]["traffic"] == "red"


async def test_only_responsible_persons_measure(login: Login) -> None:
    employee = await login("U-004")
    k = (await employee.get("/api/v1/kpis/KPI-001")).json()
    assert k["can_measure"] is False
    r = await employee.put(
        "/api/v1/kpis/KPI-001/measurements", json={"date": "2026-09-30", "value": 1}
    )
    assert r.status_code == 403


async def test_link_closes_ics_gap_and_counts_as_process_change(login: Login) -> None:
    ia = await login("U-013")
    p = (await ia.get("/api/v1/processes/P-001")).json()
    assert [g["risk_id"] for g in p["ics_gaps"]["Task_Bestellung"]] == ["R-001"]
    assert "K-001" in p["ics_gaps"]["Task_Bestellung"][0]["suggestions"]
    r = await ia.put(
        "/api/v1/processes/P-001/steps/Task_Bestellung/links",
        json={"kind": "control", "target_id": "K-001", "version": p["version"]},
    )
    assert r.status_code == 200, r.text
    after = r.json()
    assert after["version"] == p["version"] + 1
    assert "Task_Bestellung" not in after["ics_gaps"]
    hist = (await ia.get("/api/v1/processes/P-001/history")).json()
    assert any(h["note"] == "{item} assigned to step {step}" for h in hist)
    used = (await ia.get("/api/v1/controls/K-001")).json()["used_in"]
    assert {u["element_id"] for u in used} >= {"Task_Genehmigen", "Task_Bestellung"}
    r = await ia.delete(
        "/api/v1/processes/P-001/steps/Task_Bestellung/links/control/K-001",
        params={"version": after["version"]},
    )
    assert r.status_code == 200, r.text
    assert "Task_Bestellung" in r.json()["ics_gaps"]


async def test_link_rejects_unknown_element_and_stale_version(login: Login) -> None:
    ia = await login("U-013")
    p = (await ia.get("/api/v1/processes/P-001")).json()
    r = await ia.put(
        "/api/v1/processes/P-001/steps/Task_Bestellung/links",
        json={"kind": "control", "target_id": "K-999", "version": p["version"]},
    )
    assert r.status_code == 422
    r = await ia.put(
        "/api/v1/processes/P-001/steps/Task_Bestellung/links",
        json={"kind": "kpi", "target_id": "KPI-001", "version": p["version"] - 1},
    )
    assert r.status_code == 409


async def test_deleting_an_element_removes_its_step_links(login: Login) -> None:
    ia = await login("U-013")
    assert (await ia.delete("/api/v1/risks/R-001")).status_code == 204
    p = (await ia.get("/api/v1/processes/P-001")).json()
    assert all(x["target_id"] != "R-001" for links in p["links"].values() for x in links)
