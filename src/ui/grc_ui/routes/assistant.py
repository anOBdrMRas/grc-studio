"""Assistant chat (start page and dialog) and the AI settings of the administration."""

from typing import Any, cast

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from grc_client import ApiError
from grc_client.models import Turn
from grc_ui.i18n import N_, current_language, gettext
from grc_ui.session import UiContext, problem_text, ui_context
from grc_ui.templating import render, toast

router = APIRouter()
MAX_TURNS = 6
EXAMPLES = [
    N_("Where do I find the sanctions list check?"),
    N_("Which process steps concern me?"),
    N_("Who is the data protection officer?"),
    N_("Where are invoices approved?"),
]


async def chat_context(ctx: UiContext) -> dict[str, Any]:
    status = await ctx.api.assistant_status()
    return {"ai": status["ai"], "examples": EXAMPLES}


@router.get("/assistant", response_class=HTMLResponse)
async def assistant(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    """The chat as a fragment (dialog from the header, or a fresh chat on the start page)."""
    return render(request, "assistant/_chat.html", ctx, **await chat_context(ctx))


@router.post("/assistant/ask", response_class=HTMLResponse)
async def ask(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    form = await request.form()
    question = str(form.get("example") or form.get("question") or "").strip()
    if not question:
        return Response(status_code=204)
    roles = [str(x) for x in form.getlist("h_role")]
    texts = [str(x) for x in form.getlist("h_text")]
    history: list[Turn] = [
        cast(Turn, {"role": r, "text": t[:8000]})
        for r, t in zip(roles, texts, strict=False)
        if r in ("user", "assistant") and t
    ][-MAX_TURNS:]
    # an AI answer may take longer than other requests (the API limits it to about 50 s)
    ctx.api.http.timeout = httpx.Timeout(55.0)
    try:
        answer = await ctx.api.assistant_ask(
            {"question": question[:2000], "history": history, "lang": current_language.get()}
        )
    except ApiError as exc:
        return render(
            request,
            "assistant/_turn.html",
            ctx,
            question=question,
            answer={"mode": "search", "text": "", "hits": [], "error": ""},
            failure=problem_text(exc),
        )
    return render(
        request, "assistant/_turn.html", ctx, question=question, answer=dict(answer), failure=""
    )


# ---- administration ----------------------------------------------------------------------------

PERM = "ai:manage"


@router.get("/admin/ai", response_class=HTMLResponse)
async def ai_page(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    if not ctx.can(PERM):
        return render(
            request,
            "error.html",
            ctx,
            status=403,
            message=gettext("You are not allowed to do this."),
        )
    s = dict(await ctx.api.ai_settings_get())
    return render(request, "admin/ai.html", ctx, s=s, test=None)


@router.post("/admin/ai", response_class=HTMLResponse)
async def ai_save(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    form = await request.form()
    body = {
        "version": int(str(form.get("version") or 0)),
        "enabled": form.get("enabled") == "on",
        "provider": str(form.get("provider") or "openai"),
        "base_url": str(form.get("base_url") or "").strip(),
        "model": str(form.get("model") or "").strip(),
        "api_key": str(form.get("api_key") or "").strip(),
        "remove_key": form.get("remove_key") == "1",
    }
    try:
        s = dict(await ctx.api.ai_settings_update(body))  # type: ignore[arg-type]
        headers = toast("success", gettext("Saved"))
    except ApiError as exc:
        if exc.status not in (403, 409, 412, 422):
            raise
        s = dict(await ctx.api.ai_settings_get())
        headers = toast("error", problem_text(exc))
    return render(request, "admin/_ai_form.html", ctx, s=s, test=None, headers=headers)


@router.post("/admin/ai/test", response_class=HTMLResponse)
async def ai_test(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    result = dict(await ctx.api.ai_test())
    s = dict(await ctx.api.ai_settings_get())
    return render(request, "admin/_ai_form.html", ctx, s=s, test=result)


# ---- text suggestions --------------------------------------------------------------------------


def _module(kind: str) -> Any:
    from grc_ui.routes.modules import MODULES

    return next((m for m in MODULES.values() if m.kind == kind), None)


def _labels(kind: str) -> dict[str, str]:
    from grc_ui.forms import FORMS

    return {f["key"]: f["label"] for s in FORMS.get(kind, []) for f in s["fields"]}


@router.get("/assistant/suggest/{kind}/{item_id}", response_class=HTMLResponse)
async def suggest_form(
    request: Request, kind: str, item_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    return render(request, "assistant/_suggest.html", ctx, kind=kind, item_id=item_id, result=None)


@router.post("/assistant/suggest/{kind}/{item_id}", response_class=HTMLResponse)
async def suggest_run(
    request: Request, kind: str, item_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    ctx.api.http.timeout = httpx.Timeout(55.0)
    try:
        result = dict(
            await ctx.api.assistant_suggest(kind, item_id, {"lang": current_language.get()})
        )
    except ApiError as exc:
        return render(
            request,
            "assistant/_suggest.html",
            ctx,
            kind=kind,
            item_id=item_id,
            result=None,
            error=_ai_problem(exc),
        )
    return render(
        request,
        "assistant/_suggest.html",
        ctx,
        kind=kind,
        item_id=item_id,
        result=result,
        labels=_labels(kind),
    )


@router.post("/assistant/suggest/{kind}/{item_id}/apply", response_class=HTMLResponse)
async def suggest_apply(
    request: Request, kind: str, item_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    mod = _module(kind)
    if mod is None:
        return Response(status_code=404)
    form = await request.form()
    keys = [str(k) for k in form.getlist("apply")]
    values = {k: str(form.get(f"text.{k}") or "").strip() for k in keys}
    if not values:
        return Response(
            status_code=204, headers=toast("error", gettext("Choose at least one suggestion."))
        )
    update = getattr(ctx.api, f"{mod.api}_update")
    try:
        await update(item_id, {"version": int(str(form.get("version"))), "values": values})
    except ApiError as exc:
        if exc.status not in (403, 409, 412, 422):
            raise
        return Response(status_code=204, headers=toast("error", problem_text(exc)))
    return Response(status_code=204, headers={"HX-Redirect": f"{mod.base}/{item_id}"})


def _ai_problem(exc: ApiError) -> str:
    from grc_ui.assistant import ERRORS

    if exc.code == "ai_off":
        return gettext("The AI assistant is not set up. Ask the administration.")
    if exc.code == "ai_unusable":
        return gettext("The AI gave no usable answer. Please try again.")
    if exc.code in ERRORS:
        return gettext(ERRORS[exc.code])
    return problem_text(exc)


# ---- process draft -----------------------------------------------------------------------------


async def _draft_ctx(ctx: UiContext) -> dict[str, Any]:
    from grc_ui.routes.common import catalogs

    roles = [(r["id"], f"{r['code']} {r['title']}") for r in await ctx.api.roles_list()]
    cat = await catalogs(ctx.api)
    return {
        "ai": (await ctx.api.assistant_status())["ai"],
        "roles": roles,
        "categories": cat["lists"]["process_categories"],
    }


@router.get("/processes/draft", response_class=HTMLResponse)
async def draft_form(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    return render(
        request, "assistant/_draft.html", ctx, text="", draft=None, **await _draft_ctx(ctx)
    )


@router.post("/processes/draft", response_class=HTMLResponse)
async def draft_run(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    form = await request.form()
    text = str(form.get("text") or "").strip()[:5000]
    extra = await _draft_ctx(ctx)
    if form.get("back") or not text:
        return render(request, "assistant/_draft.html", ctx, text=text, draft=None, **extra)
    ctx.api.http.timeout = httpx.Timeout(55.0)
    try:
        draft = dict(
            await ctx.api.assistant_process_draft(
                {"text": text, "use_ai": form.get("mode") == "ai", "lang": current_language.get()}
            )
        )
    except ApiError as exc:
        return render(
            request,
            "assistant/_draft.html",
            ctx,
            text=text,
            draft=None,
            error=_ai_problem(exc),
            **extra,
        )
    return render(request, "assistant/_draft.html", ctx, text=text, draft=draft, **extra)


@router.post("/processes/draft/create", response_class=HTMLResponse)
async def draft_create(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    form = await request.form()
    names = [str(x) for x in form.getlist("step.name")]
    types = [str(x) for x in form.getlist("step.type")]
    roles = [str(x) for x in form.getlist("step.role_id")]
    racis = [str(x) for x in form.getlist("step.raci")]
    nos = [str(x) for x in form.getlist("step.no")]
    steps = [
        {"name": n.strip(), "type": t, "role_id": r, "raci": c, "no": o}
        for n, t, r, c, o in zip(names, types, roles, racis, nos, strict=False)
        if n.strip()
    ]
    body = {
        "title": str(form.get("title") or "").strip(),
        "category": str(form.get("category") or ""),
        "area": str(form.get("area") or ""),
        "description": str(form.get("text") or "")[:5000],
        "start": str(form.get("start") or "Start"),
        "end": str(form.get("end") or "Ende"),
        "steps": steps,
    }
    try:
        created = await ctx.api.processes_create_from_draft(body)  # type: ignore[arg-type]
    except ApiError as exc:
        if exc.status not in (403, 409, 422):
            raise
        return Response(status_code=204, headers=toast("error", problem_text(exc)))
    return Response(status_code=204, headers={"HX-Redirect": f"/processes/{created['id']}"})
