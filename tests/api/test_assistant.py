"""AI assistant: settings with an encrypted key, catalogue search, AI answers with checked links."""

import json
from collections.abc import Iterator
from typing import Any

import httpx
import pytest

from grc_api.config import get_settings
from grc_api.services import assistant as svc
from tests.api.conftest import Login

KEY = "sk-ant-test-0123456789abcdefWXYZ"
ANTHROPIC = {"version": 0, "enabled": True, "provider": "anthropic", "api_key": KEY}


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
        cfg: svc.AiConfig, system: str, messages: list[dict[str, str]], **kw: Any
    ) -> str:
        calls.append({"key": cfg.key, "model": cfg.model, "system": system, "messages": messages})
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
        json={
            "version": 0,
            "enabled": True,
            "provider": "anthropic",
            "model": "claude-opus-5-5",
            "api_key": KEY,
        },
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
    await admin.put("/api/v1/ai/settings", json=ANTHROPIC)
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
    await admin.put("/api/v1/ai/settings", json=ANTHROPIC)
    r = await admin.post("/api/v1/assistant/ask", json={"question": "Bestellung"})
    assert r.json()["mode"] == "search"
    assert r.json()["error"] == "ai_auth"
    t = await admin.post("/api/v1/ai/test")
    assert t.json() == {"ok": False, "code": "ai_auth"}


async def test_openai_compatible_service(
    login: Login, secret: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The internal con-AI: OpenAI-compatible chat completions at the configured address."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.headers["Authorization"] != f"Bearer {KEY}":
            return httpx.Response(401)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "Siehe [[role:RO-001|DSB]]."},
                        "finish_reason": "stop",
                    }
                ]
            },
        )

    monkeypatch.setattr(svc, "_transport", httpx.MockTransport(handler))
    admin = await login("U-001")
    incomplete = await admin.put(
        "/api/v1/ai/settings",
        json={"version": 0, "enabled": True, "provider": "openai", "api_key": KEY},
    )
    assert incomplete.status_code == 422  # address and model missing
    bad_url = await admin.put(
        "/api/v1/ai/settings",
        json={"version": 0, "provider": "openai", "base_url": "ftp://x", "model": "m"},
    )
    assert bad_url.status_code == 422
    r = await admin.put(
        "/api/v1/ai/settings",
        json={
            "version": 0,
            "enabled": True,
            "provider": "openai",
            "base_url": "https://con-ai.example/v1/",
            "model": "con-ai-large",
            "api_key": KEY,
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["base_url"] == "https://con-ai.example/v1"
    assert (await admin.post("/api/v1/ai/test")).json() == {"ok": True, "code": "ok"}
    answer = (await admin.post("/api/v1/assistant/ask", json={"question": "Wer ist DSB?"})).json()
    assert answer["mode"] == "ai"
    assert "[[role:RO-001|DSB]]" in answer["text"]
    req = seen[-1]
    assert str(req.url) == "https://con-ai.example/v1/chat/completions"
    body = json.loads(req.content)
    assert body["model"] == "con-ai-large"
    assert body["messages"][0]["role"] == "system"
    assert "[[role:RO-001|" in body["messages"][0]["content"]


@pytest.mark.parametrize(
    ("status", "code"),
    [(401, "ai_auth"), (429, "ai_busy"), (400, "ai_rejected"), (502, "ai_unavailable")],
)
async def test_openai_errors(status: int, code: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        svc, "_transport", httpx.MockTransport(lambda r: httpx.Response(status, json={}))
    )
    cfg = svc.AiConfig("openai", "https://con-ai.example/v1", "m", KEY)
    with pytest.raises(svc.AiFailure) as exc:
        await svc._complete(cfg, "s", [{"role": "user", "content": "q"}])
    assert exc.value.code == code
    assert KEY not in str(exc.value)
