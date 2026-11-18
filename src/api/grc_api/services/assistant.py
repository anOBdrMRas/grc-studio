"""AI assistant: settings (API key encrypted at rest), catalogue of readable elements, questions.

The AI service is either OpenAI-compatible (e.g. the internal con-AI) or Anthropic-compatible
(Claude directly or through a gateway); the administration chooses it with address, model and key.

Without an API key (or when the AI service fails) the assistant answers with the local catalogue
search, so it always gives the person something to open.
"""

import base64
import hashlib
import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import anthropic
import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.config import get_settings
from grc_api.domain import assistant as asst
from grc_api.domain.bpmn import activities
from grc_api.errors import ProblemError
from grc_api.models import (
    Audit,
    Control,
    Kpi,
    Mandate,
    Opportunity,
    Process,
    Risk,
)
from grc_api.repositories import audit, elements
from grc_api.repositories import processes as proc_repo
from grc_api.repositories import settings as settings_repo
from grc_api.schemas.assistant import (
    AiSettingsIn,
    AiSettingsOut,
    AiTestOut,
    AskIn,
    AskOut,
    AssistantStatus,
    Hit,
)
from grc_api.services.context import OrgData, load_org

log = logging.getLogger("grc_api.assistant")

KEY = "ai"
PERM = "ai:manage"
PROVIDERS = ("openai", "anthropic")
# suggestions for the model field (Anthropic); for an OpenAI-compatible service (e.g. con-AI)
# the administration enters the model name of that service
MODELS = ("claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5")
DEFAULT_MODEL = MODELS[0]
TIMEOUT = 25.0
# tests replace the transport of the OpenAI-compatible client
_transport: httpx.AsyncBaseTransport | None = None
# models that accept the server-side fallback on a refusal ("default" routing)
FALLBACK_MODELS = frozenset({"claude-opus-5-5", "claude-sonnet-5-5"})
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MAX_TOKENS = 4000


# ---- settings ----------------------------------------------------------------------------------


def _fernet() -> Fernet:
    secret = get_settings().settings_secret
    if not secret:
        raise ProblemError(
            "settings_secret_missing",
            "SETTINGS_SECRET is not configured on the server; the API key cannot be stored.",
            status=409,
        )
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()))


async def _load(db: AsyncSession) -> tuple[dict[str, Any], int]:
    row = await settings_repo.get(db, KEY)
    return (dict(row.value), row.version) if row else ({}, 0)


def _api_key(data: dict[str, Any]) -> str:
    """The decrypted key, or "" when none is stored or it cannot be decrypted."""
    token = data.get("key") or ""
    if not token or not get_settings().settings_secret:
        return ""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        log.warning("stored AI key cannot be decrypted (SETTINGS_SECRET changed?)")
        return ""


def _need(p: Principal, perm: str) -> None:
    if not p.can(perm):
        raise ProblemError("forbidden", f"Permission {perm} required")


@dataclass(frozen=True)
class AiConfig:
    provider: str  # openai (OpenAI-compatible, e.g. con-AI) or anthropic
    base_url: str  # empty: api.anthropic.com (provider anthropic only)
    model: str
    key: str


def _config(data: dict[str, Any]) -> AiConfig | None:
    """The usable configuration, or None when the assistant cannot use AI."""
    key = _api_key(data)
    provider = data.get("provider") or "anthropic"
    base_url = data.get("base_url") or ""
    model = data.get("model") or (DEFAULT_MODEL if provider == "anthropic" else "")
    if not key or not model or (provider == "openai" and not base_url):
        return None
    return AiConfig(provider, base_url, model, key)


def _settings_out(data: dict[str, Any], version: int) -> AiSettingsOut:
    provider = data.get("provider") or ("anthropic" if data.get("key") else "openai")
    return AiSettingsOut(
        version=version,
        enabled=bool(data.get("enabled")),
        provider=provider,
        providers=list(PROVIDERS),
        base_url=data.get("base_url") or "",
        model=data.get("model") or "",
        models=list(MODELS),
        has_key=bool(data.get("key")),
        key_readable=bool(_api_key(data)),
        key_hint=data.get("hint") or "",
        secret_configured=bool(get_settings().settings_secret),
    )


