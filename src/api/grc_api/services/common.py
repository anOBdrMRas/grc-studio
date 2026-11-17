"""Shared machinery: rights, version check, change recording, workflow and history of elements."""

from datetime import date
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.domain import workflow as wf
from grc_api.domain.history import diff, state_at
from grc_api.errors import ProblemError
from grc_api.models import Position, Process, Role, User
from grc_api.repositories import audit, elements
from grc_api.schemas.common import Change, Revision, Rights, StateView, WorkflowEntryOut
from grc_api.services.context import OrgData

Element = Role | Position | Process
KIND_MODEL: dict[str, type[Role] | type[Position] | type[Process]] = {
    "role": Role,
    "position": Position,
    "process": Process,
}
MANAGE = {
    "role": "org:manage",
    "position": "org:manage",
    "process": "processes:manage",
    "user": "users:manage",
}
OWNER_FIELDS = {
    "role": ["role_owner_user_id"],
    "position": ["reports_to_disciplinary_id"],
    "process": ["owner_role_id"],
    "user": [],
}


def rights(kind: str, obj: Element, org: OrgData, p: Principal) -> Rights:
    manage = p.can(MANAGE[kind])
    owner = p.user_id in org.owners(kind, obj)
    in_review = obj.status == "review"
    return Rights(
        can_edit=manage or (owner and not in_review and obj.status != "archived"),
        can_manage=manage,
        can_delete=manage,
        is_owner=owner,
        can_submit=obj.status == "draft" and (owner or manage),
        can_approve=obj.status == "review" and p.can("quality:approve"),
        can_set_status=p.can("workflow:set-status"),
        owner_fields=OWNER_FIELDS[kind],
    )


def expected_version(if_match: str | None, body_version: int | None) -> tuple[int, int]:
    """Version to check and the status code for a stale one (412 via If-Match, 409 via the body)."""
    if if_match:
        try:
            return int(if_match.strip('W/"')), 412
        except ValueError as exc:
            raise ProblemError("invalid", "If-Match must carry the version") from exc
    if body_version is not None:
        return body_version, 409
    raise ProblemError("version_required", "Send the version (If-Match header or version field)")


def stale(status: int) -> ProblemError:
    return ProblemError(
        "version_conflict",
        "Someone else changed this element in the meantime. Load the current values.",
        status=status,
    )


def jsonable(v: Any) -> Any:
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, list):
        return [jsonable(x) for x in v]
    if isinstance(v, BaseModel):
        return v.model_dump(mode="json")
    return v


def fields_of(obj: object, model: type[BaseModel]) -> dict[str, Any]:
    return {k: jsonable(getattr(obj, k)) for k in model.model_fields if hasattr(obj, k)}


def validate_merge(
    model: type[BaseModel], current: dict[str, Any], values: dict[str, Any]
) -> dict[str, Any]:
    unknown = [k for k in values if k not in model.model_fields]
    if unknown:
        raise ProblemError("invalid", f"Unknown fields: {', '.join(unknown)}")
    try:
        merged = model.model_validate({**current, **values})
    except ValidationError as exc:
        errors = [{"loc": [str(x) for x in e["loc"]], "msg": e["msg"]} for e in exc.errors()]
        raise ProblemError("invalid", "Invalid values", errors=errors) from exc
    return merged.model_dump(mode="json")


