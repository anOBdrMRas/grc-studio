"""Helpers shared by the page routes."""

from collections.abc import Mapping
from typing import Any

from fastapi import Request

from grc_client import GrcClient
from grc_client.models import Catalogs
from grc_ui.session import UiContext

_catalogs: Catalogs | None = None


async def catalogs(api: GrcClient) -> Catalogs:
    """Value lists and the clause catalogue are constant per API version: cached in memory."""
    global _catalogs
    if _catalogs is None:
        _catalogs = await api.meta_catalogs()
    return _catalogs


async def ref_options(ctx: UiContext) -> dict[str, list[tuple[str, str]]]:
    """Options of reference fields: persons, roles, positions."""
    people = await ctx.api.people_list()
    roles = await ctx.api.roles_list()
    positions = await ctx.api.positions_list()
    processes = await ctx.api.processes_list() if ctx.can("processes:read") else []
    risks = await ctx.api.risks_list() if ctx.can("grc:read") else []
    return {
        "risks": [(x["id"], f"{x['code']} {x['title']}") for x in risks],
        "processes": [(x["id"], f"{x['code']} {x['title']}") for x in processes],
        "people": [(p["id"], p["name"]) for p in people],
        "roles": [(r["id"], f"{r['code']} {r['title']}") for r in roles],
        "positions": [(x["id"], f"{x['code']} {x['title']}") for x in positions],
    }


def iso_labels(cat: Catalogs) -> dict[str, dict[str, str]]:
    return {
        c["id"]: {"label": f"{c['standard']} {c['clause']}", "title": c["title"]}
        for c in cat["iso"]
    }


def is_fragment(request: Request, target: str) -> bool:
    return (
        request.headers.get("HX-Request") == "true" and request.headers.get("HX-Target") == target
    )


def as_dict(x: Any) -> dict[str, Any]:
    return dict(x)


def plain(x: Mapping[str, object]) -> dict[str, Any]:
    """An API response (TypedDict) as a plain dict for the templates."""
    return dict(x)
