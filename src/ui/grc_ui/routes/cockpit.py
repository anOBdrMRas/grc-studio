"""I&A cockpit, laid out like the prototype: figures, quality overview, approvals, quality
checks and the GRC situation picture."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from grc_client import ApiError
from grc_ui.i18n import N_, gettext
from grc_ui.routes.common import catalogs, plain
from grc_ui.routes.grc import LINKS, MODULE_TITLES
from grc_ui.routes.modules import MODULES, _matrix
from grc_ui.session import UiContext, problem_text, ui_context
from grc_ui.templating import render, toast

router = APIRouter()

# colours of the modules (as in the prototype)
COLORS = {
    "process": "#1f4e79",
    "instruction": "#5f3dc4",
    "risk": "#d64545",
    "opportunity": "#2f9e44",
    "control": "#1971c2",
    "role": "#7048e8",
    "position": "#ae3ec9",
    "mandate": "#c2255c",
    "kpi": "#e8590c",
    "audit": "#0c8599",
    "user": "#495057",
}
KIND_LABELS = {
    "process": N_("Process"),
    "instruction": N_("Work instruction"),
    "role": N_("Role"),
    "position": N_("Position"),
    "risk": N_("Risk"),
    "opportunity": N_("Opportunity"),
}
WORKFLOW_API = {
    "process": "processes",
    "instruction": "instructions",
    "role": "roles",
    "position": "positions",
    "risk": "risks",
    "opportunity": "opportunities",
}
# segments of the life cycle bars: (catalogue value, colour)
RISK_SEGMENTS = [
    ("Closed", "#40c057"),
    ("Accepted", "#94d82d"),
    ("In treatment", "#15aabf"),
    ("Assessed", "#fab005"),
    ("Identified", "#fa5252"),
]
OPPORTUNITY_SEGMENTS = [
    ("Realised", "#40c057"),
    ("In implementation", "#15aabf"),
    ("Assessed", "#fab005"),
    ("Identified", "#ffa94d"),
    ("Discarded", "#adb5bd"),
]
CONTROL_SEGMENTS = [
    ("Effective", "#40c057"),
    ("Partially effective", "#fab005"),
    ("Not effective", "#fa5252"),
    ("Not tested", "#adb5bd"),
]
FINDING_COLORS = {
    "Major nonconformity": "#fa5252",
    "Minor nonconformity": "#fd7e14",
    "Observation": "#4dabf7",
    "Opportunity for improvement": "#9775fa",
}
CHECK_GROUPS = [
    (N_("Processes & organisation"), ("process", "role", "position")),
    (N_("Delegations & persons"), ("mandate", "user")),
    (N_("Risks, opportunities & controls"), ("risk", "opportunity", "control", "other")),
    (N_("Audits & certificates"), ("audit",)),
]


def _segments(values: list[str], spec: list[tuple[str, str]]) -> list[dict[str, Any]]:
    return [{"label": v, "color": c, "n": values.count(v)} for v, c in spec]


def _days(at: Any) -> int | None:
    if not at:
        return None
    when = datetime.fromisoformat(str(at))
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return max(0, (datetime.now(UTC) - when).days)


async def _context(ctx: UiContext) -> dict[str, Any]:
    data = await ctx.api.cockpit_get()
    checks = [plain(c) for c in data["checks"]]
    workflow = {k: plain(v) for k, v in data["workflow"].items()}
    grades = dict(data["grades"])
    processes = await ctx.api.processes_list()
    risks = [plain(x) for x in await ctx.api.risks_list()]
    opportunities = [plain(x) for x in await ctx.api.opportunities_list()]
    controls = [plain(x) for x in await ctx.api.controls_list()]
    kpis = [plain(x) for x in await ctx.api.kpis_list()]
    mandates = [plain(x) for x in await ctx.api.mandates_list()]
    people = {p["id"]: p["name"] for p in await ctx.api.people_list()}
    counts: list[tuple[str, int, str]] = [
        ("process", len(processes), "/processes"),
        ("instruction", len(await ctx.api.instructions_list()), "/instructions"),
        ("risk", len(risks), "/risks"),
        ("opportunity", len(opportunities), "/opportunities"),
        ("control", len(controls), "/controls"),
        ("role", len(await ctx.api.roles_list()), "/roles"),
        ("position", len(await ctx.api.positions_list()), "/positions"),
        ("mandate", len(mandates), "/delegations"),
        ("kpi", len(kpis), "/kpi"),
        ("audit", len(await ctx.api.audits_list()), "/audits"),
    ]
    if ctx.can("users:read"):
        counts.append(("user", len(await ctx.api.users_list()), "/users"))
    quality = [
        {"kind": k, "segments": None, "counts": workflow.get(k)}
        for k in ("process", "instruction", "role", "position")
    ] + [
        {
            "kind": "risk",
            "counts": workflow.get("risk"),
            "segments": _segments([r["treatment_status"] for r in risks], RISK_SEGMENTS),
        },
        {
            "kind": "opportunity",
            "counts": workflow.get("opportunity"),
            "segments": _segments(
                [o["progress_status"] for o in opportunities], OPPORTUNITY_SEGMENTS
            ),
        },
        {
            "kind": "control",
            "counts": None,
            "segments": _segments(
                [c["operating_effectiveness"] for c in controls], CONTROL_SEGMENTS
            ),
        },
    ]
    queue = [plain(r) | {"days": _days(r["submitted_at"])} for r in data["review_queue"]]
    pending = [
        m
        | {
            "waiting_for": N_("Granting") if m["state"] == "draft" else N_("Acceptance"),
            "person": people.get(
                (m["granted_by_user_id"] if m["state"] == "draft" else m["recipient_user_id"])
                or "",
                "–",
            ),
        }
        for m in mandates
        if m["state"] in ("draft", "pending")
    ]
    departments: dict[str, list[int]] = {}  # department → [risks, higher risks]
    for r in risks:
        d = departments.setdefault(r["department"] or gettext("without department"), [0, 0])
        d[0] += 1
        d[1] += 1 if r["level"] == "high" else 0
    by_department = [
        {"department": k, "n": n, "high": high}
        for k, (n, high) in sorted(departments.items(), key=lambda x: (-x[1][1], -x[1][0]))
    ]
    situation = plain(data["situation"])
    lists = (await catalogs(ctx.api))["lists"]
    findings = [
        {"type": t, "n": situation["findings_by_type"].get(t, 0), "color": FINDING_COLORS[t]}
        for t in lists["finding_types"]
        if t in FINDING_COLORS
    ]
    groups = [
        (title, [c for c in checks if c["module"] in modules]) for title, modules in CHECK_GROUPS
    ]
    return {
        "counts": counts,
        "activities": situation["activities"],
        "quality": quality,
        "grades": grades,
        "queue": queue,
        "can_approve": ctx.can("quality:approve"),
        "pending": pending,
        "in_work": [plain(w) for w in data["in_work"]],
        "released": [plain(r) for r in data["recently_released"]],
        "groups": [(t, cs) for t, cs in groups if cs],
        "open_total": sum(1 for c in checks if c["items"]),
        "matrix": await _matrix(ctx, MODULES["risks"], None),
        "risk_mod": MODULES["risks"],
        "by_department": by_department,
        "max_department": max([1, *(n for n, _ in departments.values())]),
        "effectiveness": _segments(
            [c["operating_effectiveness"] for c in controls], CONTROL_SEGMENTS
        ),
        "controls_total": len(controls),
        "coverage": situation["role_coverage"],
        "kpis": kpis,
        "findings": findings,
        "findings_open": situation["findings_open"],
        "findings_overdue": situation["findings_overdue"],
        "links": LINKS,
        "titles": MODULE_TITLES,
        "kind_labels": KIND_LABELS,
        "colors": COLORS,
    }


@router.get("/ia", response_class=HTMLResponse)
async def cockpit(request: Request, ctx: UiContext = Depends(ui_context)) -> Response:
    if not ctx.can("cockpit:read"):
        return render(
            request,
            "error.html",
            ctx,
            status=403,
            message=gettext("You are not allowed to do this."),
        )
    return render(request, "cockpit.html", ctx, **await _context(ctx))


@router.get("/ia/checks/{key}", response_class=HTMLResponse)
async def check_items(request: Request, key: str, ctx: UiContext = Depends(ui_context)) -> Response:
    """The elements a quality check found (dialog)."""
    data = await ctx.api.cockpit_get()
    check = next((plain(c) for c in data["checks"] if c["key"] == key), None)
    if check is None:
        return Response(status_code=404)
    return render(request, "cockpit/_check.html", ctx, check=check, links=LINKS)


@router.post("/ia/review/{kind}/{item_id}", response_class=HTMLResponse)
async def review(
    request: Request, kind: str, item_id: str, ctx: UiContext = Depends(ui_context)
) -> Response:
    """Approve or reject an element waiting for the I&A approval, then show the queue again."""
    form = await request.form()
    api = WORKFLOW_API.get(kind)
    if api is None:
        return Response(status_code=404)
    action = "reject" if form.get("action") == "reject" else "approve"
    comment = str(form.get("comment") or "").strip()
    headers: dict[str, str]
    if action == "reject" and not comment:
        headers = toast("error", gettext("A comment is required to reject."))
    else:
        try:
            await getattr(ctx.api, f"{api}_workflow")(
                item_id,
                {"action": action, "comment": comment, "version": int(str(form.get("version")))},
            )
            headers = toast(
                "success", gettext("Approved") if action == "approve" else gettext("Rejected")
            )
        except ApiError as exc:
            if exc.status not in (403, 409, 412, 422):
                raise
            headers = toast("error", problem_text(exc))
    return render(request, "cockpit/_page.html", ctx, headers=headers, **await _context(ctx))
