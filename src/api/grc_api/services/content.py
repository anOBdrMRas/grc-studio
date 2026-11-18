"""Content administration (custom fields, additional dropdown values) and the custom values of
elements."""

from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.domain import content as ct
from grc_api.domain.history import diff
from grc_api.errors import ProblemError
from grc_api.repositories import audit
from grc_api.repositories import settings as settings_repo
from grc_api.schemas.audits import AuditFields
from grc_api.schemas.content import ContentIn, ContentOut, CustomFieldIO
from grc_api.schemas.grc import ControlFields, KpiFields, OpportunityFields, RiskFields
from grc_api.schemas.mandates import MandateFields
from grc_api.schemas.org import PositionFields, RoleFields
from grc_api.schemas.processes import ProcessFields
from grc_api.schemas.users import UserFields
from grc_api.services.context import OrgData

KEY = "content"
FIELDS: dict[str, type[BaseModel]] = {
    "process": ProcessFields,
    "risk": RiskFields,
    "opportunity": OpportunityFields,
    "control": ControlFields,
    "role": RoleFields,
    "position": PositionFields,
    "mandate": MandateFields,
    "kpi": KpiFields,
    "audit": AuditFields,
    "user": UserFields,
}


async def load(db: AsyncSession) -> tuple[ct.Config, int]:
    row = await settings_repo.get(db, KEY)
    return (ct.from_json(row.value), row.version) if row else (ct.Config(), 0)


def _out(cfg: ct.Config, version: int) -> ContentOut:
    return ContentOut(
        version=version,
        fields={k: [CustomFieldIO(**f.__dict__) for f in v] for k, v in cfg.fields.items() if v},
        options={k: v for k, v in cfg.options.items() if v},
        kinds=list(ct.KINDS),
        types=list(ct.TYPES),
    )


async def view(db: AsyncSession) -> ContentOut:
    cfg, version = await load(db)
    return _out(cfg, version)


async def update(
    db: AsyncSession, body: ContentIn, if_match: str | None, p: Principal
) -> ContentOut:
    if not p.can("content:manage"):
        raise ProblemError("forbidden", "Permission content:manage required")
    old, stored = await load(db)
    if if_match:
        try:
            version, status = int(if_match.strip('W/"')), 412
        except ValueError as exc:
            raise ProblemError("invalid", "If-Match must carry the version") from exc
    elif body.version is not None:
        version, status = body.version, 409
    else:
        raise ProblemError(
            "version_required", "Send the version (If-Match header or version field)"
        )
    if version != stored:
        raise _stale(status)
    new = ct.Config(
        fields={k: [ct.CustomField(**f.model_dump()) for f in v] for k, v in body.fields.items()},
        options=dict(body.options),
    )
    try:
        cfg = ct.checked(new, old, {k: set(m.model_fields) for k, m in FIELDS.items()})
    except ct.ContentError as exc:
        raise ProblemError("invalid", str(exc)) from exc
    before = _flat(old)
    after = {k: [] for k in before} | _flat(cfg)
    changes = diff(before, after)
    if changes:
        if not await settings_repo.save(db, KEY, version, ct.to_json(cfg)):
            raise _stale(status)
        await audit.record(db, p.user_id, "update", "content", KEY, changes)
        await db.commit()
    return await view(db)


def _stale(status: int) -> ProblemError:
    return ProblemError(
        "version_conflict",
        "Someone else changed the content administration in the meantime. Load it again.",
        status=status,
    )


def _flat(cfg: ct.Config) -> dict[str, Any]:
    """One history entry per module and per extended dropdown."""
    data = ct.to_json(cfg)
    return {f"fields.{k}": v for k, v in data["fields"].items()} | {
        f"options.{k}": v for k, v in data["options"].items()
    }


# ---- values of elements ------------------------------------------------------------------------


async def custom_values(
    db: AsyncSession,
    kind: str,
    raw: dict[str, Any],
    current: dict[str, Any],
    org: OrgData | None = None,
) -> dict[str, Any]:
    """Checks the "x_…" values sent for an element; returns them as stored."""
    if not raw:
        return {}
    cfg, _ = await load(db)
    try:
        checked = ct.values(cfg, kind, raw, current)
    except ct.ContentError as exc:
        raise ProblemError("invalid", str(exc)) from exc
    fields = cfg.active(kind)
    for k, v in checked.items():
        if fields[k].type == "user" and v and org is not None and v not in org.users:
            raise ProblemError("invalid", f"{fields[k].label}: unknown person")
    return checked


def split(values: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Standard values and custom ("x_…") values of a patch."""
    std = {k: v for k, v in values.items() if not ct.is_custom(k)}
    return std, {k: v for k, v in values.items() if ct.is_custom(k)}
