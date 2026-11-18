"""Administration: content administration (custom fields, additional dropdown values)."""

from collections.abc import Callable
from typing import Any, cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from grc_client import ApiError
from grc_client.models import ContentIn
from grc_ui import content
from grc_ui.content import EXTENDABLE, NEW_SECTION, TYPE_LABELS, Content
from grc_ui.forms import FORMS
from grc_ui.i18n import N_, gettext
from grc_ui.routes.common import catalogs
from grc_ui.routes.modules import MODULES
from grc_ui.session import UiContext, problem_text, ui_context
from grc_ui.templating import render, toast

router = APIRouter()
PERM = "content:manage"

# modules in the order of the menu
TITLES: dict[str, str] = {"process": N_("Processes")} | {m.kind: m.title for m in MODULES.values()}
ORDER = [
    "process",
    "risk",
    "opportunity",
    "control",
    "role",
    "position",
    "mandate",
    "kpi",
    "audit",
    "user",
]
STANDARD_TYPES = {
    "text": N_("Text"),
    "textarea": N_("Long text"),
    "number": N_("Number"),
    "decimal": N_("Number"),
    "date": N_("Date"),
    "bool": N_("Yes/no"),
    "select": N_("Dropdown"),
    "multiselect": N_("Multiple choice"),
    "scale": N_("Scale"),
    "ref": N_("Reference"),
    "refs": N_("References"),
    "iso": N_("Standard references"),
    "iso_one": N_("Standard reference"),
    "readonly": N_("automatic"),
}


def _forbidden(request: Request, ctx: UiContext) -> Response:
    return render(
        request,
        "error.html",
        ctx,
        status=403,
        message=gettext("You are not allowed to do this."),
    )


async def _load(ctx: UiContext) -> Content:
    return await content.load(ctx.api, dict((await catalogs(ctx.api))["lists"]))


def _panel_ctx(cfg: Content, kind: str) -> dict[str, Any]:
    sections = []
    titles = [s["title"] for s in FORMS[kind]]
    custom = cfg.active(kind)
    for sec in FORMS[kind]:
        sections.append(
            {
                "title": sec["title"],
                "standard": [
                    f
                    | {
                        "type_label": STANDARD_TYPES.get(f["kind"], N_("Special field")),
                        "extendable": f["kind"] in EXTENDABLE,
                        "fixed": cfg.base_lists.get(f.get("options", ""), []),
                        "extra": cfg.options.get(f"{kind}.{f['key']}", []),
                    }
                    for f in sec["fields"]
                    if f["kind"] != "risk_guide"
                ],
                "custom": [c for c in custom if c.get("section") == sec["title"]],
            }
        )
    rest = [c for c in custom if c.get("section") not in titles]
    if rest:
        sections.append({"title": NEW_SECTION, "standard": [], "custom": rest})
    return {
        "kind": kind,
        "sections": sections,
        "section_titles": [*titles, NEW_SECTION],
        "type_labels": TYPE_LABELS,
        "with_options": EXTENDABLE,
    }


@router.get("/admin")
async def admin_home() -> Response:
    return RedirectResponse("/admin/content", status_code=303)


@router.get("/admin/content", response_class=HTMLResponse)
async def content_page(
    request: Request, m: str = "risk", ctx: UiContext = Depends(ui_context)
) -> Response:
    if not ctx.can(PERM):
        return _forbidden(request, ctx)
    kind = m if m in ORDER else "risk"
    cfg = await _load(ctx)
    return render(
        request,
        "admin/content.html",
        ctx,
        modules=[(k, TITLES[k]) for k in ORDER],
        **_panel_ctx(cfg, kind),
    )


async def _change(
    request: Request,
    ctx: UiContext,
    kind: str,
    fn: Callable[[dict[str, Any]], str],
) -> Response:
    """Applies `fn` to the configuration, saves it through the API, renders the panel again."""
    if not ctx.can(PERM) or kind not in ORDER:
        return _forbidden(request, ctx)
    cfg = await _load(ctx)
    body: dict[str, Any] = {
        "version": cfg.version,
        "fields": {k: [dict(f) for f in v] for k, v in cfg.fields.items()},
        "options": {k: list(v) for k, v in cfg.options.items()},
    }
    try:
        message = fn(body)
    except KeyError:
        return Response(status_code=404)
    try:
        await ctx.api.content_update(cast(ContentIn, body))
        headers = toast("success", message or gettext("Saved"))
    except ApiError as exc:
        if exc.status not in (409, 412, 422):
            raise
        headers = toast("error", problem_text(exc))
    cfg = await _load(ctx)
    return render(request, "admin/_content.html", ctx, headers=headers, **_panel_ctx(cfg, kind))