def _clean_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if not url:
        return ""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc or parts.query or parts.fragment:
        raise ProblemError(
            "invalid", "The address must be an http(s) URL, e.g. https://ai.example/v1"
        )
    return url


async def settings_view(db: AsyncSession, p: Principal) -> AiSettingsOut:
    _need(p, PERM)
    data, version = await _load(db)
    return _settings_out(data, version)


async def update_settings(
    db: AsyncSession, body: AiSettingsIn, if_match: str | None, p: Principal
) -> AiSettingsOut:
    _need(p, PERM)
    data, stored = await _load(db)
    version = body.version if not if_match else int(if_match.strip('W/"'))
    if version != stored:
        raise ProblemError(
            "version_conflict",
            "Someone else changed the AI settings in the meantime. Load them again.",
            status=412 if if_match else 409,
        )
    if body.provider not in PROVIDERS:
        raise ProblemError("invalid", f"Unknown interface: {body.provider}")
    model = body.model.strip()[:200]
    if any(c.isspace() for c in model):
        raise ProblemError("invalid", "The model name contains spaces")
    new = dict(data) | {
        "enabled": body.enabled,
        "provider": body.provider,
        "base_url": _clean_url(body.base_url),
        "model": model,
    }
    changes: list[dict[str, Any]] = [
        {"key": k, "from": data.get(k), "to": new[k]}
        for k in ("enabled", "provider", "base_url", "model")
        if (data.get(k) or None) != (new[k] or None)
    ]
    if body.remove_key:
        new.pop("key", None)
        new.pop("hint", None)
        if data.get("key"):
            changes.append({"key": "api_key", "from": "stored", "to": None})
    elif body.api_key:
        key = body.api_key.strip()
        if len(key) < 20 or any(c.isspace() for c in key):
            raise ProblemError("invalid", "This does not look like an API key")
        new["key"] = _fernet().encrypt(key.encode()).decode()
        new["hint"] = key[-4:]
        changes.append({"key": "api_key", "from": None, "to": f"…{key[-4:]}"})
    if new.get("enabled") and not new.get("key"):
        raise ProblemError("invalid", "Store an API key before switching the assistant on")
    if new.get("enabled") and new["provider"] == "openai" and not (new["base_url"] and model):
        raise ProblemError(
            "invalid", "An OpenAI-compatible service needs its address and a model name"
        )
    if changes:
        if not await settings_repo.save(db, KEY, version, new):
            raise ProblemError("version_conflict", "Load the AI settings again.", status=409)
        # the key itself never goes into the history
        await audit.record(db, p.user_id, "update", "settings", KEY, changes)
        await db.commit()
    data, version = await _load(db)
    return _settings_out(data, version)


async def test_connection(db: AsyncSession, p: Principal) -> AiTestOut:
    _need(p, PERM)
    data, _ = await _load(db)
    cfg = _config(data)
    if cfg is None:
        return AiTestOut(ok=False, code="no_key" if not _api_key(data) else "incomplete")
    try:
        await _complete(cfg, "Reply with: ok", [{"role": "user", "content": "ok?"}], max_tokens=200)
    except AiFailure as exc:
        return AiTestOut(ok=False, code=exc.code)
    return AiTestOut(ok=True, code="ok")


async def status(db: AsyncSession) -> AssistantStatus:
    data, _ = await _load(db)
    return AssistantStatus(ai=bool(data.get("enabled") and _config(data)))


# ---- calling the AI ----------------------------------------------------------------------------


