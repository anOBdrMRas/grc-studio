"""Delegations: grant by the grantor, acceptance by the recipient, checks."""

from tests.api.conftest import Login


async def test_grant_and_accept(login: Login) -> None:
    grantor = await login("U-016")  # grantor of DV-017
    m = (await grantor.get("/api/v1/mandates/DV-017")).json()
    assert m["state"] == "draft"
    assert m["actions"]["can_grant"] is True
    assert m["actions"]["can_accept"] is False
    r = await grantor.post(
        "/api/v1/mandates/DV-017/workflow", json={"action": "grant", "version": m["version"]}
    )
    assert r.status_code == 200, r.text
    granted = r.json()
    assert granted["status"] == "granted"
    assert granted["valid_from"]  # kept: it was set already
    # the grantor cannot accept for the recipient
    r = await grantor.post(
        "/api/v1/mandates/DV-017/workflow", json={"action": "accept", "version": granted["version"]}
    )
    assert r.status_code == 403
    recipient = await login("U-015")
    r = await recipient.post(
        "/api/v1/mandates/DV-017/workflow", json={"action": "accept", "version": granted["version"]}
    )
    assert r.status_code == 200, r.text
    assert r.json()["accepted_at"]
    assert [w["step"] for w in r.json()["workflow"]][-2:] == ["granted", "accepted"]


async def test_revoke_by_management(login: Login) -> None:
    ia = await login("U-013")
    m = (await ia.get("/api/v1/mandates/DV-008")).json()
    assert m["state"] == "active"
    r = await ia.post(
        "/api/v1/mandates/DV-008/workflow", json={"action": "revoke", "version": m["version"]}
    )
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "revoked"
    assert r.json()["revoked_at"]
    assert r.json()["rights"]["can_edit"] is True  # managers still correct a revoked one


async def test_status_cannot_be_patched(login: Login) -> None:
    ia = await login("U-013")
    m = (await ia.get("/api/v1/mandates/DV-017")).json()
    r = await ia.patch(
        "/api/v1/mandates/DV-017", json={"version": m["version"], "values": {"status": "granted"}}
    )
    assert r.status_code == 422


async def test_grantor_cannot_change_grantor(login: Login) -> None:
    grantor = await login("U-016")
    m = (await grantor.get("/api/v1/mandates/DV-017")).json()
    assert m["rights"]["can_edit"] is True
    r = await grantor.patch(
        "/api/v1/mandates/DV-017",
        json={"version": m["version"], "values": {"granted_by_user_id": "U-004"}},
    )
    assert r.status_code == 403


async def test_checks_and_filters(login: Login) -> None:
    c = await login("U-004")
    all_checks = (await c.get("/api/v1/checks")).json()
    assert any(x["kind"] == "role" and x["element_id"] == "RO-007" for x in all_checks)
    dv8 = (await c.get("/api/v1/checks", params={"mandate_id": "DV-008"})).json()
    assert {x["message"] for x in dv8} >= {
        "{mandate}: amount limit {amount} EUR above the limit of the position ({limit} EUR)."
    }
    mine = (await c.get("/api/v1/checks", params={"user_id": "U-003"})).json()
    assert mine
    assert all(x["user_id"] == "U-003" for x in mine)
    m = (await c.get("/api/v1/mandates/DV-008")).json()
    assert m["checks"] == dv8


async def test_only_managers_create(login: Login) -> None:
    c = await login("U-004")
    assert (await c.post("/api/v1/mandates", json={"title": "X"})).status_code == 403
    ia = await login("U-013")
    r = await ia.post("/api/v1/mandates", json={"title": "Neue Vollmacht"})
    assert r.status_code == 201
    assert r.json()["code"] == "DV-019"
