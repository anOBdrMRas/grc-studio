"""Optimistic versioning, approval workflow with four-eyes principle, history."""

from tests.api.conftest import Login


async def test_stale_version_is_rejected(login: Login) -> None:
    c = await login("U-013")
    role = (await c.get("/api/v1/roles/RO-006")).json()
    v = role["version"]
    assert (
        await c.patch("/api/v1/roles/RO-006", json={"version": v, "values": {"trainings": "A"}})
    ).status_code == 200
    stale = await c.patch("/api/v1/roles/RO-006", json={"version": v, "values": {"trainings": "B"}})
    assert stale.status_code == 409
    assert stale.json()["code"] == "version_conflict"
    via_header = await c.patch(
        "/api/v1/roles/RO-006", headers={"If-Match": f'"{v}"'}, json={"values": {"trainings": "B"}}
    )
    assert via_header.status_code == 412
    assert (
        await c.patch("/api/v1/roles/RO-006", json={"values": {"trainings": "B"}})
    ).status_code == 428


async def test_unknown_field_is_rejected(login: Login) -> None:
    c = await login("U-013")
    role = (await c.get("/api/v1/roles/RO-006")).json()
    r = await c.patch(
        "/api/v1/roles/RO-006", json={"version": role["version"], "values": {"nope": 1}}
    )
    assert r.status_code == 422


async def test_workflow_with_four_eyes(login: Login) -> None:
    ia = await login("U-013")
    created = (await ia.post("/api/v1/roles", json={"title": "Prüfrolle"})).json()
    rid, v = created["id"], created["version"]
    assert created["status"] == "draft"
    # I&A submits itself and may then not approve
    r = await ia.post(f"/api/v1/roles/{rid}/workflow", json={"action": "submit", "version": v})
    assert r.status_code == 200, r.text
    r = await ia.post(
        f"/api/v1/roles/{rid}/workflow", json={"action": "approve", "version": r.json()["version"]}
    )
    assert r.status_code == 409
    assert r.json()["code"] == "four_eyes"
    # the administration may set the status but not give the quality approval
    admin = await login("U-001")
    cur = (await admin.get(f"/api/v1/roles/{rid}")).json()
    r = await admin.post(
        f"/api/v1/roles/{rid}/workflow", json={"action": "approve", "version": cur["version"]}
    )
    assert r.status_code == 403


async def test_release_by_second_person(login: Login) -> None:
    owner = await login("U-010")
    role = (await owner.get("/api/v1/roles/RO-006")).json()
    if role["status"] == "released":  # owner edit reopens a released role
        r = await owner.patch(
            "/api/v1/roles/RO-006",
            json={"version": role["version"], "values": {"trainings": "neu"}},
        )
        role = r.json()
        assert role["status"] == "draft"
        assert role["released"] is not None
    r = await owner.post(
        "/api/v1/roles/RO-006/workflow", json={"action": "submit", "version": role["version"]}
    )
    assert r.json()["status"] == "review"
    ia = await login("U-013")
    r = await ia.post(
        "/api/v1/roles/RO-006/workflow",
        json={"action": "approve", "version": r.json()["version"], "comment": "ok"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "released"
    assert body["released"] is None
    assert [w["step"] for w in body["workflow"]][-2:] == ["submitted", "approved"]


async def test_history_and_state(login: Login) -> None:
    c = await login("U-013")
    role = (await c.get("/api/v1/roles/RO-006")).json()
    old = role["trainings"]
    await c.patch(
        "/api/v1/roles/RO-006", json={"version": role["version"], "values": {"trainings": "Neu 1"}}
    )
    hist = (await c.get("/api/v1/roles/RO-006/history")).json()
    last = hist[0] if hist[0]["changes"] else hist[-1]
    assert any(ch["key"] == "trainings" and ch["to"] == "Neu 1" for ch in last["changes"])
    # the state before the change: an older revision shows the old value
    older = [h for h in hist if h["id"] != last["id"]]
    if older:
        st = (await c.get(f"/api/v1/roles/RO-006/history/{older[0]['id']}")).json()
        assert st["values"]["trainings"] == old
