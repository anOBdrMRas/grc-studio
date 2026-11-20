"""Work instructions: rich text per process step, owned by a person, with the approval workflow.
Read by everybody who reads processes; created and deleted by I&A and administration."""

from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.domain import richtext
from grc_api.domain.codes import next_code
from grc_api.errors import ProblemError
from grc_api.models import WorkInstruction
from grc_api.repositories import audit, elements
from grc_api.repositories import processes as proc_repo
from grc_api.schemas.common import ElementPatch, Revision, StateView, WorkflowAction
from grc_api.schemas.instructions import (
    WorkInstructionFields,
    WorkInstructionListItem,
    WorkInstructionOut,
)
from grc_api.services import common
from grc_api.services.context import OrgData, load_org
from grc_api.services.processes import usages

KIND = "instruction"
PREFIX = "WI"


def _need(p: Principal, perm: str) -> None:
    if not p.can(perm):
        raise ProblemError("forbidden", f"Permission {perm} required")


async def list_instructions(db: AsyncSession, p: Principal) -> list[WorkInstructionListItem]:
    _need(p, "processes:read")
    org = await load_org(db)
    counts: dict[str, int] = {}
    for link in await proc_repo.links_of_kind(db, KIND):
        counts[link.target_id] = counts.get(link.target_id, 0) + 1
    return [
        WorkInstructionListItem(
            id=w.id,
            code=w.code,
            title=w.title,
            description=w.description,
            owner_name=org.name(w.owner_user_id) if w.owner_user_id else "",
            steps=counts.get(w.id, 0),
            status=w.status,
            doc_version=w.doc_version,
            is_owner=p.user_id in org.owners(KIND, w),
        )
        for w in await elements.list_all(db, WorkInstruction)
    ]


async def view(
    db: AsyncSession, wi_id: str, p: Principal, org: OrgData | None = None
) -> WorkInstructionOut:
    _need(p, "processes:read")
    org = org or await load_org(db)
    w = await common.get_or_404(db, WorkInstruction, wi_id)
    return WorkInstructionOut(
        **common.fields_of(w, WorkInstructionFields),
        id=w.id,
        custom=w.custom,
        code=w.code,
        status=w.status,
        doc_version=w.doc_version,
        version=w.version,
        created_at=w.created_at,
        updated_at=w.updated_at,
        rights=common.rights(KIND, w, org, p),
        used_in=await usages(db, KIND, w.id),
        workflow=await common.workflow_out(db, KIND, w.id, org),
        released=w.released,
        labels={w.owner_user_id: org.label(w.owner_user_id)} if w.owner_user_id else {},
    )


async def create(db: AsyncSession, title: str, p: Principal) -> WorkInstructionOut:
    _need(p, "processes:manage")
    code = next_code(await elements.codes(db, WorkInstruction), PREFIX)
    await elements.insert(db, WorkInstruction(id=code, code=code, title=title))
    await audit.record(
        db, p.user_id, "create", KIND, code, [{"key": "title", "from": None, "to": title}]
    )
    await db.commit()
    return await view(db, code, p)


async def update(
    db: AsyncSession, wi_id: str, patch: ElementPatch, if_match: str | None, p: Principal
) -> WorkInstructionOut:
    org = await load_org(db)
    w = await common.get_or_404(db, WorkInstruction, wi_id)
    values = dict(patch.values)
    if "content" in values:
        try:
            values["content"] = richtext.clean(str(values["content"] or ""))
        except richtext.RichTextError as exc:
            raise ProblemError("invalid", str(exc)) from exc
    owner = values.get("owner_user_id")
    if owner and owner not in org.users:
        raise ProblemError("invalid", "Unknown person")
    await common.save_element(
        db,
        KIND,
        w,
        WorkInstructionFields,
        values,
        common.expected_version(if_match, patch.version),
        p,
        org,
    )
    await db.commit()
    db.expire_all()
    return await view(db, wi_id, p)


async def delete(db: AsyncSession, wi_id: str, p: Principal) -> None:
    w = await common.get_or_404(db, WorkInstruction, wi_id)
    if not common.rights(KIND, w, await load_org(db), p).can_delete:
        raise ProblemError("forbidden", "You may not delete this element")
    await proc_repo.remove_links_to(db, KIND, wi_id)
    await elements.remove(db, WorkInstruction, wi_id)
    await audit.record(db, p.user_id, "delete", KIND, wi_id)
    await db.commit()


async def workflow(
    db: AsyncSession, wi_id: str, body: WorkflowAction, if_match: str | None, p: Principal
) -> WorkInstructionOut:
    org = await load_org(db)
    w = await common.get_or_404(db, WorkInstruction, wi_id)
    await common.workflow_action(
        db,
        KIND,
        w,
        WorkInstructionFields,
        body.action,
        body.comment,
        body.target_status,
        common.expected_version(if_match, body.version),
        p,
        org,
    )
    await db.commit()
    db.expire_all()
    return await view(db, wi_id, p)


def _short(value: object) -> object:
    """The content in the history as plain text (without markup and embedded images)."""
    if not isinstance(value, str):
        return value
    text = richtext.plain(value)
    return text if len(text) <= 300 else text[:300] + " …"


async def history(db: AsyncSession, wi_id: str, p: Principal) -> list[Revision]:
    _need(p, "processes:read")
    out = await common.revisions(db, KIND, wi_id, await load_org(db))
    for r in out:
        for c in r.changes:
            if c.key == "content":
                c.from_, c.to = _short(c.from_), _short(c.to)
    return out


async def state(db: AsyncSession, wi_id: str, revision_id: int, p: Principal) -> StateView:
    _need(p, "processes:read")
    w = await common.get_or_404(db, WorkInstruction, wi_id)
    return await common.state_after(
        db,
        KIND,
        wi_id,
        revision_id,
        common.state_of(w, WorkInstructionFields),
        await load_org(db),
    )
