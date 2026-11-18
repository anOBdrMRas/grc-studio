"""Excel export (per module and for all modules) and import with preview.

The import never writes directly: it compares the rows with the stored elements, shows a preview
(new / changed / unchanged / errors) and then calls the normal API, so rights, version checks,
validation and history apply exactly as for an edit in the browser.
"""

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import HTMLResponse, Response

from grc_client import ApiError, GrcClient
from grc_ui import excel
from grc_ui.forms import FORMS, Section
from grc_ui.i18n import N_, gettext
from grc_ui.routes.common import catalogs, plain
from grc_ui.routes.modules import MODULES
from grc_ui.session import UiContext, problem_text, ui_context
from grc_ui.templating import render, toast

router = APIRouter()
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MAX_UPLOAD = 5 * 1024 * 1024


@dataclass(frozen=True)
class Kind:
    slug: str
    kind: str
    base: str
    title: str
    api: str  # method prefix of the generated client
    read_perm: str
    manage_perm: str

    @property
    def sections(self) -> list[Section]:
        return FORMS[self.kind]


KINDS: dict[str, Kind] = {
    "processes": Kind(
        "processes",
        "process",
        "/processes",
        N_("Processes"),
        "processes",
        "processes:read",
        "processes:manage",
    ),
    **{
        slug: Kind(slug, m.kind, m.base, m.title, m.api, m.read_perm, m.manage_perm)
        for slug, m in MODULES.items()
    },
}
BY_BASE = {k.base: k for k in KINDS.values()}


def _fn(api: GrcClient, k: Kind, op: str) -> Callable[..., Awaitable[Any]]:
    fn: Callable[..., Awaitable[Any]] = getattr(api, f"{k.api}_{op}")
    return fn


async def _items(api: GrcClient, k: Kind) -> list[dict[str, Any]]:
    """Full elements of a module (the lists carry only a few columns)."""
    return [plain(await _fn(api, k, "get")(x["id"])) for x in await _fn(api, k, "list")()]


async def _lookups(ctx: UiContext) -> excel.Lookups:
    people = {p["id"]: p["name"] for p in await ctx.api.people_list()}
    return excel.Lookups(people=people, lists=dict((await catalogs(ctx.api))["lists"]))


async def _extras(
    ctx: UiContext, kinds: list[Kind], cache: dict[str, list[dict[str, Any]]]
) -> list[excel.ExtraSheet]:
    """Additional tables for export: KPI values, audit findings, process steps."""
    out = []
    slugs = {k.slug for k in kinds}
    if "kpi" in slugs:
        out.append(
            excel.ExtraSheet(
                gettext("KPI values"),
                [gettext("KPI"), gettext("Date"), gettext("Value")],
                [
                    [k["code"], m["date"], m["value"]]
                    for k in cache["kpi"]
                    for m in k["measurements"]
                ],
            )
        )
    if "audits" in slugs:
        lk = await _lookups(ctx)
        out.append(
            excel.ExtraSheet(
                gettext("Findings"),
                [
                    gettext("Audit"),
                    gettext("ID"),
                    gettext("Type"),
                    gettext("Description"),
                    gettext("Responsible person"),
                    gettext("Due date"),
                    gettext("Status"),
                ],
                [
                    [
                        a["code"],
                        f["code"],
                        gettext(f["finding_type"]),
                        f["description"],
                        lk.people.get(f["responsible_user_id"] or "", ""),
                        f["due_date"],
                        gettext(f["status"]),
                    ]
                    for a in cache["audits"]
                    for f in a["findings"]
                ],
            )
        )
    if "processes" in slugs:
        rows: list[list[Any]] = []
        for p in cache["processes"]:
            for el, roles in p["steps"].items():
                rows.extend(
                    [p["code"], el, gettext("Role"), f"{r['code']} {r['title']}", r["raci"]]
                    for r in roles
                )
            for el, links in p["links"].items():
                rows.extend(
                    [
                        p["code"],
                        el,
                        gettext(x["kind"].capitalize()),
                        f"{x['code']} {x['title']}",
                        "",
                    ]
                    for x in links
                )
        out.append(
            excel.ExtraSheet(
                gettext("Process steps"),
                [
                    gettext("Process"),
                    gettext("Process step (element id)"),
                    gettext("Type"),
                    gettext("Element"),
                    "RACI",
                ],
                rows,
            )
        )
    return out


def _download(content: bytes, name: str) -> Response:
    return Response(
        content,
        media_type=XLSX,
        headers={
            "Content-Disposition": f'attachment; filename="{name}-{date.today().isoformat()}.xlsx"'
        },
    )


@router.get("/export.xlsx")
async def export_all(ctx: UiContext = Depends(ui_context)) -> Response:
    """All modules the person may read, one sheet each, plus the additional tables."""
    kinds = [k for k in KINDS.values() if ctx.can(k.read_perm)]
    cache = {k.slug: await _items(ctx.api, k) for k in kinds}
    sheets = [excel.SheetData(gettext(k.title), k.sections, cache[k.slug]) for k in kinds]
    content = excel.workbook(sheets, await _extras(ctx, kinds, cache), await _lookups(ctx))
    return _download(content, "grc-studio")


