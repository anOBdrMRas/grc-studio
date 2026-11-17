"""Risks and opportunities: recorded by everybody, owned by a person (risk) or a role (opportunity)."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.domain import risk as rk
from grc_api.domain.codes import next_code
from grc_api.errors import ProblemError
from grc_api.models import Opportunity, Process, Risk
from grc_api.repositories import audit, elements
from grc_api.schemas.common import ElementPatch, Revision, StateView, WorkflowAction
from grc_api.schemas.grc import (
    Assessment,
    OpportunityFields,
    OpportunityListItem,
    OpportunityOut,
    RiskFields,
    RiskListItem,
    RiskOut,
)
from grc_api.services import common
from grc_api.services.context import OrgData, load_org

PREFIX = {"risk": "R", "opportunity": "CH"}


def _need(p: Principal, perm: str) -> None:
    if not p.can(perm):
        raise ProblemError("forbidden", f"Permission {perm} required")


def assessment(likelihood: int, impact: int) -> Assessment:
    s = rk.score(likelihood, impact)
    return Assessment(score=s, level=rk.level(s), high=s > rk.HIGH_ABOVE)


async def _process_labels(db: AsyncSession) -> dict[str, str]:
    return {x.id: f"{x.code} {x.title}" for x in await elements.list_all(db, Process)}


async def _ever_submitted(db: AsyncSession, kind: str, id_: str) -> bool:
    return any(e.step == "submitted" for e in await audit.workflow(db, kind, id_))


# ---- risks -------------------------------------------------------------------------------------


async def list_risks(db: AsyncSession, p: Principal) -> list[RiskListItem]:
    _need(p, "grc:read")
    org = await load_org(db)
    out = []
    for r in await elements.list_all(db, Risk):
        s = rk.score(r.likelihood, r.impact)
        out.append(
            RiskListItem(
                id=r.id,
                code=r.code,
                title=r.title,
                department=r.department,
                owner_name=org.name(r.owner_user_id) if r.owner_user_id else "",
                likelihood=r.likelihood,
                impact=r.impact,
                score=s,
                level=rk.level(s),
                treatment_status=r.treatment_status,
                status=r.status,
                is_owner=p.user_id in org.owners("risk", r),
            )
        )
    return out


async def risk_view(
    db: AsyncSession, risk_id: str, p: Principal, org: OrgData | None = None
) -> RiskOut:
    _need(p, "grc:read")
    org = org or await load_org(db)
    r = await common.get_or_404(db, Risk, risk_id)
    processes = await _process_labels(db)
    people = [r.owner_user_id, r.created_by_user_id, *(a.get("owner_user_id") for a in r.actions)]
    labels = {x: org.name(x) for x in people if x}
    labels |= {x: processes.get(x, x) for x in r.process_ids}
    return RiskOut(
        **common.fields_of(r, RiskFields),
        id=r.id,
        code=r.code,
        title=r.title,
        status=r.status,
        doc_version=r.doc_version,
        version=r.version,
        created_at=r.created_at,
        updated_at=r.updated_at,
        created_by_user_id=r.created_by_user_id,
        assessment=assessment(r.likelihood, r.impact),
        rights=common.rights(
            "risk", r, org, p, ever_submitted=await _ever_submitted(db, "risk", r.id)
        ),
        workflow=await common.workflow_out(db, "risk", r.id, org),
        released=r.released,
        labels=labels,
    )


async def create_risk(db: AsyncSession, description: str, p: Principal) -> RiskOut:
    """The text typed when recording becomes the description; the recorder owns the draft."""
    _need(p, "grc:record")
    code = next_code(await elements.codes(db, Risk), PREFIX["risk"])
    await elements.insert(
        db,
        Risk(
            id=code,
            code=code,
            title=rk.title_from_description(description),
            description=description,
            treatment_status="Identified",
            owner_user_id=p.user_id,
            created_by_user_id=p.user_id,
        ),
    )
    await audit.record(
        db,
        p.user_id,
        "create",
        "risk",
        code,
        [{"key": "description", "from": None, "to": description}],
    )
    await db.commit()
    return await risk_view(db, code, p)


async def update_risk(
    db: AsyncSession, risk_id: str, patch: ElementPatch, if_match: str | None, p: Principal
) -> RiskOut:
    org = await load_org(db)
    r = await common.get_or_404(db, Risk, risk_id)
    cols: dict[str, Any] = {}
    if "description" in patch.values:
        cols["title"] = rk.title_from_description(str(patch.values["description"] or ""))
    await common.save_element(
        db,
        "risk",
        r,
        RiskFields,
        patch.values,
        common.expected_version(if_match, patch.version),
        p,
        org,
        column_values=cols,
    )
    await db.commit()
    db.expire_all()
    return await risk_view(db, risk_id, p)


# ---- opportunities -----------------------------------------------------------------------------


async def list_opportunities(db: AsyncSession, p: Principal) -> list[OpportunityListItem]:
    _need(p, "grc:read")
    org = await load_org(db)
    return [
        OpportunityListItem(
            id=o.id,
            code=o.code,
            title=o.title,
            category=o.category,
            owner_role_title=org.roles[o.owner_role_id].title
            if o.owner_role_id in org.roles
            else "",
            potential=o.likelihood * o.benefit_score,
            progress_status=o.progress_status,
            status=o.status,
            is_owner=p.user_id in org.owners("opportunity", o),
        )
        for o in await elements.list_all(db, Opportunity)
    ]


async def opportunity_view(
    db: AsyncSession, opp_id: str, p: Principal, org: OrgData | None = None
) -> OpportunityOut:
    _need(p, "grc:read")
    org = org or await load_org(db)
    o = await common.get_or_404(db, Opportunity, opp_id)
    refs = [o.owner_role_id, o.created_by_user_id]
    return OpportunityOut(
        **common.fields_of(o, OpportunityFields),
        id=o.id,
        code=o.code,
        status=o.status,
        doc_version=o.doc_version,
        version=o.version,
        created_at=o.created_at,
        updated_at=o.updated_at,
        created_by_user_id=o.created_by_user_id,
        potential=o.likelihood * o.benefit_score,
        rights=common.rights(
            "opportunity",
            o,
            org,
            p,
            ever_submitted=await _ever_submitted(db, "opportunity", o.id),
        ),
        workflow=await common.workflow_out(db, "opportunity", o.id, org),
        released=o.released,
        labels={x: org.label(x) for x in refs if x},
    )


async def create_opportunity(db: AsyncSession, title: str, p: Principal) -> OpportunityOut:
    _need(p, "grc:record")
    code = next_code(await elements.codes(db, Opportunity), PREFIX["opportunity"])
    await elements.insert(
        db,
        Opportunity(
            id=code,
            code=code,
            title=title,
            progress_status="Identified",
            created_by_user_id=p.user_id,
        ),
    )
    await audit.record(
        db, p.user_id, "create", "opportunity", code, [{"key": "title", "from": None, "to": title}]
    )
    await db.commit()
    return await opportunity_view(db, code, p)


async def update_opportunity(
    db: AsyncSession, opp_id: str, patch: ElementPatch, if_match: str | None, p: Principal
) -> OpportunityOut:
    org = await load_org(db)
    o = await common.get_or_404(db, Opportunity, opp_id)
    await common.save_element(
        db,
        "opportunity",
        o,
        OpportunityFields,
        patch.values,
        common.expected_version(if_match, patch.version),
        p,
        org,
    )
    await db.commit()
    db.expire_all()
    return await opportunity_view(db, opp_id, p)


# ---- shared: delete, workflow, history ---------------------------------------------------------

MODELS: dict[str, tuple[type[Risk] | type[Opportunity], type[RiskFields | OpportunityFields]]] = {
    "risk": (Risk, RiskFields),
    "opportunity": (Opportunity, OpportunityFields),
}


async def delete(db: AsyncSession, kind: str, id_: str, p: Principal) -> None:
    """Managers delete; the recorder deletes an own draft that was never submitted."""
    model, _ = MODELS[kind]
    obj = await common.get_or_404(db, model, id_)
    org = await load_org(db)
    r = common.rights(kind, obj, org, p, ever_submitted=await _ever_submitted(db, kind, id_))
    if not r.can_delete:
        raise ProblemError("forbidden", "You may not delete this element")
    await elements.remove(db, model, id_)
    await audit.record(db, p.user_id, "delete", kind, id_)
    await db.commit()


async def workflow(
    db: AsyncSession, kind: str, id_: str, body: WorkflowAction, if_match: str | None, p: Principal
) -> None:
    model, fields = MODELS[kind]
    org = await load_org(db)
    obj = await common.get_or_404(db, model, id_)
    await common.workflow_action(
        db,
        kind,
        obj,
        fields,
        body.action,
        body.comment,
        body.target_status,
        common.expected_version(if_match, body.version),
        p,
        org,
    )
    await db.commit()
    db.expire_all()


async def history(db: AsyncSession, kind: str, id_: str, p: Principal) -> list[Revision]:
    _need(p, "grc:read")
    return await common.revisions(db, kind, id_, await load_org(db))


async def state(db: AsyncSession, kind: str, id_: str, revision_id: int, p: Principal) -> StateView:
    _need(p, "grc:read")
    model, fields = MODELS[kind]
    obj = await common.get_or_404(db, model, id_)
    return await common.state_after(
        db, kind, id_, revision_id, common.fields_of(obj, fields), await load_org(db)
    )