def _field(body: dict[str, Any], kind: str, key: str) -> dict[str, Any]:
    for f in body["fields"].get(kind, []):
        if f["key"] == key:
            return dict(f)
    raise KeyError(key)


def _put_field(body: dict[str, Any], kind: str, changed: dict[str, Any]) -> None:
    body["fields"][kind] = [
        changed if f["key"] == changed["key"] else f for f in body["fields"].get(kind, [])
    ]


async def _value(request: Request) -> str:
    return str((await request.form()).get("value") or "").strip()


@router.post("/admin/content/{kind}/options/{key}/add", response_class=HTMLResponse)
async def option_add(
    request: Request, kind: str, key: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    value = await _value(request)

    def fn(body: dict[str, Any]) -> str:
        name = f"{kind}.{key}"
        if value and value not in body["options"].get(name, []):
            body["options"][name] = [*body["options"].get(name, []), value]
        return ""

    return await _change(request, ctx, kind, fn)


@router.post("/admin/content/{kind}/options/{key}/remove", response_class=HTMLResponse)
async def option_remove(
    request: Request, kind: str, key: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    value = await _value(request)

    def fn(body: dict[str, Any]) -> str:
        name = f"{kind}.{key}"
        body["options"][name] = [x for x in body["options"].get(name, []) if x != value]
        return ""

    return await _change(request, ctx, kind, fn)


@router.post("/admin/content/{kind}/fields", response_class=HTMLResponse)
async def field_add(request: Request, kind: str, ctx: UiContext = Depends(ui_context)) -> Response:
    form = await request.form()
    new = {
        "key": "",
        "label": str(form.get("label") or "").strip(),
        "type": str(form.get("type") or "text"),
        "section": str(form.get("section") or NEW_SECTION),
        "options": [
            x.strip()
            for x in str(form.get("options") or "").replace(";", "\n").splitlines()
            if x.strip()
        ],
        "removed": False,
    }

    def fn(body: dict[str, Any]) -> str:
        body["fields"][kind] = [*body["fields"].get(kind, []), new]
        return gettext("Field {name} added").format(name=new["label"])

    return await _change(request, ctx, kind, fn)


@router.post("/admin/content/{kind}/fields/{key}/label", response_class=HTMLResponse)
async def field_label(
    request: Request, kind: str, key: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    label = await _value(request)

    def fn(body: dict[str, Any]) -> str:
        _put_field(body, kind, _field(body, kind, key) | {"label": label})
        return ""

    return await _change(request, ctx, kind, fn)


@router.post("/admin/content/{kind}/fields/{key}/options/add", response_class=HTMLResponse)
async def field_option_add(
    request: Request, kind: str, key: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    value = await _value(request)

    def fn(body: dict[str, Any]) -> str:
        f = _field(body, kind, key)
        if value and value not in f["options"]:
            _put_field(body, kind, f | {"options": [*f["options"], value]})
        return ""

    return await _change(request, ctx, kind, fn)


@router.post("/admin/content/{kind}/fields/{key}/options/remove", response_class=HTMLResponse)
async def field_option_remove(
    request: Request, kind: str, key: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    value = await _value(request)

    def fn(body: dict[str, Any]) -> str:
        f = _field(body, kind, key)
        _put_field(body, kind, f | {"options": [x for x in f["options"] if x != value]})
        return ""

    return await _change(request, ctx, kind, fn)


@router.post("/admin/content/{kind}/fields/{key}/remove", response_class=HTMLResponse)
async def field_remove(
    request: Request, kind: str, key: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    def fn(body: dict[str, Any]) -> str:
        f = _field(body, kind, key)
        _put_field(body, kind, f | {"removed": True})
        return gettext("Field {name} hidden. Stored values are kept.").format(name=f["label"])

    return await _change(request, ctx, kind, fn)
