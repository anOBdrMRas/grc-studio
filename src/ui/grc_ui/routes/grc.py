"""Pages of the risk register beside the generic module routes (registered before them)."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from grc_client import ApiError
from grc_ui.i18n import gettext
from grc_ui.routes.common import catalogs
from grc_ui.routes.modules import MODULES, detail_context, detail_urls
from grc_ui.session import UiContext, problem_text, ui_context
from grc_ui.templating import render, toast

router = APIRouter()


@router.get("/risks/scale", response_class=HTMLResponse)
async def risk_scale(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    """The 4-level assessment scale: likelihood and impact per type of consequence (modal)."""
    lists = (await catalogs(ctx.api))["lists"]
    impact = {t: lists[f"impact:{t}"] for t in lists["consequence_types"]}
    return render(request, "risks/_scale.html", ctx, lists=lists, impact=impact)


@router.post("/kpi/{kpi_id}/measurements", response_class=HTMLResponse)
async def record_measurement(
    request: Request, kpi_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    form = await request.form()
    headers: dict[str, str] = {"HX-Trigger": "refreshList"}
    try:
        await ctx.api.kpis_record_measurement(
            kpi_id,
            {
                "date": str(form.get("date")),
                "value": float(str(form.get("value") or "0").replace(",", ".")),
            },
        )
        headers |= toast("success", gettext("Value recorded"))
    except (ApiError, ValueError) as exc:
        headers = toast(
            "error", problem_text(exc) if isinstance(exc, ApiError) else gettext("Invalid value")
        )
    return await _kpi_detail(request, ctx, kpi_id, headers)


@router.post("/kpi/{kpi_id}/measurements/{day}/delete", response_class=HTMLResponse)
async def delete_measurement(
    request: Request, kpi_id: str, day: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    headers: dict[str, str] = {"HX-Trigger": "refreshList"}
    try:
        await ctx.api.kpis_delete_measurement(kpi_id, day)
    except ApiError as exc:
        headers = toast("error", problem_text(exc))
    return await _kpi_detail(request, ctx, kpi_id, headers)


async def _kpi_detail(
    request: Request, ctx: UiContext, kpi_id: str, headers: dict[str, str]
) -> Response:
    mod = MODULES["kpi"]
    d = await detail_context(request, ctx, mod, kpi_id)
    return render(
        request, "entity/_detail.html", ctx, **d, **detail_urls(mod, kpi_id), headers=headers
    )
