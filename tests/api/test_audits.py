"""Audits, findings and the I&A cockpit."""

from tests.api.conftest import Login


async def test_audit_read_and_create_rights(login: Login) -> None:
    employee = await login("U-004")
    a = (await employee.get("/api/v1/audits/AU-001")).json()
    assert a["rights"]["can_edit"] is False
    assert {f["code"] for f in a["findings"]} >= {"F-001", "F-002", "F-003"}
    assert (await employee.post("/api/v1/audits", json={"title": "X"})).status_code == 403
    ia = await login("U-013")
    r = await ia.post("/api/v1/audits", json={"title": "Internes Audit IT"})
    assert r.status_code == 201
    assert r.json()["audit_status"] == "Planned"


async def test_findings_by_auditor(login: Login) -> None:
    ia = await login("U-013")
    a = (
        await ia.post("/api/v1/audits/AU-001/findings", json={"description": "Neue Beobachtung"})
    ).json()
    new = next(f for f in a["findings"] if f["description"] == "Neue Beobachtung")
    assert new["code"] == "F-006"
    r = await ia.patch(
        f"/api/v1/audits/AU-001/findings/{new['id']}",
        json={
            "version": new["version"],
            "values": {"status": "Closed", "verification_result": "ok"},
        },
    )
    assert r.status_code == 200, r.text
    changed = next(f for f in r.json()["findings"] if f["id"] == new["id"])
    assert changed["status"] == "Closed"
    assert changed["open"] is False
    hist = (await ia.get("/api/v1/audits/AU-001/history")).json()
    assert any(h["note"] == "Finding {code} changed" for h in hist)
    r = await ia.delete(f"/api/v1/audits/AU-001/findings/{new['id']}")
    assert all(f["id"] != new["id"] for f in r.json()["findings"])


async def test_responsible_person_documents_but_cannot_close(login: Login) -> None:
    owner = await login("U-002")  # responsible for F-001
    a = (await owner.get("/api/v1/audits/AU-001")).json()
    f = next(x for x in a["findings"] if x["code"] == "F-001")
    assert f["is_responsible"] is True
    assert f["can_edit"] is False
    r = await owner.patch(
        "/api/v1/audits/AU-001/findings/F-001",
        json={
            "version": f["version"],
            "values": {"corrective_action": "Neu", "status": "In progress"},
        },
    )
    assert r.status_code == 200, r.text
    f = next(x for x in r.json()["findings"] if x["code"] == "F-001")
    r = await owner.patch(
        "/api/v1/audits/AU-001/findings/F-001",
        json={"version": f["version"], "values": {"status": "Closed"}},
    )
    assert r.status_code == 403
    r = await owner.patch(
        "/api/v1/audits/AU-001/findings/F-001",
        json={"version": f["version"], "values": {"due_date": "2030-01-01"}},
    )
    assert r.status_code == 403


async def test_stale_finding_version(login: Login) -> None:
    ia = await login("U-013")
    f = next(
        x
        for x in (await ia.get("/api/v1/audits/AU-001")).json()["findings"]
        if x["code"] == "F-002"
    )
    ok = await ia.patch(
        "/api/v1/audits/AU-001/findings/F-002",
        json={"version": f["version"], "values": {"evidence": "a"}},
    )
    assert ok.status_code == 200
    stale = await ia.patch(
        "/api/v1/audits/AU-001/findings/F-002",
        json={"version": f["version"], "values": {"evidence": "b"}},
    )
    assert stale.status_code == 409


async def test_independence_is_reported(login: Login) -> None:
    ia = await login("U-013")
    a = (await ia.get("/api/v1/audits/AU-005")).json()
    assert a["independence"]


async def test_cockpit(login: Login) -> None:
    employee = await login("U-004")
    assert (await employee.get("/api/v1/cockpit")).status_code == 403
    ia = await login("U-013")
    data = (await ia.get("/api/v1/cockpit")).json()
    keys = {c["key"]: c for c in data["checks"]}
    assert len(keys) == 33
    assert keys["audit-findings-overdue"]["items"]
    assert keys["audit-independence"]["items"][0]["id"] == "AU-005"
    assert {r["kind"] for r in data["review_queue"]} >= {"process", "role", "risk"}
    assert data["workflow"]["process"]["total"] == 12
    assert 0 <= data["grades"]["role"] <= 100
    admin = await login("U-001")
    assert (await admin.get("/api/v1/cockpit")).status_code == 200