def export_route(k: Kind) -> None:
    @router.get(k.base + "/export.xlsx", name=f"{k.slug}_export")
    async def export(ctx: UiContext = Depends(ui_context)) -> Response:
        if not ctx.can(k.read_perm):
            return Response(status_code=403)
        items = await _items(ctx.api, k)
        sheets = [excel.SheetData(gettext(k.title), k.sections, items)]
        extras = await _extras(ctx, [k], {k.slug: items})
        return _download(excel.workbook(sheets, extras, await _lookups(ctx)), k.slug)

    @router.get(k.base + "/import", response_class=HTMLResponse, name=f"{k.slug}_import")
    async def import_form(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
        return render(request, "excel/_upload.html", ctx, k=k)

    @router.post(k.base + "/import", response_class=HTMLResponse)
    async def import_preview(
        request: Request, file: UploadFile, ctx: UiContext = Depends(ui_context)
    ) -> Response:
        if not ctx.can(k.manage_perm):
            return render(
                request,
                "excel/_upload.html",
                ctx,
                k=k,
                error=gettext("You are not allowed to do this."),
            )
        content = await file.read(MAX_UPLOAD + 1)
        if len(content) > MAX_UPLOAD:
            return render(
                request,
                "excel/_upload.html",
                ctx,
                k=k,
                error=gettext("The file is larger than 5 MB."),
            )
        lk = await _lookups(ctx)
        try:
            rows, unknown = excel.read_rows(content, k.sections, lk)
        except ValueError as exc:
            return render(request, "excel/_upload.html", ctx, k=k, error=str(exc))
        current = {x["code"]: x for x in await _items(ctx.api, k)}
        plan = []
        for row in rows:
            item = current.get(row.code)
            label = str(
                row.values.get("title")
                or row.values.get("last_name")
                or row.values.get("description")
                or ""
            )[:80]
            entry: dict[str, Any] = {
                "row": row.number,
                "code": row.code,
                "label": label,
                "errors": row.errors,
            }
            if row.errors:
                entry["action"] = "error"
            elif item is None:
                entry |= {"action": "new", "values": row.values}
                if row.code:
                    entry["note"] = gettext(
                        "ID {code} not found – it is created with a new ID."
                    ).format(code=row.code)
            else:
                diff = excel.changes(item, row.values)
                entry |= {
                    "action": "changed" if diff else "unchanged",
                    "id": item["id"],
                    "version": item["version"],
                    "label": label or item.get("title") or item.get("name", ""),
                    "values": diff,
                    "before": {key: item.get(key) for key in diff},
                }
            plan.append(entry)
        labels = {c["key"]: c["label"] for c in excel.columns(k.sections)}
        counts = {
            a: sum(1 for p in plan if p["action"] == a)
            for a in ("new", "changed", "unchanged", "error")
        }
        payload = json.dumps(
            [p for p in plan if p["action"] in ("new", "changed")], ensure_ascii=False
        )
        return render(
            request,
            "excel/_preview.html",
            ctx,
            k=k,
            plan=plan,
            counts=counts,
            unknown=unknown,
            labels=labels,
            payload=payload,
            filename=file.filename or "",
        )

    @router.post(k.base + "/import/apply", response_class=HTMLResponse)
    async def import_apply(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
        form = await request.form()
        plan = json.loads(str(form.get("payload") or "[]"))
        results = []
        for p in plan:
            try:
                if p["action"] == "new":
                    item_id = await _create(ctx.api, k, p["values"])
                    current = plain(await _fn(ctx.api, k, "get")(item_id))
                    rest = excel.changes(current, p["values"])
                    if rest:
                        await _fn(ctx.api, k, "update")(
                            item_id, {"version": current["version"], "values": rest}
                        )
                    results.append(
                        {"row": p["row"], "ok": True, "code": current["code"], "action": "new"}
                    )
                else:
                    await _fn(ctx.api, k, "update")(
                        p["id"], {"version": p["version"], "values": p["values"]}
                    )
                    results.append(
                        {"row": p["row"], "ok": True, "code": p["code"], "action": "changed"}
                    )
            except ApiError as exc:
                results.append(
                    {
                        "row": p["row"],
                        "ok": False,
                        "code": p.get("code", ""),
                        "message": problem_text(exc),
                    }
                )
        ok = sum(1 for r in results if r["ok"])
        headers = toast(
            "success" if ok == len(results) else "error",
            gettext("{ok} of {total} rows applied").format(ok=ok, total=len(results)),
            "refreshList",
        )
        return render(request, "excel/_result.html", ctx, k=k, results=results, headers=headers)


async def _create(api: GrcClient, k: Kind, values: dict[str, Any]) -> str:
    """A new element: the API creates it from its title (persons from their names)."""
    if k.kind == "user":
        created = await api.users_create(
            {
                "last_name": str(values.get("last_name") or "?"),
                "first_name": str(values.get("first_name") or ""),
            }
        )
    else:
        title = values.get("title") or values.get("description") or gettext("New entry")
        created = await _fn(api, k, "create")({"title": str(title)[:300]})
    return str(created["id"])


for _k in KINDS.values():
    export_route(_k)