async def save_element(
    db: AsyncSession,
    kind: str,
    obj: Element,
    model: type[BaseModel],
    values: dict[str, Any],
    version: tuple[int, int],
    p: Principal,
    org: OrgData,
    *,
    column_values: dict[str, Any] | None = None,
    action: str = "update",
    note: str = "",
    vars_: dict[str, str] | None = None,
    before_extra: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Checks the rights, records the changes, reopens a released element edited by its owner."""
    r = rights(kind, obj, org, p)
    if not r.can_edit:
        raise ProblemError("forbidden", "You may not edit this element")
    if not r.can_manage and any(
        k in values and values[k] != jsonable(getattr(obj, k)) for k in r.owner_fields
    ):
        raise ProblemError("forbidden", "Only the administration and the I&A team change the owner")
    before = fields_of(obj, model) | (before_extra or {})
    after = validate_merge(model, before, values) if values else before
    changes = diff(before, after)
    cols = dict(column_values or {})
    if not changes and not cols and not note:
        return []
    extra: dict[str, Any] = {}
    if wf.reopens(obj.status, r.can_manage):  # type: ignore[arg-type]
        extra = {
            "status": "draft",
            "released": obj.released or {**before, "doc_version": obj.doc_version},
        }
        await audit.add_workflow(db, kind, obj.id, "reopened", p.user_id, "", "draft")
        changes.append({"key": "status", "from": obj.status, "to": "draft"})
    db_values = {k: to_column(model, k, v) for k, v in after.items() if k != "roles"} | cols | extra
    if not await elements.update_versioned(db, type(obj), obj.id, version[0], db_values):
        raise stale(version[1])
    await audit.record(db, p.user_id, action, kind, obj.id, changes, note, vars_)
    return changes


def to_column(model: type[BaseModel], key: str, value: Any) -> Any:
    ann = model.model_fields[key].annotation
    if value and ann in (date, date | None):
        return date.fromisoformat(value)
    return value


async def workflow_action(
    db: AsyncSession,
    kind: str,
    obj: Element,
    model: type[BaseModel],
    action: str,
    comment: str,
    target: str | None,
    version: tuple[int, int],
    p: Principal,
    org: OrgData,
) -> None:
    r = rights(kind, obj, org, p)
    entries = await audit.workflow(db, kind, obj.id)
    submitted = next((e.by_user_id for e in reversed(entries) if e.step == "submitted"), None)
    actor = wf.Actor(
        p.user_id, r.is_owner, r.can_manage, p.can("quality:approve"), p.can("workflow:set-status")
    )
    try:
        t = wf.transition(
            obj.status,  # type: ignore[arg-type]
            action,  # type: ignore[arg-type]
            actor,
            obj.doc_version,
            ever_released=any(e.step == "approved" for e in entries),
            submitted_by=submitted,
            comment=comment,
            target=target,  # type: ignore[arg-type]
        )
    except wf.WorkflowError as exc:
        raise ProblemError(exc.code, exc.detail) from exc
    values: dict[str, Any] = {"status": t.status, "doc_version": t.doc_version}
    if t.clears_released:
        values["released"] = None
    if t.status == "released" and isinstance(obj, Role | Position):
        values["last_review"] = date.today()
    if not await elements.update_versioned(db, type(obj), obj.id, version[0], values):
        raise stale(version[1])
    await audit.add_workflow(db, kind, obj.id, t.step, p.user_id, comment, t.status)
    changes = [{"key": "status", "from": obj.status, "to": t.status}]
    if t.doc_version != obj.doc_version:
        changes.append({"key": "doc_version", "from": obj.doc_version, "to": t.doc_version})
    await audit.record(db, p.user_id, "workflow", kind, obj.id, changes, t.step)


async def workflow_out(
    db: AsyncSession, kind: str, id_: str, org: OrgData
) -> list[WorkflowEntryOut]:
    return [
        WorkflowEntryOut(
            step=e.step,
            by_user_id=e.by_user_id,
            by_name=org.name(e.by_user_id),
            at=e.at,
            comment=e.comment,
            status=e.status,
        )
        for e in await audit.workflow(db, kind, id_)
    ]


async def revisions(db: AsyncSession, kind: str, id_: str, org: OrgData) -> list[Revision]:
    return [
        Revision(
            id=e.id,
            at=e.at,
            actor_id=e.actor_id,
            actor_name=org.name(e.actor_id),
            action=e.action,
            changes=[Change.model_validate(c) for c in e.changes],
            note=e.note,
            vars=e.vars,
        )
        for e in await audit.history(db, kind, id_)
    ]


async def state_after(
    db: AsyncSession, kind: str, id_: str, revision_id: int, current: dict[str, Any], org: OrgData
) -> StateView:
    entries = await audit.history(db, kind, id_)
    idx = next((i for i, e in enumerate(entries) if e.id == revision_id), None)
    if idx is None:
        raise ProblemError("not_found", "Change not found")
    later = [e.changes for e in reversed(entries[idx + 1 :])]
    e = entries[idx]
    return StateView(
        revision_id=e.id, at=e.at, actor_name=org.name(e.actor_id), values=state_at(current, later)
    )


async def get_or_404(
    db: AsyncSession, model: type[User] | type[Role] | type[Position] | type[Process], id_: str
) -> Any:
    obj = await elements.get(db, model, id_)
    if obj is None:
        raise ProblemError("not_found", "Element not found")
    return obj
