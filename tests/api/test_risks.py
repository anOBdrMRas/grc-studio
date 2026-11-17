"""Risks and opportunities: everybody records, the recorder edits the own draft, the owner submits, I&A releases."""

from tests.api.conftest import Login


async def test_everybody_records_and_owns_the_draft(login: Login) -> None:
    c = await login("U-004")
    r = await c.post(
        "/api/v1/risks", json={"title": "Lieferant liefert verspätet. Produktion steht."}
    )
    assert r.status_code == 201, r.text
    risk = r.json()
    assert risk["title"] == "Lieferant liefert verspätet"
    assert risk["created_by_user_id"] == "U-004"
    assert risk["owner_user_id"] == "U-004"
    assert risk["rights"]["can_edit"] is True
    assert risk["rights"]["owner_fields"] == []  # the recorder chooses the owner
    assert risk["assessment"] == {"score": 0, "level": "low", "high": False}


async def test_recorder_assesses_and_hands_over(login: Login) -> None:
    c = await login("U-004")
    risk = (await c.post("/api/v1/risks", json={"title": "Ausfall. Details."})).json()
    r = await c.patch(
        f"/api/v1/risks/{risk['id']}",
        json={
            "version": risk["version"],
            "values": {
                "likelihood": 3,
                "impact": 4,
                "description": "Neuer erster Satz. Rest.",
                "actions": [{"text": "Zweitlieferant", "owner_user_id": "U-003"}],
                "owner_user_id": "U-002",
            },
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["assessment"] == {"score": 12, "level": "high", "high": True}
    assert body["title"] == "Neuer erster Satz"
    assert body["labels"]["U-003"]
    # after the hand-over the recorder is no longer owner but still edits the own draft
    assert body["rights"]["is_owner"] is False
    assert body["rights"]["can_edit"] is True


async def test_scale_is_validated(login: Login) -> None:
    c = await login("U-013")
    risk = (await c.get("/api/v1/risks/R-001")).json()
    r = await c.patch(
        "/api/v1/risks/R-001", json={"version": risk["version"], "values": {"impact": 5}}
    )
    assert r.status_code == 422


async def test_others_may_read_but_not_edit(login: Login) -> None:
    c = await login("U-004")
    assert (await c.get("/api/v1/risks")).status_code == 200
    risk = (await c.get("/api/v1/risks/R-001")).json()
    assert risk["rights"]["can_edit"] is False
    r = await c.patch(
        "/api/v1/risks/R-001", json={"version": risk["version"], "values": {"cause": "x"}}
    )
    assert r.status_code == 403
    assert (await c.delete("/api/v1/risks/R-001")).status_code == 403


async def test_owner_cannot_reassign_released_risk(login: Login) -> None:
    owner = await login("U-002")  # owner of R-001
    risk = (await owner.get("/api/v1/risks/R-001")).json()
    assert risk["rights"]["owner_fields"] == ["owner_user_id"]
    r = await owner.patch(
        "/api/v1/risks/R-001",
        json={"version": risk["version"], "values": {"owner_user_id": "U-004"}},
    )
    assert r.status_code == 403
    # an owner edit of a released risk reopens it
    r = await owner.patch(
        "/api/v1/risks/R-001", json={"version": risk["version"], "values": {"review_note": "neu"}}
    )
    assert r.json()["status"] == "draft"
    assert r.json()["released"] is not None


async def test_recorder_deletes_only_unsubmitted_draft(login: Login) -> None:
    c = await login("U-004")
    first = (await c.post("/api/v1/risks", json={"title": "Eins."})).json()
    assert first["rights"]["can_delete"] is True
    assert (await c.delete(f"/api/v1/risks/{first['id']}")).status_code == 204
    second = (await c.post("/api/v1/risks", json={"title": "Zwei."})).json()
    r = await c.post(
        f"/api/v1/risks/{second['id']}/workflow",
        json={"action": "submit", "version": second["version"]},
    )
    assert r.status_code == 200, r.text
    ia = await login("U-013")
    back = await ia.post(
        f"/api/v1/risks/{second['id']}/workflow",
        json={"action": "reject", "comment": "Bitte bewerten", "version": r.json()["version"]},
    )
    assert back.json()["status"] == "draft"
    again = (await c.get(f"/api/v1/risks/{second['id']}")).json()
    assert again["rights"]["can_delete"] is False
    assert (await c.delete(f"/api/v1/risks/{second['id']}")).status_code == 403


async def test_four_eyes_on_risks(login: Login) -> None:
    ia = await login("U-013")
    risk = (await ia.post("/api/v1/risks", json={"title": "Eigenes Risiko."})).json()
    r = await ia.post(
        f"/api/v1/risks/{risk['id']}/workflow",
        json={"action": "submit", "version": risk["version"]},
    )
    r = await ia.post(
        f"/api/v1/risks/{risk['id']}/workflow",
        json={"action": "approve", "version": r.json()["version"]},
    )
    assert r.status_code == 409
    assert r.json()["code"] == "four_eyes"


async def test_opportunity_owned_by_role_holders(login: Login) -> None:
    c = await login("U-004")
    opp = (await c.get("/api/v1/opportunities/CH-001")).json()
    assert opp["potential"] == opp["likelihood"] * opp["benefit_score"]
    created = await c.post("/api/v1/opportunities", json={"title": "Neue Chance"})
    assert created.status_code == 201
    assert created.json()["rights"]["can_edit"] is True
    items = (await c.get("/api/v1/opportunities")).json()
    assert {"CH-001", created.json()["id"]} <= {x["id"] for x in items}


async def test_catalogues_carry_the_risk_lists(login: Login) -> None:
    c = await login("U-004")
    lists = (await c.get("/api/v1/meta/catalogs")).json()["lists"]
    assert len(lists["risk_matrix"]) == 16
    assert lists["impact:Economic loss"][3] == "≥ 3 m USD"
