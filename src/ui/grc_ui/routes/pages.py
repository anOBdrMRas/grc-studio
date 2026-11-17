"""Start page and the modules of later stages."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from grc_ui.nav import NAV
from grc_ui.routes.common import plain
from grc_ui.session import UiContext, ui_context
from grc_ui.templating import render

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    owned: list[tuple[str, str, dict[str, Any]]] = []
    review: list[tuple[str, str, dict[str, Any]]] = []
    if ctx.can("processes:read"):
        for x in await ctx.api.processes_list():
            if x["is_owner"]:
                owned.append(("/processes", "Process", plain(x)))
            if x["status"] == "review":
                review.append(("/processes", "Process", plain(x)))
    if ctx.can("org:read"):
        for r in await ctx.api.roles_list():
            if r["is_owner"]:
                owned.append(("/roles", "Role", plain(r)))
            if r["status"] == "review":
                review.append(("/roles", "Role", plain(r)))
        for p in await ctx.api.positions_list():
            if p["is_owner"]:
                owned.append(("/positions", "Position", plain(p)))
            if p["status"] == "review":
                review.append(("/positions", "Position", plain(p)))
    me = ctx.me["id"]
    actions: list[dict[str, Any]] = []
    if ctx.can("grc:read"):
        risks = [plain(e) for e in await ctx.api.risks_list()]
        for base, label, elements in (
            ("/risks", "Risk", risks),
            (
                "/opportunities",
                "Opportunity",
                [plain(e) for e in await ctx.api.opportunities_list()],
            ),
            ("/controls", "Control", [plain(e) for e in await ctx.api.controls_list()]),
            ("/kpi", "KPI", [plain(e) for e in await ctx.api.kpis_list()]),
        ):
            for e in elements:
                if e["is_owner"]:
                    owned.append((base, label, e))
                if e.get("status") == "review":
                    review.append((base, label, e))
        # treatment actions of open risks assigned to me
        for risk in risks:
            for a in risk["actions"]:
                if a.get("owner_user_id") == me and risk["treatment_status"] != "Closed":
                    actions.append({"risk": risk, "text": a["text"]})
    received: list[dict[str, Any]] = []
    todo: list[dict[str, Any]] = []
    if ctx.can("org:read"):
        received = [plain(m) for m in await ctx.api.mandates_list() if m["recipient_user_id"] == me]
        todo = [dict(c) for c in await ctx.api.checks_list(user_id=me)]
    return render(
        request,
        "home.html",
        ctx,
        owned=owned,
        review=review if ctx.can("quality:approve") else [],
        received=received,
        todo=todo,
        actions=actions,
    )


def _later(href: str) -> None:
    item = next(n for n in NAV if n.href == href)

    @router.get(href, response_class=HTMLResponse, name=f"later_{href.strip('/')}")
    async def later(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
        return render(request, "coming_soon.html", ctx, title=item.label)


for _n in NAV:
    if not _n.ready:
        _later(_n.href)
