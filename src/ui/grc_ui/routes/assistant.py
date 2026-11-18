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
