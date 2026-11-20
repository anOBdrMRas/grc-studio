"""Process landscape, the process workspace with the BPMN editor (deviation A3) and the step panel."""

import json
from typing import Any

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response

from grc_client import ApiError
from grc_ui import content
from grc_ui.content import flat
from grc_ui.formdata import values_from_form
from grc_ui.i18n import N_, gettext
from grc_ui.routes.common import catalogs, iso_labels, plain, ref_options
from grc_ui.session import UiContext, field_errors, problem_text, ui_context
from grc_ui.templating import render, toast

router = APIRouter()
MAX_BPMN = 5 * 1024 * 1024
CATEGORIES = [N_("Management process"), N_("Core process"), N_("Support process")]


@router.get("/processes", response_class=HTMLResponse)
async def landscape(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    items = [dict(x) for x in await ctx.api.processes_list()]
    bands = [
        (
            c,
            sorted(
                [x for x in items if x["category"] == c],
                key=lambda x: (x["landscape_order"], x["code"]),
            ),
        )
        for c in CATEGORIES
    ]
    return render(request, "processes/index.html", ctx, bands=bands)


@router.post("/processes", response_class=HTMLResponse)
async def create(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    form = await request.form()
    # like the prototype: an empty process, its profile opens in edit mode
    created = await ctx.api.processes_create({"title": str(form.get("title") or "")})
    return Response(
        status_code=204,
        headers={"HX-Redirect": f"/processes/{created['id']}?tab=profile&edit=1"},
    )


async def _profile_ctx(
    ctx: UiContext, process_id: str, revision: int | None = None, view: str = ""
) -> dict[str, Any]:
    item = flat(plain(await ctx.api.processes_get(process_id)))
    cat = await catalogs(ctx.api)
    cfg = await content.load(ctx.api, cat["lists"])
    shown = dict(item)
    banner = None
    if view == "released" and item.get("released"):
        shown.update(item["released"])
        banner = {"kind": "released", "version": item["released"].get("doc_version", "")}
    elif revision is not None:
        st = await ctx.api.processes_state(process_id, str(revision))
        shown.update(st["values"])
        banner = {"kind": "revision", "at": st["at"], "actor": st["actor_name"], "id": revision}
    b = f"/processes/{process_id}/profile"
    return {
        "mod": {"kind": "process", "base": "/processes", "singular": N_("Process")},
        "item": item,
        "shown": shown,
        "sections": cfg.sections("process"),
        "iso": iso_labels(cat),
        "lists": cfg.lists,
        "banner": banner,
        "self_url": b,
        "edit_url": f"{b}/edit",
        "save_url": b,
        "workflow_url": f"/processes/{process_id}/workflow",
        "history_url": f"/processes/{process_id}/history",
        "profile_url": "",
    }


@router.get("/processes/{process_id}", response_class=HTMLResponse)
async def workspace(
    request: Request,
    process_id: str,
    tab: str = "model",
    edit: int = 0,
    ctx: UiContext = Depends(ui_context),
) -> Response:
    item = plain(await ctx.api.processes_get(process_id))
    profile = await _profile_ctx(ctx, process_id) if tab == "profile" else None
    # a new process opens its profile in edit mode
    form = (
        {"refs": await ref_options(ctx), "errors": {}, "conflict": False}
        if profile is not None and edit and item["rights"]["can_edit"]
        else None
    )
    return render(
        request, "processes/workspace.html", ctx, item=item, tab=tab, profile=profile, form=form
    )


@router.get("/processes/{process_id}/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    process_id: str,
    revision: int | None = None,
    view: str = "",
    ctx: UiContext = Depends(ui_context),
) -> Response:
    return render(
        request, "entity/_detail.html", ctx, **await _profile_ctx(ctx, process_id, revision, view)
    )


@router.get("/processes/{process_id}/profile/edit", response_class=HTMLResponse)
async def profile_edit(
    request: Request, process_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    return render(
        request,
        "entity/_form.html",
        ctx,
        **await _profile_ctx(ctx, process_id),
        refs=await ref_options(ctx),
        errors={},
        conflict=False,
    )


@router.post("/processes/{process_id}/profile", response_class=HTMLResponse)
async def profile_save(
    request: Request, process_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    form = await request.form()
    cfg = await content.load(ctx.api, (await catalogs(ctx.api))["lists"])
    values = values_from_form(cfg.sections("process"), form, ctx.can("processes:manage"))
    try:
        await ctx.api.processes_update(
            process_id, {"version": int(str(form.get("version"))), "values": values}
        )
    except ApiError as exc:
        if exc.status not in (409, 412, 422, 428):
            raise
        d = await _profile_ctx(ctx, process_id)
        d["shown"] = d["item"] | values
        return render(
            request,
            "entity/_form.html",
            ctx,
            status=exc.status,
            **d,
            refs=await ref_options(ctx),
            errors=field_errors(exc),
            conflict=exc.code == "version_conflict",
            message=problem_text(exc),
        )
    return render(
        request,
        "entity/_detail.html",
        ctx,
        **await _profile_ctx(ctx, process_id),
        headers=toast("success", gettext("Saved")),
    )


@router.post("/processes/{process_id}/workflow", response_class=HTMLResponse)
async def workflow(
    request: Request, process_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    form = await request.form()
    headers: dict[str, str] = {}
    try:
        await ctx.api.processes_workflow(
            process_id,
            {
                "action": str(form.get("action")),
                "comment": str(form.get("comment") or ""),
                "target_status": str(form.get("target_status") or "") or None,
                "version": int(str(form.get("version"))),
            },
        )
    except ApiError as exc:
        if exc.status not in (403, 409, 412, 422):
            raise
        headers = toast("error", problem_text(exc))
    item = plain(await ctx.api.processes_get(process_id))
    return render(request, "processes/_wfbar.html", ctx, item=item, headers=headers)


@router.get("/processes/{process_id}/wfbar", response_class=HTMLResponse)
async def wfbar(
    request: Request, process_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    item = plain(await ctx.api.processes_get(process_id))
    return render(request, "processes/_wfbar.html", ctx, item=item)


@router.post("/processes/{process_id}/delete")
async def delete(
    request: Request, process_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    await ctx.api.processes_delete(process_id)
    return Response(status_code=204, headers={"HX-Redirect": "/processes"})


@router.get("/processes/{process_id}/history", response_class=HTMLResponse)
async def history(
    request: Request, process_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    revisions = [dict(r) for r in await ctx.api.processes_history(process_id)]
    labels = (await content.load(ctx.api, {})).labels("process")
    return render(
        request,
        "entity/_history.html",
        ctx,
        revisions=list(reversed(revisions)),
        labels=labels,
        base=f"/processes/{process_id}/profile",
        can_view=True,
    )


@router.get("/processes/{process_id}/diagram.xml")
async def diagram_xml(process_id: str, ctx: UiContext = Depends(ui_context)) -> Response:
    d = await ctx.api.processes_diagram(process_id)
    return Response(
        d["xml"], media_type="application/xml", headers={"X-Version": str(d["version"])}
    )


@router.put("/processes/{process_id}/diagram")
async def diagram_save(
    request: Request, process_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    body = json.loads(await request.body())
    try:
        d = await ctx.api.processes_save_diagram(
            process_id, {"xml": str(body["xml"]), "version": int(body["version"])}
        )
    except ApiError as exc:
        return JSONResponse(
            {"message": problem_text(exc), "code": exc.code}, status_code=exc.status
        )
    return JSONResponse({"version": d["version"], "message": gettext("Diagram saved")})


@router.get("/processes/{process_id}/badges.json")
async def badges(process_id: str, ctx: UiContext = Depends(ui_context)) -> Response:
    """Per BPMN element: counts of roles, risks, opportunities, controls and KPI, and ICS gaps."""
    item = await ctx.api.processes_get(process_id)
    out: dict[str, dict[str, Any]] = {}
    for el, roles in item["steps"].items():
        out.setdefault(el, {})["role"] = len(roles)
    for el, links in item["links"].items():
        counts = out.setdefault(el, {})
        for link in links:
            counts[link["kind"]] = counts.get(link["kind"], 0) + 1
    for el in item["ics_gaps"]:
        out.setdefault(el, {})["gap"] = 1
    titles = {
        "role": gettext("Roles"),
        "risk": gettext("Risks"),
        "opportunity": gettext("Opportunities"),
        "control": gettext("Controls (ICS)"),
        "kpi": gettext("KPI"),
        "gap": gettext("Risk without a control in this step"),
    }
    return JSONResponse({"counts": out, "titles": titles})


LINK_GROUPS = (
    ("risk", N_("Risks"), "/risks"),
    ("control", N_("Controls (ICS)"), "/controls"),
    ("opportunity", N_("Opportunities"), "/opportunities"),
    ("kpi", N_("KPI"), "/kpi"),
)


async def _steps(
    request: Request,
    ctx: UiContext,
    process_id: str,
    element_id: str,
    name: str,
    headers: dict[str, str] | None = None,
) -> Response:
    item = plain(await ctx.api.processes_get(process_id))
    roles = [dict(r) for r in await ctx.api.roles_list()]
    assigned = item["steps"].get(element_id, [])
    links = item["links"].get(element_id, [])
    linked = {(x["kind"], x["target_id"]) for x in links}
    candidates: dict[str, list[dict[str, Any]]] = {
        "risk": [plain(x) for x in await ctx.api.risks_list()],
        "opportunity": [plain(x) for x in await ctx.api.opportunities_list()],
        "control": [plain(x) for x in await ctx.api.controls_list()],
        "kpi": [plain(x) for x in await ctx.api.kpis_list()],
    }
    groups = [
        {
            "kind": kind,
            "title": title,
            "base": base,
            "items": [x for x in links if x["kind"] == kind],
            "options": [
                (c["id"], f"{c['code']} {c['title']}")
                for c in candidates[kind]
                if (kind, c["id"]) not in linked
            ],
        }
        for kind, title, base in LINK_GROUPS
    ]
    codes = {c["id"]: f"{c['code']} {c['title']}" for c in candidates["control"]}
    codes |= {c["id"]: f"{c['code']} {c['title']}" for c in candidates["risk"]}
    return render(
        request,
        "processes/_steps.html",
        ctx,
        item=item,
        element_id=element_id,
        name=name,
        assigned=assigned,
        roles=[r for r in roles if r["id"] not in {a["role_id"] for a in assigned}],
        groups=groups,
        gaps=item["ics_gaps"].get(element_id, []),
        codes=codes,
        raci=["R", "A", "C", "I"],
        is_call=element_id in item["call_activities"],
        call=item["calls"].get(element_id),
        processes=[
            (x["id"], f"{x['code']} {x['title']}")
            for x in await ctx.api.processes_list()
            if x["id"] != process_id
        ]
        if element_id in item["call_activities"]
        else [],
        headers=headers,
    )


@router.get("/processes/{process_id}/steps/{element_id}", response_class=HTMLResponse)
async def steps(
    request: Request,
    process_id: str,
    element_id: str,
    name: str = "",
    ctx: UiContext = Depends(ui_context),
) -> Response:
    return await _steps(request, ctx, process_id, element_id, name)


@router.post("/processes/{process_id}/steps/{element_id}/roles", response_class=HTMLResponse)
async def assign(
    request: Request, process_id: str, element_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    form = await request.form()
    headers: dict[str, str] = {"HX-Trigger": "badgesChanged"}
    try:
        await ctx.api.processes_assign_role(
            process_id,
            element_id,
            {
                "role_id": str(form.get("role_id")),
                "raci": str(form.get("raci") or "R"),
                "version": int(str(form.get("version"))),
            },
        )
    except ApiError as exc:
        headers = toast("error", problem_text(exc))
    return await _steps(request, ctx, process_id, element_id, str(form.get("name") or ""), headers)


@router.post(
    "/processes/{process_id}/steps/{element_id}/roles/{role_id}/delete", response_class=HTMLResponse
)
async def unassign(
    request: Request,
    process_id: str,
    element_id: str,
    role_id: str,
    ctx: UiContext = Depends(ui_context),
) -> Response:
    form = await request.form()
    headers: dict[str, str] = {"HX-Trigger": "badgesChanged"}
    try:
        await ctx.api.processes_unassign_role(
            process_id, element_id, role_id, version=int(str(form.get("version")))
        )
    except ApiError as exc:
        headers = toast("error", problem_text(exc))
    return await _steps(request, ctx, process_id, element_id, str(form.get("name") or ""), headers)


@router.post("/processes/{process_id}/steps/{element_id}/call", response_class=HTMLResponse)
async def call_link(
    request: Request, process_id: str, element_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    form = await request.form()
    headers: dict[str, str] = {}
    try:
        await ctx.api.processes_link_call(
            process_id,
            element_id,
            {
                "target_process_id": str(form.get("target_process_id") or "") or None,
                "version": int(str(form.get("version"))),
            },
        )
        headers = toast("success", gettext("Saved"))
    except ApiError as exc:
        headers = toast("error", problem_text(exc))
    return await _steps(request, ctx, process_id, element_id, str(form.get("name") or ""), headers)


@router.get("/processes/{process_id}/diagram.bpmn")
async def diagram_download(process_id: str, ctx: UiContext = Depends(ui_context)) -> Response:
    item = await ctx.api.processes_get(process_id)
    d = await ctx.api.processes_diagram(process_id)
    return Response(
        d["xml"],
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{item["code"]}.bpmn"'},
    )


@router.get("/processes/{process_id}/diagram/import", response_class=HTMLResponse)
async def diagram_import_form(
    request: Request, process_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    item = plain(await ctx.api.processes_get(process_id))
    return render(request, "processes/_import_bpmn.html", ctx, item=item, error="")


@router.post("/processes/{process_id}/diagram/import", response_class=HTMLResponse)
async def diagram_import(
    request: Request, process_id: str, file: UploadFile, ctx: UiContext = Depends(ui_context)
) -> Response:
    item = plain(await ctx.api.processes_get(process_id))
    raw = await file.read(MAX_BPMN + 1)
    error = ""
    if len(raw) > MAX_BPMN:
        error = gettext("The file is larger than 5 MB.")
    else:
        try:
            xml = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            error = gettext("The file is not a BPMN 2.0 diagram (.bpmn).")
    if not error:
        try:
            await ctx.api.processes_save_diagram(
                process_id, {"xml": xml, "version": int(item["version"])}
            )
        except ApiError as exc:
            error = (
                gettext("The file is not a BPMN 2.0 diagram (.bpmn).")
                if exc.code == "invalid"
                else problem_text(exc)
            )
    if error:
        return render(request, "processes/_import_bpmn.html", ctx, item=item, error=error)
    return Response(
        status_code=204,
        headers={"HX-Redirect": f"/processes/{process_id}"}
        | toast("success", gettext("Diagram imported")),
    )


@router.post("/processes/{process_id}/steps/{element_id}/links", response_class=HTMLResponse)
async def link(
    request: Request, process_id: str, element_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    form = await request.form()
    headers: dict[str, str] = {"HX-Trigger": "badgesChanged"}
    try:
        await ctx.api.processes_link_element(
            process_id,
            element_id,
            {
                "kind": str(form.get("kind")),
                "target_id": str(form.get("target_id")),
                "version": int(str(form.get("version"))),
            },
        )
    except ApiError as exc:
        headers = toast("error", problem_text(exc))
    return await _steps(request, ctx, process_id, element_id, str(form.get("name") or ""), headers)


@router.post(
    "/processes/{process_id}/steps/{element_id}/links/{kind}/{target_id}/delete",
    response_class=HTMLResponse,
)
async def unlink(
    request: Request,
    process_id: str,
    element_id: str,
    kind: str,
    target_id: str,
    ctx: UiContext = Depends(ui_context),
) -> Response:
    form = await request.form()
    headers: dict[str, str] = {"HX-Trigger": "badgesChanged"}
    try:
        await ctx.api.processes_unlink_element(
            process_id, element_id, kind, target_id, version=int(str(form.get("version")))
        )
    except ApiError as exc:
        headers = toast("error", problem_text(exc))
    return await _steps(request, ctx, process_id, element_id, str(form.get("name") or ""), headers)
