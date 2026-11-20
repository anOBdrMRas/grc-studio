"""Work instructions: I&A creates, the owner writes and submits, I&A releases; rich text is
sanitised; assignment to process steps; description of a step."""

from tests.api.conftest import Login


async def test_demo_and_rights(login: Login) -> None:
    employee = await login("U-004")
    items = {x["code"]: x for x in (await employee.get("/api/v1/instructions")).json()}
    assert items["WI-001"]["steps"] == 1
    assert items["WI-001"]["owner_name"]
    wi = (await employee.get("/api/v1/instructions/WI-001")).json()
    assert wi["used_in"][0]["element_id"] == "Task_Genehmigen"
    assert wi["rights"]["can_edit"] is False
    r = await employee.post("/api/v1/instructions", json={"title": "x"})
    assert r.status_code == 403


async def test_owner_writes_submits_and_ia_releases(login: Login) -> None:
    ia = await login("U-013")
    wi = (await ia.post("/api/v1/instructions", json={"title": "Wareneingang prüfen"})).json()
    assert wi["status"] == "draft"
    wi = (
        await ia.patch(
            f"/api/v1/instructions/{wi['id']}",
            json={"version": wi["version"], "values": {"owner_user_id": "U-002"}},
        )
    ).json()
    owner = await login("U-002")
    r = await owner.patch(
        f"/api/v1/instructions/{wi['id']}",
        json={
            "version": wi["version"],
            "values": {
                "content": '<h2 onclick="x()">Prüfen</h2><script>alert(1)</script>'
                '<p style="text-align: center; color: red">Text <a href="javascript:x">a</a></p>'
                '<img src="data:image/png;base64,iVBORw0KGgo=" onerror="x()">'
                '<table><tbody><tr><th>Merkmal</th><td colspan="2">Soll</td></tr></tbody></table>'
            },
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    html = body["content"]
    assert "<script" not in html
    assert "onclick" not in html
    assert "onerror" not in html
    assert "javascript:" not in html
    assert "color" not in html
    assert 'style="text-align: center"' in html or 'style="text-align:center"' in html
    assert 'src="data:image/png;base64,iVBORw0KGgo="' in html
    assert '<td colspan="2">' in html
    r = await owner.post(
        f"/api/v1/instructions/{wi['id']}/workflow",
        json={"action": "submit", "version": body["version"]},
    )
    assert r.status_code == 200, r.text
    wi = r.json()
    assert wi["status"] == "review"
    assert wi["rights"]["can_edit"] is False  # frozen while in review
    r = await ia.post(
        f"/api/v1/instructions/{wi['id']}/workflow",
        json={"action": "approve", "version": wi["version"]},
    )
    assert r.json()["status"] == "released"
    assert r.json()["doc_version"] == "1.0"
    history = (await ia.get(f"/api/v1/instructions/{wi['id']}/history")).json()
    content_changes = [c for h in history for c in h["changes"] if c["key"] == "content"]
    assert content_changes
    assert "<" not in str(content_changes[0]["to"])  # plain text in the history


async def test_unsafe_image_and_size_refused(login: Login) -> None:
    ia = await login("U-013")
    wi = (await ia.get("/api/v1/instructions/WI-003")).json()
    r = await ia.patch(
        "/api/v1/instructions/WI-003",
        json={
            "version": wi["version"],
            "values": {"content": '<p>x<img src="data:text/html;base64,PHNjcmlwdD4="></p>'},
        },
    )
    assert 'src="data:text/html' not in r.json()["content"]
    big = "<p>" + "a" * (8 * 1024 * 1024 + 1) + "</p>"
    r = await ia.patch(
        "/api/v1/instructions/WI-003",
        json={"version": r.json()["version"], "values": {"content": big}},
    )
    assert r.status_code == 422


async def test_step_links_notes_and_delete(login: Login) -> None:
    ia = await login("U-013")
    p = (await ia.get("/api/v1/processes/P-003")).json()
    assert p["activities"]["P003_T3"] == "Budget planen"
    assert p["step_notes"]["P003_T3"].startswith("Die Bereiche planen")
    assert [x["code"] for x in p["links"]["P003_T3"]] == ["WI-002"]
    r = await ia.put(
        "/api/v1/processes/P-003/steps/P003_T2/note",
        json={"text": "  Ziele aus der Strategie ableiten.  ", "version": p["version"]},
    )
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["step_notes"]["P003_T2"] == "Ziele aus der Strategie ableiten."
    r = await ia.put(
        "/api/v1/processes/P-003/steps/P003_T2/links",
        json={"kind": "instruction", "target_id": "WI-003", "version": p["version"]},
    )
    assert r.status_code == 200, r.text
    wi = (await ia.get("/api/v1/instructions/WI-003")).json()
    assert {u["element_id"] for u in wi["used_in"]} == {"Task_Rechnung", "P003_T2"}
    history = (await ia.get("/api/v1/processes/P-003/history")).json()
    assert any(h["note"] == "Description of step {step} changed" for h in history)
    # an employee who does not own the process may not describe its steps
    employee = await login("U-004")
    p = (await employee.get("/api/v1/processes/P-003")).json()
    r = await employee.put(
        "/api/v1/processes/P-003/steps/P003_T2/note", json={"text": "x", "version": p["version"]}
    )
    assert r.status_code == 403
    assert (await ia.delete("/api/v1/instructions/WI-003")).status_code == 204
    p = (await ia.get("/api/v1/processes/P-003")).json()
    assert "P003_T2" not in p["links"] or all(
        x["target_id"] != "WI-003" for x in p["links"]["P003_T2"]
    )