class AiFailure(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


async def _complete(
    cfg: AiConfig, system: str, messages: list[dict[str, str]], *, max_tokens: int = MAX_TOKENS
) -> str:
    """One answer of the configured AI service; raises AiFailure with a stable code (never with
    the key)."""
    if cfg.provider == "openai":
        return await _openai(cfg, system, messages, max_tokens)
    return await _anthropic(cfg, system, messages, max_tokens)


async def _openai(
    cfg: AiConfig, system: str, messages: list[dict[str, str]], max_tokens: int
) -> str:
    """OpenAI-compatible chat completions (e.g. the internal con-AI): POST {base}/chat/completions."""
    body = {
        "model": cfg.model,
        "messages": [{"role": "system", "content": system}, *messages],
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=TIMEOUT, transport=_transport) as client:
        try:
            r = await client.post(
                f"{cfg.base_url}/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {cfg.key}"},
            )
        except httpx.HTTPError as exc:
            log.warning("AI service unavailable: %s", type(exc).__name__)
            raise AiFailure("ai_unavailable") from exc
    if r.status_code in (401, 403):
        raise AiFailure("ai_auth")
    if r.status_code == 429:
        raise AiFailure("ai_busy")
    if r.status_code in (400, 404, 413, 422):
        log.warning("AI request rejected: HTTP %s", r.status_code)
        raise AiFailure("ai_rejected")
    if r.status_code != 200:
        log.warning("AI service unavailable: HTTP %s", r.status_code)
        raise AiFailure("ai_unavailable")
    try:
        choice = r.json()["choices"][0]
        text = choice["message"]["content"] or ""
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        log.warning("AI service answered in an unexpected format")
        raise AiFailure("ai_unavailable") from exc
    if choice.get("finish_reason") == "content_filter":
        raise AiFailure("ai_refused")
    return str(text).strip()


async def _anthropic(
    cfg: AiConfig, system: str, messages: list[dict[str, str]], max_tokens: int
) -> str:
    """Claude through the Messages API (Anthropic directly, or a compatible gateway)."""
    official = not cfg.base_url
    client = anthropic.AsyncAnthropic(
        api_key=cfg.key, base_url=cfg.base_url or None, timeout=TIMEOUT, max_retries=1
    )
    params: dict[str, Any] = {
        "model": cfg.model,
        "max_tokens": max_tokens,
        # rules and catalogue are stable: cached between questions
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        "messages": messages,
    }
    if official:
        # options of the Anthropic API that a gateway may not know
        params["output_config"] = {"effort": "low"}
    try:
        if official and cfg.model in FALLBACK_MODELS:
            # on a refusal the API answers with a fallback model instead of stopping
            response: Any = await client.beta.messages.create(
                betas=[FALLBACK_BETA], fallbacks="default", **params
            )
        else:
            response = await client.messages.create(**params)
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
        raise AiFailure("ai_auth") from exc
    except anthropic.RateLimitError as exc:
        raise AiFailure("ai_busy") from exc
    except anthropic.BadRequestError as exc:
        log.warning("AI request rejected: %s", exc.message)
        raise AiFailure("ai_rejected") from exc
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
        log.warning("AI service unavailable: %s", type(exc).__name__)
        raise AiFailure("ai_unavailable") from exc
    finally:
        await client.close()
    if response.stop_reason == "refusal":
        raise AiFailure("ai_refused")
    return "".join(b.text for b in response.content if b.type == "text").strip()


# ---- catalogue ---------------------------------------------------------------------------------


def _join(names: list[str]) -> str:
    return ", ".join(dict.fromkeys(n for n in names if n)) or "–"


