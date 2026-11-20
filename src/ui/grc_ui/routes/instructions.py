"""Work instructions: assignment to process steps from the work instruction ("Refers to").
The list, detail, form and workflow pages are the generic module pages (routes/modules.py)."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response
from markupsafe import escape

from grc_client import ApiError
from grc_ui.i18n import gettext
from grc_ui.routes.modules import MODULES, detail_context, detail_urls
from grc_ui.session import UiContext, problem_text, ui_context
from grc_ui.templating import render, toast

router = APIRouter()
MOD = MODULES["instructions"]


@router.get("/instructions/{wi_id}/step-options", response_class=HTMLResponse)
async def step_options(
    wi_id: str, process_id: str = "", ctx: UiContext = Depends(ui_context)
) -> Response:
    """The steps (activities) of the chosen process as the second dropdown."""
    options = [f'<option value="">{escape(gettext("Choose process step …"))}</option>']
    if process_id:
        p = await ctx.api.processes_get(process_id)
        for el, name in p["activities"].items():
            links = p["links"].get(el, [])
            if not any(lk["kind"] == "instruction" and lk["target_id"] == wi_id for lk in links):
                options.append(f'<option value="{escape(el)}">{escape(name)}</option>')
    disabled = "" if process_id else " disabled"
    label = escape(gettext("Process step"))
    return HTMLResponse(
        f'<select name="element_id" class="select select-bordered select-xs" aria-label="{label}" required{disabled}>'
        + "".join(options)
        + "</select>"
    )


async def _detail(
    request: Request, ctx: UiContext, wi_id: str, headers: dict[str, str]
) -> Response:
    d = await detail_context(request, ctx, MOD, wi_id)
    return render(
        request, "entity/_detail.html", ctx, **d, **detail_urls(MOD, wi_id), headers=headers
    )


async def _change(request: Request, ctx: UiContext, wi_id: str, remove: bool) -> Response:
    form = await request.form()
    process_id = str(form.get("process_id") or "")
    element_id = str(form.get("element_id") or "")
    if not process_id or not element_id:
        return await _detail(
            request, ctx, wi_id, toast("error", gettext("Choose a process and a step."))
        )
    try:
        version = (await ctx.api.processes_get(process_id))["version"]
        if remove:
            await ctx.api.processes_unlink_element(
                process_id, element_id, "instruction", wi_id, version=version
            )
            headers = toast("success", gettext("Assignment removed"), "refreshList")
        else:
            await ctx.api.processes_link_element(
                process_id,
                element_id,
                {"kind": "instruction", "target_id": wi_id, "version": version},
            )
            headers = toast("success", gettext("Assigned"), "refreshList")
    except ApiError as exc:
        if exc.status not in (403, 404, 409, 412, 422):
            raise
        headers = toast("error", problem_text(exc))
    return await _detail(request, ctx, wi_id, headers)


@router.post("/instructions/{wi_id}/steps", response_class=HTMLResponse)
async def add_step(request: Request, wi_id: str, ctx: UiContext = Depends(ui_context)) -> Response:
    return await _change(request, ctx, wi_id, remove=False)


@router.post("/instructions/{wi_id}/steps/remove", response_class=HTMLResponse)
async def remove_step(
    request: Request, wi_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    return await _change(request, ctx, wi_id, remove=True)
