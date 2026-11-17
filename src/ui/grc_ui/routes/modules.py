"""Generic list + detail pages (deviation A2: list 1/3, detail 2/3, read view with "Edit")."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from grc_client import ApiError
from grc_ui.formdata import values_from_form
from grc_ui.forms import FORMS
from grc_ui.i18n import N_, gettext
from grc_ui.routes.common import catalogs, iso_labels, ref_options
from grc_ui.session import UiContext, field_errors, problem_text, ui_context
from grc_ui.templating import render, toast

router = APIRouter()


@dataclass(frozen=True)
class Module:
    kind: str
    base: str
    title: str
    singular: str
    read_perm: str
    manage_perm: str
    api: str  # method prefix of the generated client: roles, positions, users
    columns: tuple[tuple[str, str], ...]  # (key, label) of the narrow list


MODULES = {
    "roles": Module(
        "role",
        "/roles",
        N_("Roles"),
        N_("Role"),
        "org:read",
        "org:manage",
        "roles",
        (("role_type", N_("Type")), ("holders", N_("Holder"))),
    ),
    "positions": Module(
        "position",
        "/positions",
        N_("Positions"),
        N_("Position"),
        "org:read",
        "org:manage",
        "positions",
        (("org_unit", N_("Org. unit")), ("holders", N_("Holder"))),
    ),
    "users": Module(
        "user",
        "/users",
        N_("User management"),
        N_("User"),
        "users:read",
        "users:manage",
        "users",
        (("position_title", N_("Position")), ("division", N_("Area"))),
    ),
}


def _m(ctx: UiContext, mod: Module, op: str) -> Callable[..., Awaitable[Any]]:
    fn: Callable[..., Awaitable[Any]] = getattr(ctx.api, f"{mod.api}_{op}")
    return fn


async def _list(ctx: UiContext, mod: Module, q: str = "") -> list[dict[str, Any]]:
    items = [dict(x) for x in await _m(ctx, mod, "list")()]
    needle = q.strip().lower()
    if needle:
        items = [
            x
            for x in items
            if needle in f"{x.get('code', '')} {x.get('title', x.get('name', ''))}".lower()
        ]
    return items


async def _detail(
    request: Request,
    ctx: UiContext,
    mod: Module,
    item_id: str,
    *,
    view: str = "",
    revision: int | None = None,
) -> dict[str, Any]:
    item = dict(await _m(ctx, mod, "get")(item_id))
    cat = await catalogs(ctx.api)
    shown = dict(item)
    banner: dict[str, Any] | None = None
    if view == "released" and item.get("released"):
        shown.update(item["released"])
        banner = {"kind": "released", "version": item["released"].get("doc_version", "")}
    elif revision is not None and mod.kind != "user":
        state = await _m(ctx, mod, "state")(item_id, str(revision))
        shown.update(state["values"])
        banner = {
            "kind": "revision",
            "at": state["at"],
            "actor": state["actor_name"],
            "id": revision,
        }
    return {
        "mod": mod,
        "item": item,
        "shown": shown,
        "sections": FORMS[mod.kind],
        "iso": iso_labels(cat),
        "lists": cat["lists"],
        "banner": banner,
    }


def _detail_urls(mod: Module, item_id: str) -> dict[str, Any]:
    b = f"{mod.base}/{item_id}"
    return {
        "self_url": b,
        "edit_url": f"{b}/edit",
        "save_url": b,
        "workflow_url": f"{b}/workflow",
        "history_url": f"{b}/history",
        "profile_url": f"{b}/profile",
    }


def page_routes(slug: str) -> None:
    mod = MODULES[slug]

    @router.get(mod.base, response_class=HTMLResponse, name=f"{slug}_index")
    async def index(
        request: Request, q: str = "", ctx: UiContext = Depends(ui_context)
    ) -> Response:
        if not ctx.can(mod.read_perm):
            return render(
                request,
                "error.html",
                ctx,
                status=403,
                message=gettext("You are not allowed to do this."),
            )
        items = await _list(ctx, mod, q)
        if request.headers.get("HX-Target") == "list":
            return render(request, "entity/_list.html", ctx, mod=mod, items=items, q=q, selected="")
        return render(
            request,
            "entity/index.html",
            ctx,
            mod=mod,
            items=items,
            q=q,
            selected="",
            detail=None,
            form=None,
        )

    @router.get(mod.base + "/{item_id}", response_class=HTMLResponse, name=f"{slug}_detail")
    async def detail(
        request: Request,
        item_id: str,
        view: str = "",
        revision: int | None = None,
        edit: int = 0,
        ctx: UiContext = Depends(ui_context),
    ) -> Response:
        d = await _detail(request, ctx, mod, item_id, view=view, revision=revision)
        urls = _detail_urls(mod, item_id)
        if request.headers.get("HX-Target") == "detail":
            return render(request, "entity/_detail.html", ctx, **d, **urls)
        items = await _list(ctx, mod)
        # a new element opens in edit mode
        form = {"refs": await ref_options(ctx), "errors": {}, "conflict": False} if edit else None
        return render(
            request,
            "entity/index.html",
            ctx,
            mod=mod,
            items=items,
            q="",
            selected=item_id,
            detail=d | urls,
            form=form,
        )

    @router.get(mod.base + "/{item_id}/edit", response_class=HTMLResponse)
    async def edit(
        request: Request, item_id: str, ctx: UiContext = Depends(ui_context)
    ) -> Response:
        d = await _detail(request, ctx, mod, item_id)
        return render(
            request,
            "entity/_form.html",
            ctx,
            **d,
            **_detail_urls(mod, item_id),
            refs=await ref_options(ctx),
            errors={},
            conflict=False,
        )

    @router.post(mod.base + "/{item_id}", response_class=HTMLResponse)
    async def save(
        request: Request, item_id: str, ctx: UiContext = Depends(ui_context)
    ) -> Response:
        form = await request.form()
        item = dict(await _m(ctx, mod, "get")(item_id))
        manage = ctx.can(mod.manage_perm)
        values = values_from_form(FORMS[mod.kind], form, manage)
        version = int(str(form.get("version") or item["version"]))
        try:
            await _m(ctx, mod, "update")(item_id, {"version": version, "values": values})
        except ApiError as exc:
            if exc.status not in (409, 412, 422, 428):
                raise
            d = await _detail(request, ctx, mod, item_id)
            d["shown"] = d["item"] | values  # keep what was typed
            return render(
                request,
                "entity/_form.html",
                ctx,
                status=exc.status,
                **d,
                **_detail_urls(mod, item_id),
                refs=await ref_options(ctx),
                errors=field_errors(exc),
                conflict=exc.code == "version_conflict",
                message=problem_text(exc),
            )
        d = await _detail(request, ctx, mod, item_id)
        return render(
            request,
            "entity/_detail.html",
            ctx,
            **d,
            **_detail_urls(mod, item_id),
            headers={"HX-Trigger": "refreshList"} | toast("success", gettext("Saved")),
        )

    @router.post(mod.base, response_class=HTMLResponse)
    async def create(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
        form = await request.form()
        title = str(form.get("title") or gettext("New entry")).strip()
        if mod.kind == "user":
            created = await ctx.api.users_create({"last_name": title, "first_name": ""})
        else:
            created = await _m(ctx, mod, "create")({"title": title})
        return Response(
            status_code=204, headers={"HX-Redirect": f"{mod.base}/{created['id']}?edit=1"}
        )

    @router.post(mod.base + "/{item_id}/delete")
    async def delete(
        request: Request, item_id: str, ctx: UiContext = Depends(ui_context)
    ) -> Response:
        await _m(ctx, mod, "delete")(item_id)
        return Response(status_code=204, headers={"HX-Redirect": mod.base})

    @router.post(mod.base + "/{item_id}/workflow", response_class=HTMLResponse)
    async def workflow(
        request: Request, item_id: str, ctx: UiContext = Depends(ui_context)
    ) -> Response:
        form = await request.form()
        body = {
            "action": str(form.get("action")),
            "comment": str(form.get("comment") or ""),
            "target_status": str(form.get("target_status") or "") or None,
            "version": int(str(form.get("version"))),
        }
        headers: dict[str, str] = {"HX-Trigger": "refreshList"}
        try:
            await _m(ctx, mod, "workflow")(item_id, body)
        except ApiError as exc:
            if exc.status not in (403, 409, 412, 422):
                raise
            headers = toast("error", problem_text(exc))
        d = await _detail(request, ctx, mod, item_id)
        return render(
            request, "entity/_detail.html", ctx, **d, **_detail_urls(mod, item_id), headers=headers
        )

    @router.get(mod.base + "/{item_id}/history", response_class=HTMLResponse)
    async def history(
        request: Request, item_id: str, ctx: UiContext = Depends(ui_context)
    ) -> Response:
        revisions = [dict(r) for r in await _m(ctx, mod, "history")(item_id)]
        labels = {f["key"]: f["label"] for s in FORMS[mod.kind] for f in s["fields"]}
        return render(
            request,
            "entity/_history.html",
            ctx,
            revisions=list(reversed(revisions)),
            labels=labels,
            base=f"{mod.base}/{item_id}",
            can_view=mod.kind != "user",
        )

    @router.get(mod.base + "/{item_id}/profile", response_class=HTMLResponse)
    async def profile(
        request: Request, item_id: str, ctx: UiContext = Depends(ui_context)
    ) -> Response:
        d = await _detail(request, ctx, mod, item_id)
        return render(request, "entity/_profile.html", ctx, **d)


for _slug in MODULES:
    page_routes(_slug)
