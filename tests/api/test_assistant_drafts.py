"""AI text suggestions and process drafts (the AI call is faked)."""

import json
from typing import Any

import pytest

from grc_api.config import get_settings
from grc_api.services import assistant as svc
from tests.api.conftest import Login

KEY = "conai-test-0123456789abcdefWXYZ"
ON = {
    "version": 0,
    "enabled": True,
    "provider": "openai",
    "base_url": "https://con-ai.example/v1",
    "model": "m",
    "api_key": KEY,
}


@pytest.fixture
def ai(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.setenv("SETTINGS_SECRET", "test-secret")
    get_settings.cache_clear()
    state: dict[str, Any] = {"answer": "{}", "calls": []}

    async def complete(cfg: Any, system: str, messages: Any, **kw: Any) -> str:
        state["calls"].append((system, messages))
        return str(state["answer"])

    monkeypatch.setattr(svc, "_complete", complete)
    return state


async def test_suggestions_need_ai_and_edit_rights(login: Login, ai: dict[str, Any]) -> None:
    ia = await login("U-013")
    r = await ia.post("/api/v1/assistant/suggest/role/RO-001", json={})
    assert r.status_code == 409
    assert r.json()["code"] == "ai_off"
    admin = await login("U-001")
    await admin.put("/api/v1/ai/settings", json=ON)
    employee = await login("U-004")
    assert (
        await employee.post("/api/v1/assistant/suggest/role/RO-001", json={})
    ).status_code == 403
    assert (await ia.post("/api/v1/assistant/suggest/audit/AU-001", json={})).status_code == 404


async def test_suggestions_are_returned_not_saved(login: Login, ai: dict[str, Any]) -> None:
    admin = await login("U-001")
    await admin.put("/api/v1/ai/settings", json=ON)
    ai["answer"] = (
        'Vorschlag:\n{"responsibilities": "Prüft Bestellungen.", "nope": "x", "trainings": 3}'
    )
    ia = await login("U-013")
    before = (await ia.get("/api/v1/roles/RO-001")).json()
    r = await ia.post("/api/v1/assistant/suggest/role/RO-001", json={"lang": "de"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["version"] == before["version"]
    assert [f["key"] for f in body["fields"]] == ["responsibilities"]
    assert body["fields"][0]["current"] == before["responsibilities"]
    assert (await ia.get("/api/v1/roles/RO-001")).json()["version"] == before["version"]
    system, messages = ai["calls"][0]
    assert "JSON" in system
    assert before["title"] in messages[0]["content"]
    ai["answer"] = "keine Ahnung"
    r = await ia.post("/api/v1/assistant/suggest/role/RO-001", json={})
    assert r.status_code == 503


async def test_draft_without_ai_and_create(login: Login, ai: dict[str, Any]) -> None:
    ia = await login("U-013")
    r = await ia.post(
        "/api/v1/assistant/process-draft",
        json={
            "text": "Bestellung erfassen (Einkäufer)\nBetrag über Limit?\nBestellung senden",
            "use_ai": False,
        },
    )
    assert r.status_code == 200, r.text
    draft = r.json()
    assert draft["mode"] == "text"
    assert [s["type"] for s in draft["steps"]] == ["task", "decision", "task"]
    assert draft["steps"][0]["role_id"]  # Einkäufer matched to a role
    created = await ia.post(
        "/api/v1/processes/from-draft",
        json={
            "title": "Bestellung (Entwurf)",
            "category": "Support process",
            "description": "aus Text",
            "start": "Bedarf",
            "end": "Bestellt",
            "steps": draft["steps"],
        },
    )
    assert created.status_code == 201, created.text
    p = created.json()
    assert p["status"] == "draft"
    assert p["category"] == "Support process"
    role_id = draft["steps"][0]["role_id"]
    assert any(r["role_id"] == role_id for roles in p["steps"].values() for r in roles)
    diagram = (await ia.get(f"/api/v1/processes/{p['id']}/diagram")).json()
    assert "Betrag über Limit?" in diagram["xml"]
    hist = (await ia.get(f"/api/v1/processes/{p['id']}/history")).json()
    assert hist[0]["note"] == "Created from a draft"


async def test_draft_with_ai(login: Login, ai: dict[str, Any]) -> None:
    admin = await login("U-001")
    await admin.put("/api/v1/ai/settings", json=ON)
    ai["answer"] = json.dumps(
        {
            "title": "Retouren",
            "category": "Unknown",
            "area": "Vertrieb",
            "start": "Retoure da",
            "end": "Erledigt",
            "steps": [
                {"name": "Retoure erfassen", "type": "task", "role": "Einkäufer", "raci": "A"},
                {"name": "Ware ok?", "type": "decision", "no": "Abgelehnt"},
                {"name": "", "type": "task"},
                {"name": "Gutschrift", "type": "weird"},
            ],
        }
    )
    ia = await login("U-013")
    r = await ia.post("/api/v1/assistant/process-draft", json={"text": "Retouren bearbeiten"})
    draft = r.json()
    assert draft["mode"] == "ai"
    assert draft["category"] == "Core process"
    assert [s["name"] for s in draft["steps"]] == ["Retoure erfassen", "Ware ok?", "Gutschrift"]
    assert draft["steps"][0]["raci"] == "A"
    assert draft["steps"][2]["type"] == "task"
    employee = await login("U-004")
    r = await employee.post("/api/v1/assistant/process-draft", json={"text": "x", "use_ai": False})
    assert r.status_code == 403
