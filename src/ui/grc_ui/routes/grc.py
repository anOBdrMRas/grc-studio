"""Pages of the risk register beside the generic module routes (registered before them)."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from grc_ui.routes.common import catalogs
from grc_ui.session import UiContext, ui_context
from grc_ui.templating import render

router = APIRouter()


@router.get("/risks/scale", response_class=HTMLResponse)
async def risk_scale(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    """The 4-level assessment scale: likelihood and impact per type of consequence (modal)."""
    lists = (await catalogs(ctx.api))["lists"]
    impact = {t: lists[f"impact:{t}"] for t in lists["consequence_types"]}
    return render(request, "risks/_scale.html", ctx, lists=lists, impact=impact)