async def catalog(db: AsyncSession, p: Principal, org: OrgData, lang: str) -> list[asst.Entry]:
    """Everything the person may open, with a short context line each."""
    de = lang != "en"
    out: list[asst.Entry] = []

    def holders(role_id: str | None) -> str:
        return _join([org.name(u) for u in org.role_holders(role_id)]) if role_id else "–"

    def role_title(role_id: str | None) -> str:
        r = org.roles.get(role_id or "")
        return r.title if r else ""

    if p.can("processes:read"):
        by_step: dict[tuple[str, str], list[str]] = {}
        for a in await proc_repo.assignments(db):
            by_step.setdefault((a.process_id, a.element_id), []).append(
                f"{role_title(a.role_id)} ({a.raci})"
            )
        for x in await elements.list_all(db, Process):
            owner = role_title(x.owner_role_id)
            sub = " · ".join(
                s for s in (x.category, x.area, f"Owner: {owner}" if owner else "") if s
            )
            out.append(
                asst.Entry("processes", x.id, x.title, sub, f"{x.title} {x.description} {sub}")
            )
            for el, name in activities(x.xml):
                roles = ", ".join(by_step.get((x.id, el), []))
                sub = f"{x.title}{' · ' + roles if roles else ''}"
                out.append(asst.Entry("step", f"{x.id}/{el}", name, sub, f"{name} {sub}"))
    if p.can("org:read"):
        for r in org.roles.values():
            sub = f"{'Rolle' if de else 'Role'} · {'Inhaber' if de else 'Holders'}: " + holders(
                r.id
            )
            text = f"{r.title} {r.description} {r.responsibilities} {r.authorities} {sub}"
            out.append(asst.Entry("role", r.id, r.title, sub, text))
        for pos in org.positions.values():
            names = [u.display_name for u in org.users.values() if u.position_id == pos.id]
            sub = f"{'Stelle' if de else 'Position'} · {'Inhaber' if de else 'Holders'}: " + (
                _join(names) if names else ("unbesetzt" if de else "vacant")
            )
            out.append(
                asst.Entry(
                    "position",
                    pos.id,
                    pos.title,
                    sub,
                    f"{pos.title} {pos.purpose} {pos.tasks} {sub}",
                )
            )
        for m in await elements.list_all(db, Mandate):
            sub = f"{m.mandate_type} · {org.name(m.recipient_user_id)}"
            out.append(asst.Entry("mandate", m.id, m.title, sub, f"{m.title} {m.scope} {sub}"))
    if p.can("grc:read"):
        for k in await elements.list_all(db, Risk):
            sub = f"{'Risiko' if de else 'Risk'} · {k.category} · {org.name(k.owner_user_id)}"
            out.append(
                asst.Entry("risk", k.id, k.title, sub, f"{k.title} {k.description} {k.cause}")
            )
        for o in await elements.list_all(db, Opportunity):
            sub = f"{'Chance' if de else 'Opportunity'} · {o.category}"
            out.append(asst.Entry("opportunity", o.id, o.title, sub, f"{o.title} {o.description}"))
        for c in await elements.list_all(db, Control):
            sub = f"Control · {role_title(c.owner_role_id)}"
            text = f"{c.title} {c.description} {c.objective}"
            out.append(asst.Entry("control", c.id, c.title, sub, text))
        for kp in await elements.list_all(db, Kpi):
            sub = f"KPI · {role_title(kp.owner_role_id)}"
            text = f"{kp.title} {kp.objective} {kp.formula}"
            out.append(asst.Entry("kpi", kp.id, kp.title, sub, text))
        for au in await elements.list_all(db, Audit):
            sub = f"Audit · {au.audit_type} · {au.audit_status}"
            out.append(asst.Entry("audit", au.id, au.title, sub, f"{au.title} {au.objective}"))
    return out


def _hit(e: asst.Entry) -> Hit:
    return Hit(kind=e.kind, id=e.id, label=e.label, sub=e.sub)


async def ask(db: AsyncSession, body: AskIn, p: Principal) -> AskOut:
    _need(p, "people:read")
    question = body.question.strip()[: asst.MAX_QUESTION]
    if not question:
        raise ProblemError("invalid", "Ask a question")
    lang = "en" if body.lang == "en" else "de"
    org = await load_org(db)
    entries = await catalog(db, p, org, lang)
    hits = asst.search(entries, question)
    data, _ = await _load(db)
    cfg = _config(data) if data.get("enabled") else None
    if cfg is None:
        return AskOut(mode="search", text="", hits=[_hit(e) for e in hits])
    me = org.users.get(p.user_id)
    roles = [org.roles[r].title for r in org.roles_of(p.user_id) if r in org.roles]
    pos = org.positions.get(me.position_id or "") if me else None
    who = f"{org.name(p.user_id)} ({pos.title if pos else '–'}; roles: {_join(roles)})"
    history = [
        {"role": h.role, "content": h.text[:4000]}
        for h in body.history[-asst.MAX_HISTORY :]
        if h.text.strip()
    ]
    # the API wants the conversation to start with the person
    while history and history[0]["role"] != "user":
        history.pop(0)
    messages = [*history, {"role": "user", "content": asst.question_prompt(question, who, hits)}]
    try:
        text = await _complete(cfg, asst.system_prompt(lang, entries), messages)
    except AiFailure as exc:
        return AskOut(mode="search", text="", hits=[_hit(e) for e in hits], error=exc.code)
    return AskOut(mode="ai", text=asst.checked_links(text, entries), hits=[])
