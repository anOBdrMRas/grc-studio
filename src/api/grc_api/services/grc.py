"""GRC elements. Risks and opportunities: recorded by everybody, with approval workflow.
Controls and KPI: managed by I&A and administration, owned by the holders of their role."""

from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.domain import kpi as kp
from grc_api.domain import risk as rk
from grc_api.domain.codes import next_code
from grc_api.errors import ProblemError
from grc_api.models import Control, Kpi, KpiMeasurement, Opportunity, Process, Risk
from grc_api.repositories import audit, elements
from grc_api.repositories import grc as grc_repo
from grc_api.repositories import processes as proc_repo
from grc_api.schemas.common import ElementPatch, Revision, StateView, WorkflowAction
from grc_api.schemas.grc import (
    Assessment,
    ControlFields,
    ControlListItem,
    ControlOut,
    KpiFields,
    KpiListItem,
    KpiOut,
    Measurement,
    MeasurementIn,
    OpportunityFields,
    OpportunityListItem,
    OpportunityOut,
    RiskAction,
    RiskFields,
    RiskListItem,
    RiskOut,
)
from grc_api.services import common
from grc_api.services.context import OrgData, load_org
from grc_api.services.processes import usages

PREFIX = {"risk": "R", "opportunity": "CH", "control": "K", "kpi": "KPI"}


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
                actions=[RiskAction.model_validate(a) for a in r.actions],
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
        custom=r.custom,
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
        used_in=await usages(db, "risk", r.id),
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
        custom=o.custom,
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
        used_in=await usages(db, "opportunity", o.id),
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


# ---- controls (ICS) ----------------------------------------------------------------------------


async def list_controls(db: AsyncSession, p: Principal) -> list[ControlListItem]:
    _need(p, "grc:read")
    org = await load_org(db)
    return [
        ControlListItem(
            id=c.id,
            code=c.code,
            title=c.title,
            control_type=c.control_type,
            key_control=c.key_control,
            operating_effectiveness=c.operating_effectiveness,
            is_owner=p.user_id in org.owners("control", c),
        )
        for c in await elements.list_all(db, Control)
    ]


async def control_view(db: AsyncSession, control_id: str, p: Principal) -> ControlOut:
    _need(p, "grc:read")
    org = await load_org(db)
    c = await common.get_or_404(db, Control, control_id)
    risks = {r.id: f"{r.code} {r.title}" for r in await elements.list_all(db, Risk)}
    labels = {x: org.label(x) for x in (c.owner_role_id, c.executor_role_id) if x}
    labels |= {r: risks.get(r, r) for r in c.mitigates_risk_ids}
    return ControlOut(
        **common.fields_of(c, ControlFields),
        id=c.id,
        custom=c.custom,
        code=c.code,
        version=c.version,
        created_at=c.created_at,
        updated_at=c.updated_at,
        rights=common.rights("control", c, org, p),
        used_in=await usages(db, "control", c.id),
        labels=labels,
    )


async def create_control(db: AsyncSession, title: str, p: Principal) -> ControlOut:
    _need(p, "grc:manage")
    code = next_code(await elements.codes(db, Control), PREFIX["control"])
    await elements.insert(db, Control(id=code, code=code, title=title))
    await audit.record(
        db, p.user_id, "create", "control", code, [{"key": "title", "from": None, "to": title}]
    )
    await db.commit()
    return await control_view(db, code, p)


async def update_control(
    db: AsyncSession, control_id: str, patch: ElementPatch, if_match: str | None, p: Principal
) -> ControlOut:
    org = await load_org(db)
    c = await common.get_or_404(db, Control, control_id)
    await common.save_element(
        db,
        "control",
        c,
        ControlFields,
        patch.values,
        common.expected_version(if_match, patch.version),
        p,
        org,
    )
    await db.commit()
    db.expire_all()
    return await control_view(db, control_id, p)


# ---- KPI ---------------------------------------------------------------------------------------


def _can_measure(k: Kpi, org: OrgData, p: Principal) -> bool:
    """Managers, the owners and the holders of the evaluating role record measured values."""
    return (
        p.can("grc:manage")
        or p.user_id in org.owners("kpi", k)
        or (k.evaluator_role_id is not None and p.user_id in org.role_holders(k.evaluator_role_id))
    )


async def list_kpis(db: AsyncSession, p: Principal) -> list[KpiListItem]:
    _need(p, "grc:read")
    org = await load_org(db)
    last = await grc_repo.last_values(db)
    return [
        KpiListItem(
            id=k.id,
            code=k.code,
            title=k.title,
            unit=k.unit,
            last_value=last.get(k.id),
            target=k.target,
            traffic=kp.status(last.get(k.id), k.direction, k.target, k.critical),
            is_owner=p.user_id in org.owners("kpi", k),
        )
        for k in await elements.list_all(db, Kpi)
    ]


