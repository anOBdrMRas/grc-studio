"""Pages of the risk register beside the generic module routes (registered before them)."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from grc_client import ApiError
from grc_ui.formdata import values_from_form
from grc_ui.forms import FORMS
from grc_ui.i18n import N_, gettext
from grc_ui.routes.common import catalogs, iso_labels, ref_options
from grc_ui.routes.modules import MODULES, detail_context, detail_urls
from grc_ui.session import UiContext, field_errors, problem_text, ui_context
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
        headers = toast("success", gettext("Value recorded"), "refreshList")
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


# ---- audit findings ----------------------------------------------------------------------------

RESPONSIBLE_STATUSES = ("Open", "In progress", "Implemented")


async def _audit_detail(
    request: Request, ctx: UiContext, audit_id: str, headers: dict[str, str]
) -> Response:
    mod = MODULES["audits"]
    d = await detail_context(request, ctx, mod, audit_id)
    return render(
        request, "entity/_detail.html", ctx, **d, **detail_urls(mod, audit_id), headers=headers
    )


@router.post("/audits/{audit_id}/findings", response_class=HTMLResponse)
async def create_finding(
    request: Request, audit_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    form = await request.form()
    headers: dict[str, str] = {"HX-Trigger": "refreshList"}
    try:
        await ctx.api.audits_create_finding(
            audit_id, {"description": str(form.get("description") or "")}
        )
    except ApiError as exc:
        headers = toast("error", problem_text(exc))
    return await _audit_detail(request, ctx, audit_id, headers)


async def _finding_form(
    request: Request,
    ctx: UiContext,
    audit_id: str,
    finding: dict[str, Any],
    labels: dict[str, str],
    *,
    errors: dict[str, str] | None = None,
    message: str = "",
    status: int = 200,
) -> Response:
    cat = await catalogs(ctx.api)
    return render(
        request,
        "audits/_finding_form.html",
        ctx,
        status=status,
        finding=finding,
        labels=labels,
        sections=FORMS["finding"],
        refs=await ref_options(ctx),
        lists=cat["lists"],
        iso=iso_labels(cat),
        errors=errors or {},
        message=message,
        responsible_statuses=RESPONSIBLE_STATUSES,
        self_url=f"/audits/{audit_id}",
    )


@router.get("/audits/{audit_id}/findings/{finding_id}/edit", response_class=HTMLResponse)
async def edit_finding(
    request: Request, audit_id: str, finding_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    audit = await ctx.api.audits_get(audit_id)
    finding = next((dict(f) for f in audit["findings"] if f["id"] == finding_id), None)
    if finding is None:
        return Response(status_code=404)
    return await _finding_form(request, ctx, audit_id, finding, dict(audit["labels"]))


@router.post("/audits/{audit_id}/findings/{finding_id}", response_class=HTMLResponse)
async def save_finding(
    request: Request, audit_id: str, finding_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    form = await request.form()
    audit = await ctx.api.audits_get(audit_id)
    finding = next((dict(f) for f in audit["findings"] if f["id"] == finding_id), None)
    if finding is None:
        return Response(status_code=404)
    sections = FORMS["finding"]
    if not finding["can_edit"]:
        # the responsible person sends only the fields open to them
        sections = [
            {**s, "fields": [f for f in s["fields"] if f.get("responsible")]} for s in sections
        ]
    values = values_from_form(sections, form, True)
    try:
        await ctx.api.audits_update_finding(
            audit_id,
            finding_id,
            {"version": int(str(form.get("version") or finding["version"])), "values": values},
        )
    except ApiError as exc:
        if exc.status not in (403, 409, 412, 422, 428):
            raise
        return await _finding_form(
            request,
            ctx,
            audit_id,
            finding | values,
            dict(audit["labels"]),
            errors=field_errors(exc),
            message=problem_text(exc),
            status=exc.status,
        )
    headers = toast("success", gettext("Saved"), "closeModal", "refreshList")
    return await _audit_detail(request, ctx, audit_id, headers)


@router.post("/audits/{audit_id}/findings/{finding_id}/delete", response_class=HTMLResponse)
async def delete_finding(
    request: Request, audit_id: str, finding_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    headers: dict[str, str] = {}
    try:
        await ctx.api.audits_delete_finding(audit_id, finding_id)
    except ApiError as exc:
        headers = toast("error", problem_text(exc))
    return await _audit_detail(request, ctx, audit_id, headers)


# ---- I&A cockpit -------------------------------------------------------------------------------

LINKS = {
    "process": "/processes/",
    "role": "/roles/",
    "position": "/positions/",
    "risk": "/risks/",
    "opportunity": "/opportunities/",
    "control": "/controls/",
    "kpi": "/kpi/",
    "audit": "/audits/",
    "mandate": "/delegations/",
    "user": "/users/",
}
MODULE_TITLES = {
    "process": N_("Processes"),
    "role": N_("Roles"),
    "position": N_("Positions"),
    "risk": N_("Risks"),
    "opportunity": N_("Opportunities"),
    "control": N_("Controls (ICS)"),
    "audit": N_("Audits"),
    "mandate": N_("Delegations & powers of attorney"),
    "user": N_("User management"),
    "kpi": N_("KPI"),
    "other": N_("Reviews"),
}
