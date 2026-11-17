"""Demo data (pseudonymised persons, roles, positions and processes of the prototype)."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.models import (
    AuditEntry,
    Control,
    Kpi,
    KpiMeasurement,
    Mandate,
    Opportunity,
    Position,
    PositionRole,
    Process,
    Risk,
    Role,
    StepAssignment,
    StepLink,
    User,
    WorkflowEntry,
)
from grc_api.schemas.org import RoleFields

DEMO = Path(__file__).with_name("demo.json")
DATES = (
    "position_since",
    "last_review",
    "next_review",
    "last_assessment",
    "last_test",
    "next_test",
    "valid_from",
    "valid_until",
    "revoked_at",
    "accepted_at",
    "registered_at",
    "last_supervision",
    "next_supervision",
)


def _row(d: dict[str, Any], skip: tuple[str, ...]) -> dict[str, Any]:
    out = {k: v for k, v in d.items() if k not in skip}
    for k in DATES:
        if out.get(k):
            out[k] = date.fromisoformat(out[k])
    return out


async def is_empty(db: AsyncSession) -> bool:
    return not (await db.execute(select(func.count()).select_from(User))).scalar()


async def load_demo(db: AsyncSession) -> dict[str, int]:
    data = json.loads(DEMO.read_text(encoding="utf-8"))
    for u in data["users"]:
        db.add(User(**_row(u, ())))
    for r in data["roles"]:
        role = Role(**_row(r, ("workflow",)))
        if r.get("released"):
            # the released state of a changed draft: the draft's fields with the released texts
            base = {k: r.get(k) for k in RoleFields.model_fields}
            role.released = base | r["released"]
        db.add(role)
    for p in data["positions"]:
        db.add(Position(**_row(p, ("workflow", "roles"))))
    for p in data["processes"]:
        db.add(Process(**_row(p, ("workflow", "steps", "links"))))
    for r in data.get("risks", []):
        db.add(Risk(**_row(r, ("workflow",))))
    for o in data.get("opportunities", []):
        db.add(Opportunity(**_row(o, ("workflow",))))
    for c in data.get("controls", []):
        db.add(Control(**_row(c, ())))
    for k in data.get("kpis", []):
        db.add(Kpi(**_row(k, ("measurements",))))
    for m in data.get("mandates", []):
        db.add(Mandate(**_row(m, ("workflow",))))
    await db.flush()
    for p in data["positions"]:
        for i, pr in enumerate(p["roles"]):
            db.add(
                PositionRole(
                    position_id=p["id"], role_id=pr["role_id"], comment=pr["comment"], sort=i
                )
            )
    for p in data["processes"]:
        for s in p["steps"]:
            db.add(StepAssignment(process_id=p["id"], **s))
        for link in p.get("links", []):
            db.add(StepLink(process_id=p["id"], **link))
    for k in data.get("kpis", []):
        for m in k["measurements"]:
            db.add(
                KpiMeasurement(kpi_id=k["id"], date=date.fromisoformat(m["date"]), value=m["value"])
            )
    for kind, items in (
        ("role", data["roles"]),
        ("position", data["positions"]),
        ("process", data["processes"]),
        ("risk", data.get("risks", [])),
        ("opportunity", data.get("opportunities", [])),
        ("mandate", data.get("mandates", [])),
    ):
        for e in items:
            for w in e.get("workflow", []):
                db.add(
                    WorkflowEntry(
                        kind=kind,
                        entity_id=e["id"],
                        step=w["step"],
                        by_user_id=w["by_user_id"],
                        at=datetime.fromisoformat(w["at"]),
                        comment=w["comment"],
                        status=w["status"],
                    )
                )
    db.add(
        AuditEntry(
            actor_id="system",
            action="seed",
            kind="system",
            entity_id="demo",
            note="Demo data loaded",
        )
    )
    await db.commit()
    return {k: len(v) for k, v in data.items()}
