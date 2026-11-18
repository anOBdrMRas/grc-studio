"""Permissions by system role and ownership."""

from tests.api.conftest import Login


async def test_employee_reads_but_cannot_manage(login: Login) -> None:
    c = await login("U-004")
    assert (await c.get("/api/v1/roles")).status_code == 200
    assert (await c.post("/api/v1/roles", json={"title": "X"})).status_code == 403
    assert (await c.get("/api/v1/users")).status_code == 403


async def test_ia_manages_modules_but_not_users(login: Login) -> None:
    c = await login("U-013")
    assert (await c.post("/api/v1/processes", json={"title": "Neuer Prozess"})).status_code == 201
    assert (await c.get("/api/v1/users")).status_code == 403
    assert (await c.get("/api/v1/people")).status_code == 200


async def test_admin_manages_users(login: Login) -> None:
    c = await login("U-001")
    r = await c.post("/api/v1/users", json={"last_name": "Neumann", "first_name": "Lea"})
    assert r.status_code == 201
    assert r.json()["name"] == "Lea Neumann"


async def test_owner_may_edit_own_role_only(login: Login) -> None:
    owner = await login("U-010")  # owner of RO-006
    role = (await owner.get("/api/v1/roles/RO-006")).json()
    assert role["rights"]["is_owner"] is True
    r = await owner.patch(
        "/api/v1/roles/RO-006", json={"version": role["version"], "values": {"description": "neu"}}
    )
    assert r.status_code == 200, r.text
    other = (await owner.get("/api/v1/roles/RO-005")).json()
    assert other["rights"]["can_edit"] is False
    r = await owner.patch(
        "/api/v1/roles/RO-005", json={"version": other["version"], "values": {"description": "x"}}
    )
    assert r.status_code == 403


async def test_org_chart(login: "Login") -> None:
    employee = await login("U-004")
    r = await employee.get("/api/v1/org-chart")
    assert r.status_code == 200, r.text
    chart = r.json()
    ids = {p["id"] for p in chart["positions"]}
    in_tree = set(chart["disciplinary"]["roots"]) | set(chart["disciplinary"]["separate"])
    for kids in chart["disciplinary"]["children"].values():
        in_tree |= set(kids)
    assert in_tree == ids  # every position appears exactly in the hierarchy
    assert {u for x in chart["units"] for u in x["position_ids"]} == ids
    used = {r["role_id"] for p in chart["positions"] for r in p["roles"]}
    assert {r["role_id"] for r in chart["matrix_roles"]} == used
    assert any(p["sod_conflict"] for p in chart["positions"])