async def kpi_view(db: AsyncSession, kpi_id: str, p: Principal) -> KpiOut:
    _need(p, "grc:read")
    org = await load_org(db)
    k = await common.get_or_404(db, Kpi, kpi_id)
    series = [
        Measurement(date=m.date, value=m.value) for m in await grc_repo.measurements(db, k.id)
    ]
    last = series[-1].value if series else None
    return KpiOut(
        **common.fields_of(k, KpiFields),
        id=k.id,
        custom=k.custom,
        code=k.code,
        version=k.version,
        created_at=k.created_at,
        updated_at=k.updated_at,
        measurements=series,
        traffic=kp.status(last, k.direction, k.target, k.critical),
        can_measure=_can_measure(k, org, p),
        rights=common.rights("kpi", k, org, p),
        used_in=await usages(db, "kpi", k.id),
        labels={x: org.label(x) for x in (k.owner_role_id, k.evaluator_role_id) if x},
    )


async def create_kpi(db: AsyncSession, title: str, p: Principal) -> KpiOut:
    _need(p, "grc:manage")
    code = next_code(await elements.codes(db, Kpi), PREFIX["kpi"])
    await elements.insert(db, Kpi(id=code, code=code, title=title))
    await audit.record(
        db, p.user_id, "create", "kpi", code, [{"key": "title", "from": None, "to": title}]
    )
    await db.commit()
    return await kpi_view(db, code, p)


async def update_kpi(
    db: AsyncSession, kpi_id: str, patch: ElementPatch, if_match: str | None, p: Principal
) -> KpiOut:
    org = await load_org(db)
    k = await common.get_or_404(db, Kpi, kpi_id)
    await common.save_element(
        db,
        "kpi",
        k,
        KpiFields,
        patch.values,
        common.expected_version(if_match, patch.version),
        p,
        org,
    )
    await db.commit()
    db.expire_all()
    return await kpi_view(db, kpi_id, p)


async def record_measurement(
    db: AsyncSession, kpi_id: str, body: MeasurementIn, p: Principal
) -> KpiOut:
    """One value per date: a second value for the same date replaces the first."""
    org = await load_org(db)
    k = await common.get_or_404(db, Kpi, kpi_id)
    if not _can_measure(k, org, p):
        raise ProblemError("forbidden", "You may not record values of this KPI")
    previous = await grc_repo.measurement_at(db, kpi_id, body.date)
    if previous is None:
        db.add(
            KpiMeasurement(kpi_id=kpi_id, date=body.date, value=body.value, by_user_id=p.user_id)
        )
    else:
        previous.value = body.value
        previous.by_user_id = p.user_id
    await audit.record(
        db,
        p.user_id,
        "measurement",
        "kpi",
        kpi_id,
        [
            {
                "key": f"value {body.date.isoformat()}",
                "from": previous and previous.value,
                "to": body.value,
            }
        ],
    )
    await db.commit()
    db.expire_all()
    return await kpi_view(db, kpi_id, p)


async def delete_measurement(db: AsyncSession, kpi_id: str, day: date, p: Principal) -> KpiOut:
    org = await load_org(db)
    k = await common.get_or_404(db, Kpi, kpi_id)
    if not _can_measure(k, org, p):
        raise ProblemError("forbidden", "You may not record values of this KPI")
    previous = await grc_repo.measurement_at(db, kpi_id, day)
    if previous is None:
        raise ProblemError("not_found", "No value on this date")
    await audit.record(
        db,
        p.user_id,
        "measurement",
        "kpi",
        kpi_id,
        [{"key": f"value {day.isoformat()}", "from": previous.value, "to": None}],
    )
    await db.delete(previous)
    await db.commit()
    db.expire_all()
    return await kpi_view(db, kpi_id, p)


# ---- shared: delete, workflow, history ---------------------------------------------------------

Model = type[Risk] | type[Opportunity] | type[Control] | type[Kpi]
MODELS: dict[
    str, tuple[Model, type[RiskFields | OpportunityFields | ControlFields | KpiFields]]
] = {
    "risk": (Risk, RiskFields),
    "opportunity": (Opportunity, OpportunityFields),
    "control": (Control, ControlFields),
    "kpi": (Kpi, KpiFields),
}


async def delete(db: AsyncSession, kind: str, id_: str, p: Principal) -> None:
    """Managers delete; the recorder deletes an own draft that was never submitted."""
    model, _ = MODELS[kind]
    obj = await common.get_or_404(db, model, id_)
    org = await load_org(db)
    submitted = kind not in common.RECORDED or await _ever_submitted(db, kind, id_)
    r = common.rights(kind, obj, org, p, ever_submitted=submitted)
    if not r.can_delete:
        raise ProblemError("forbidden", "You may not delete this element")
    await proc_repo.remove_links_to(db, kind, id_)
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
        db, kind, id_, revision_id, common.state_of(obj, fields), await load_org(db)
    )
