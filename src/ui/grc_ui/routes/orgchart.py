"""Organisation chart (disciplinary, functional, by unit) and the role matrix of the positions."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from grc_ui.i18n import gettext
from grc_ui.session import UiContext, ui_context
from grc_ui.templating import render

router = APIRouter()
VIEWS = ("disciplinary", "functional", "units", "roles")


@router.get("/org-chart", response_class=HTMLResponse)
async def org_chart(
    request: Request,
    view: str = "disciplinary",
    roles: int = 1,
    ctx: UiContext = Depends(ui_context),
) -> Response:
    if not ctx.can("org:read"):
        return render(
            request,
            "error.html",
            ctx,
            status=403,
            message=gettext("You are not allowed to do this."),
        )
    data: dict[str, Any] = dict(await ctx.api.org_chart())
    view = view if view in VIEWS else "disciplinary"
    return render(
        request,
        "orgchart.html",
        ctx,
        view=view,
        show_roles=bool(roles),
        chart=data,
        by_id={p["id"]: p for p in data["positions"]},
    )
