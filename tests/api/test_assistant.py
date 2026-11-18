"""AI assistant: settings with an encrypted key, catalogue search, AI answers with checked links."""

from collections.abc import Iterator
from typing import Any

import pytest

from grc_api.config import get_settings
from grc_api.services import assistant as svc
from tests.api.conftest import Login

KEY = "sk-ant-test-0123456789abcdefWXYZ"


@pytest.fixture
def secret(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("SETTINGS_SECRET", "test-secret-for-the-ai-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def fake_ai(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    async def complete(
        key: str, model: str, system: str, messages: list[dict[str, str]], **kw: Any
    ) -> str:
        calls.append({"key": key, "model": model, "system": system, "messages": messages})
        return (
            "Im Schritt [[step:P-001/P001_T1|Bedarf melden]] (erfunden: "
            "[[risk:R-999|Geheimes Risiko]]) und [[role:RO-001|Rolle]]."
        )

    monkeypatch.setattr(svc, "_complete", complete)
    return calls


async def test_only_admins_configure_the_ai(login: Login, secret: None) -> None:
    ia = await login("U-013")
    assert (await ia.get("/api/v1/ai/settings")).status_code == 403
    admin = await login("U-001")
    s = (await admin.get("/api/v1/ai/settings")).json()
    assert s["has_key"] is False
    assert s["secret_configured"] is True
    r = await admin.put("/api/v1/ai/settings", json={"version": 0, "enabled": True})
    assert r.status_code == 422  # no key yet
    r = await admin.put(
        "/api/v1/ai/settings",
        json={"version": 0, "enabled": True, "model": "claude-opus-5-5", "api_key": KEY},
    )
    assert r.status_code == 200, r.text
    s = r.json()
    assert s == s | {"has_key": True, "key_readable": True, "key_hint": "WXYZ", "enabled": True}
    assert KEY not in r.text
    hist = (await admin.get("/api/v1/assistant")).json()
    assert hist == {"ai": True}


async def test_key_is_encrypted_at_rest(login: Login, secret: None) -> None:
    from grc_api.db import get_sessionmaker
    from grc_api.repositories import settings as repo

    admin = await login("U-001")
    await admin.put("/api/v1/ai/settings", json={"version": 0, "api_key": KEY})
    async with get_sessionmaker()() as db:
        row = await repo.get(db, "ai")
        assert row is not None
        assert KEY not in str(row.value)


async def test_key_needs_the_server_secret(login: Login, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SETTINGS_SECRET", "")
    get_settings.cache_clear()
    admin = await login("U-001")
    r = await admin.put("/api/v1/ai/settings", json={"version": 0, "api_key": KEY})
    assert r.status_code == 409
    assert r.json()["code"] == "settings_secret_missing"
    get_settings.cache_clear()


async def test_search_without_ai(login: Login) -> None:
    employee = await login("U-004")
    r = await employee.post("/api/v1/assistant/ask", json={"question": "Wo wird bestellt?"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mode"] == "search"
    assert body["hits"], body
    assert {h["kind"] for h in body["hits"]} <= {
        "processes",
        "step",
        "role",
        "position",
        "mandate",
        "risk",
        "opportunity",
        "control",
        "kpi",
        "audit",
    }


async def test_ai_answer_keeps_only_known_links(
    login: Login, secret: None, fake_ai: list[dict[str, Any]]
) -> None:
    admin = await login("U-001")
    await admin.put("/api/v1/ai/settings", json={"version": 0, "enabled": True, "api_key": KEY})
    employee = await login("U-004")
    r = await employee.post(
        "/api/v1/assistant/ask",
        json={
            "question": "Wer genehmigt Bestellungen?",
            "history": [
                {"role": "assistant", "text": "Hallo"},
                {"role": "user", "text": "Hallo"},
                {"role": "assistant", "text": "Wie kann ich helfen?"},
            ],
        },
    )
    body = r.json()
    assert body["mode"] == "ai", body
    assert "[[role:RO-001|Rolle]]" in body["text"]
    assert "R-999" not in body["text"]
    assert "Geheimes Risiko" in body["text"]
    call = fake_ai[0]
    assert call["key"] == KEY
    assert call["messages"][0]["role"] == "user"  # history starts with the person
    assert "[[role:RO-001|" in call["system"]


async def test_ai_failure_falls_back_to_search(
    login: Login, secret: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def failing(*a: Any, **kw: Any) -> str:
        raise svc.AiFailure("ai_auth")

    monkeypatch.setattr(svc, "_complete", failing)
    admin = await login("U-001")
    await admin.put("/api/v1/ai/settings", json={"version": 0, "enabled": True, "api_key": KEY})
    r = await admin.post("/api/v1/assistant/ask", json={"question": "Bestellung"})
    assert r.json()["mode"] == "search"
    assert r.json()["error"] == "ai_auth"
    t = await admin.post("/api/v1/ai/test")
    assert t.json() == {"ok": False, "code": "ai_auth"}
