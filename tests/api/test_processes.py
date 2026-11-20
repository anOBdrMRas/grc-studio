"""Processes: diagram with version check, step assignments, rights."""

from tests.api.conftest import Login

DIAGRAM = (
    '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D">'
    '<bpmn:process id="P1"><bpmn:task id="T1" name="Prüfen"/></bpmn:process></bpmn:definitions>'
)


async def test_landscape_lists_processes(login: Login) -> None:
    c = await login("U-004")
    items = (await c.get("/api/v1/processes")).json()
    assert len(items) >= 12


async def test_landscape_counts_my_steps(login: Login) -> None:
    """Steps of the processes in which a role of the user is assigned (column "My involvement")."""
    c = await login("U-002")
    items = {x["code"]: x for x in (await c.get("/api/v1/processes")).json()}
    assert items["P-001"]["is_owner"]
    assert items["P-001"]["my_steps"] == 4
    assert items["P-004"]["my_steps"] == 0


async def test_diagram_save_and_conflict(login: Login) -> None:
    c = await login("U-013")
    d = (await c.get("/api/v1/processes/P-008/diagram")).json()
    r = await c.put(
        "/api/v1/processes/P-008/diagram", json={"xml": DIAGRAM, "version": d["version"]}
    )
    assert r.status_code == 200, r.text
    assert r.json()["version"] == d["version"] + 1
    stale = await c.put(
        "/api/v1/processes/P-008/diagram",
        json={"xml": DIAGRAM.replace("Prüfen", "X"), "version": d["version"]},
    )
    assert stale.status_code == 409
    hist = (await c.get("/api/v1/processes/P-008/history")).json()
    assert any(h["action"] == "diagram" for h in hist)


async def test_invalid_diagram_rejected(login: Login) -> None:
    c = await login("U-013")
    d = (await c.get("/api/v1/processes/P-008/diagram")).json()
    r = await c.put(
        "/api/v1/processes/P-008/diagram",
        json={"xml": "<svg>" + "x" * 30 + "</svg>", "version": d["version"]},
    )
    assert r.status_code == 422
    bomb = '<?xml version="1.0"?><!DOCTYPE d [<!ENTITY a "aaaaaaaaaa">]><d>&a;&a;</d>'
    r = await c.put("/api/v1/processes/P-008/diagram", json={"xml": bomb, "version": d["version"]})
    assert r.status_code == 422


async def test_employee_cannot_change_foreign_diagram(login: Login) -> None:
    c = await login("U-004")
    d = (await c.get("/api/v1/processes/P-008/diagram")).json()
    r = await c.put(
        "/api/v1/processes/P-008/diagram", json={"xml": DIAGRAM, "version": d["version"]}
    )
    assert r.status_code == 403


async def test_step_role_assignment(login: Login) -> None:
    c = await login("U-013")
    p = (await c.get("/api/v1/processes/P-008")).json()
    step = next(iter(p["steps"]))
    r = await c.put(
        f"/api/v1/processes/P-008/steps/{step}/roles",
        json={"role_id": "RO-001", "raci": "C", "version": p["version"]},
    )
    assert r.status_code == 200, r.text
    after = r.json()
    assert any(s["role_id"] == "RO-001" and s["raci"] == "C" for s in after["steps"][step])
    r = await c.delete(
        f"/api/v1/processes/P-008/steps/{step}/roles/RO-001",
        headers={"If-Match": f'"{after["version"]}"'},
    )
    assert r.status_code == 200, r.text
    assert all(s["role_id"] != "RO-001" for s in r.json()["steps"][step])


async def test_call_activity_links(login: "Login") -> None:
    from pathlib import Path

    ia = await login("U-013")
    xml = (Path(__file__).parents[1] / "fixtures" / "call_activity.bpmn").read_text()
    p = (await ia.get("/api/v1/processes/P-003")).json()
    r = await ia.put("/api/v1/processes/P-003/diagram", json={"xml": xml, "version": p["version"]})
    assert r.status_code == 200, r.text
    p = (await ia.get("/api/v1/processes/P-003")).json()
    assert p["call_activities"] == {"Call_Beschaffung": "Beschaffung durchführen"}
    url = "/api/v1/processes/P-003/steps/{}/call"
    bad = await ia.put(
        url.format("Task_Budget"), json={"target_process_id": "P-001", "version": p["version"]}
    )
    assert bad.status_code == 422  # not a call activity
    own = await ia.put(
        url.format("Call_Beschaffung"), json={"target_process_id": "P-003", "version": p["version"]}
    )
    assert own.status_code == 422
    r = await ia.put(
        url.format("Call_Beschaffung"), json={"target_process_id": "P-001", "version": p["version"]}
    )
    assert r.status_code == 200, r.text
    assert r.json()["calls"]["Call_Beschaffung"]["code"] == "P-001"
    called = (await ia.get("/api/v1/processes/P-001")).json()["called_by"]
    assert [(c["process_id"], c["element_name"]) for c in called] == [
        ("P-003", "Beschaffung durchführen")
    ]
    hist = (await ia.get("/api/v1/processes/P-003/history")).json()
    assert hist[-1]["note"] == "{step} calls {process}"
    stale = await ia.put(
        url.format("Call_Beschaffung"), json={"target_process_id": None, "version": p["version"]}
    )
    assert stale.status_code == 409
    r = await ia.put(
        url.format("Call_Beschaffung"),
        json={"target_process_id": None, "version": r.json()["version"]},
    )
    assert r.json()["calls"] == {}
    employee = await login("U-004")
    v = r.json()["version"]
    denied = await employee.put(
        url.format("Call_Beschaffung"), json={"target_process_id": "P-001", "version": v}
    )
    assert denied.status_code == 403
