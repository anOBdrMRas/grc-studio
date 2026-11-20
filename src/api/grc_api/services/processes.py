"""Processes: landscape, profile, BPMN diagram and the roles of the steps."""

from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.auth.principal import Principal
from grc_api.domain import bpmn_draft, ics
from grc_api.domain.bpmn import activities, call_activities, element_names, is_bpmn
from grc_api.domain.catalogs import PROCESS_CATEGORIES
from grc_api.domain.codes import next_code
from grc_api.errors import ProblemError
from grc_api.models import Control, Kpi, Opportunity, Process, Risk, WorkInstruction
from grc_api.repositories import audit, elements
from grc_api.repositories import processes as proc_repo
from grc_api.schemas.assistant import DraftCreate
from grc_api.schemas.common import ElementPatch, Revision, StateView, WorkflowAction
from grc_api.schemas.grc import Usage
from grc_api.schemas.processes import (
    CallerRef,
    CallLinkIn,
    DiagramIn,
    DiagramOut,
    IcsGap,
    ProcessFields,
    ProcessListItem,
    ProcessOut,
    ProcessRef,
    StepLinkIn,
    StepLinkOut,
    StepNoteIn,
    StepRole,
    StepRoleIn,
)
from grc_api.services import common
from grc_api.services.context import OrgData, load_org

EMPTY_DIAGRAM = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="StartEvent_1" name="Start" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">
        <dc:Bounds x="180" y="160" width="36" height="36" />
      </bpmndi:BPMNShape>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
"""


def _need(p: Principal, perm: str) -> None:
    if not p.can(perm):
        raise ProblemError("forbidden", f"Permission {perm} required")


async def list_processes(db: AsyncSession, p: Principal) -> list[ProcessListItem]:
    _need(p, "processes:read")
    org = await load_org(db)
    my_roles = org.roles_of(p.user_id)
    mine: dict[str, set[str]] = {}
    for a in await proc_repo.assignments(db):
        if a.role_id in my_roles:
            mine.setdefault(a.process_id, set()).add(a.element_id)
    out = []
    for x in await elements.list_all(db, Process):
        owner = org.roles.get(x.owner_role_id or "")
        out.append(
            ProcessListItem(
                id=x.id,
                code=x.code,
                title=x.title,
                category=x.category,
                area=x.area,
                landscape_order=x.landscape_order,
                status=x.status,
                owner_role_title=owner.title if owner else "",
                is_owner=p.user_id in org.owners("process", x),
                my_steps=len(mine.get(x.id, set()) & {el for el, _ in activities(x.xml)}),
            )
        )
    return out


async def process_view(
    db: AsyncSession, process_id: str, p: Principal, org: OrgData | None = None
) -> ProcessOut:
    _need(p, "processes:read")
    org = org or await load_org(db)
    x = await common.get_or_404(db, Process, process_id)
    steps: dict[str, list[StepRole]] = {}
    for a in await proc_repo.assignments(db, x.id):
        role = org.roles.get(a.role_id)
        if role:
            steps.setdefault(a.element_id, []).append(
                StepRole(role_id=role.id, code=role.code, title=role.title, raci=a.raci)
            )
    elements_by_kind = await grc_index(db)
    links: dict[str, list[StepLinkOut]] = {}
    for link in await proc_repo.links(db, x.id):
        target = elements_by_kind[link.kind].get(link.target_id)
        if target:
            links.setdefault(link.element_id, []).append(
                StepLinkOut(
                    kind=link.kind,
                    target_id=link.target_id,
                    code=target[0],
                    title=target[1],
                )
            )
    mitigates = await mitigation(db)
    gaps: dict[str, list[IcsGap]] = {}
    for element_id, items in links.items():
        found = ics.gaps(
            [i.target_id for i in items if i.kind == "risk"],
            [i.target_id for i in items if i.kind == "control"],
            mitigates,
        )
        if found:
            gaps[element_id] = [
                IcsGap(risk_id=g.risk_id, suggestions=list(g.suggestions)) for g in found
            ]
    others = {p.id: p for p in await elements.list_all(db, Process)}
    calls = {
        el: ProcessRef(process_id=t.id, code=t.code, title=t.title)
        for el, target in (x.call_links or {}).items()
        if (t := others.get(target))
    }
    called_by = [
        CallerRef(
            process_id=o.id,
            code=o.code,
            title=o.title,
            element_id=el,
            element_name=call_activities(o.xml).get(el, el),
        )
        for o in others.values()
        if o.id != x.id
        for el, target in (o.call_links or {}).items()
        if target == x.id
    ]
    return ProcessOut(
        **common.fields_of(x, ProcessFields),
        id=x.id,
        custom=x.custom,
        code=x.code,
        status=x.status,
        doc_version=x.doc_version,
        version=x.version,
        created_at=x.created_at,
        updated_at=x.updated_at,
        rights=common.rights("process", x, org, p),
        owners=[org.name(u) for u in org.owners("process", x)],
        steps=steps,
        links=links,
        ics_gaps=gaps,
        activities={el: name for el, name in activities(x.xml)},
        step_notes=dict(x.step_notes or {}),
        call_activities=call_activities(x.xml),
        calls=calls,
        called_by=called_by,
        workflow=await common.workflow_out(db, "process", x.id, org),
        released=x.released,
        labels={x.owner_role_id: org.label(x.owner_role_id)} if x.owner_role_id else {},
    )


async def create_process(db: AsyncSession, title: str, p: Principal) -> ProcessOut:
    _need(p, "processes:manage")
    code = next_code(await elements.codes(db, Process), "P")
    await elements.insert(db, Process(id=code, code=code, title=title, xml=EMPTY_DIAGRAM))
    await audit.record(
        db, p.user_id, "create", "process", code, [{"key": "title", "from": None, "to": title}]
    )
    await db.commit()
    return await process_view(db, code, p)


async def create_from_draft(db: AsyncSession, body: DraftCreate, p: Principal) -> ProcessOut:
    """A new draft process with a generated diagram and the roles of its steps."""
    _need(p, "processes:manage")
    org = await load_org(db)
    code = next_code(await elements.codes(db, Process), "P")
    steps = [
        bpmn_draft.Step(s.name.strip() or "?", s.type, s.role_id, s.raci, s.no.strip())
        for s in body.steps
    ]
    xml, ids = bpmn_draft.generate(
        body.title.strip(), steps, code.replace("-", ""), body.start.strip(), body.end.strip()
    )
    if not is_bpmn(xml):
        raise ProblemError("invalid", "The draft could not be turned into a diagram")
    category = body.category if body.category in PROCESS_CATEGORIES else "Core process"
    await elements.insert(
        db,
        Process(
            id=code,
            code=code,
            title=body.title.strip(),
            description=body.description.strip(),
            category=category,
            area=body.area.strip(),
            xml=xml,
        ),
    )
    for s, element_id in zip(steps, ids, strict=True):
        if s.role and s.role in org.roles and s.type != "decision":
            await proc_repo.add(db, code, element_id, s.role, s.raci)
    await audit.record(
        db,
        p.user_id,
        "create",
        "process",
        code,
        [{"key": "title", "from": None, "to": body.title.strip()}],
        "Created from a draft",
    )
    await db.commit()
    return await process_view(db, code, p)


async def update_process(
    db: AsyncSession, process_id: str, patch: ElementPatch, if_match: str | None, p: Principal
) -> ProcessOut:
    org = await load_org(db)
    x = await common.get_or_404(db, Process, process_id)
    await common.save_element(
        db,
        "process",
        x,
        ProcessFields,
        patch.values,
        common.expected_version(if_match, patch.version),
        p,
        org,
    )
    await db.commit()
    db.expire_all()
    return await process_view(db, process_id, p)


async def delete_process(db: AsyncSession, process_id: str, p: Principal) -> None:
    _need(p, "processes:manage")
    await common.get_or_404(db, Process, process_id)
    await elements.remove(db, Process, process_id)
    await audit.record(db, p.user_id, "delete", "process", process_id)
    await db.commit()


async def diagram(db: AsyncSession, process_id: str, p: Principal) -> DiagramOut:
    _need(p, "processes:read")
    x = await common.get_or_404(db, Process, process_id)
    return DiagramOut(xml=x.xml, version=x.version)


async def save_diagram(
    db: AsyncSession, process_id: str, body: DiagramIn, if_match: str | None, p: Principal
) -> DiagramOut:
    org = await load_org(db)
    x = await common.get_or_404(db, Process, process_id)
    if not is_bpmn(body.xml):
        raise ProblemError("invalid", "The diagram is not a valid BPMN 2.0 document")
    if body.xml != x.xml:
        await common.save_element(
            db,
            "process",
            x,
            ProcessFields,
            {},
            common.expected_version(if_match, body.version),
            p,
            org,
            column_values={"xml": body.xml},
            action="diagram",
            note="Diagram changed",
        )
        await db.commit()
        db.expire_all()
    return await diagram(db, process_id, p)


async def _step_change(
    db: AsyncSession,
    process_id: str,
    version: tuple[int, int],
    p: Principal,
    note: str,
    vars_: dict[str, str],
) -> None:
    """A change of a step assignment counts as a change of the process (version, rights, reopening, history)."""
    org = await load_org(db)
    x = await common.get_or_404(db, Process, process_id)
    await common.save_element(
        db,
        "process",
        x,
        ProcessFields,
        {},
        version,
        p,
        org,
        column_values={},
        action="assignment",
        note=note,
        vars_=vars_,
    )


async def link_call(
    db: AsyncSession,
    process_id: str,
    element_id: str,
    body: CallLinkIn,
    if_match: str | None,
    p: Principal,
) -> ProcessOut:
    """Links a call activity to the process it calls (or removes the link)."""
    org = await load_org(db)
    x = await common.get_or_404(db, Process, process_id)
    names = call_activities(x.xml)
    if element_id not in names:
        raise ProblemError("invalid", "The element is not a call activity of this diagram")
    target = body.target_process_id or None
    if target is not None:
        if target == process_id:
            raise ProblemError("invalid", "A process cannot call itself")
        t = await elements.get(db, Process, target)
        if t is None:
            raise ProblemError("invalid", "Unknown process")
        label = f"{t.code} {t.title}"
    links = dict(x.call_links or {})
    if links.get(element_id) == target:
        return await process_view(db, process_id, p)
    if target is None:
        links.pop(element_id, None)
        note, vars_ = "Link of {step} removed", {"step": names[element_id]}
    else:
        links[element_id] = target
        note, vars_ = "{step} calls {process}", {"step": names[element_id], "process": label}
    await common.save_element(
        db,
        "process",
        x,
        ProcessFields,
        {},
        common.expected_version(if_match, body.version),
        p,
        org,
        column_values={"call_links": links},
        action="assignment",
        note=note,
        vars_=vars_,
    )
    await db.commit()
    db.expire_all()
    return await process_view(db, process_id, p)


async def set_step_note(
    db: AsyncSession,
    process_id: str,
    element_id: str,
    body: StepNoteIn,
    if_match: str | None,
    p: Principal,
) -> ProcessOut:
    """Description of a step (definition, specifics); a change of the process like any other."""
    org = await load_org(db)
    x = await common.get_or_404(db, Process, process_id)
    names = element_names(x.xml)
    if element_id not in names:
        raise ProblemError("invalid", "The element is not part of this diagram")
    notes = dict(x.step_notes or {})
    text = body.text.strip()
    if notes.get(element_id, "") == text:
        return await process_view(db, process_id, p)
    if text:
        notes[element_id] = text
    else:
        notes.pop(element_id, None)
    await common.save_element(
        db,
        "process",
        x,
        ProcessFields,
        {},
        common.expected_version(if_match, body.version),
        p,
        org,
        column_values={"step_notes": notes},
        action="assignment",
        note="Description of step {step} changed",
        vars_={"step": names[element_id]},
    )
    await db.commit()
    db.expire_all()
    return await process_view(db, process_id, p)


async def assign_role(
    db: AsyncSession,
    process_id: str,
    element_id: str,
    body: StepRoleIn,
    if_match: str | None,
    p: Principal,
) -> ProcessOut:
    org = await load_org(db)
    role = org.roles.get(body.role_id)
    if role is None:
        raise ProblemError("invalid", "Unknown role")
    x = await common.get_or_404(db, Process, process_id)
    existing = await proc_repo.find(db, process_id, element_id, body.role_id)
    version = common.expected_version(if_match, body.version)
    if existing:
        if existing.raci == body.raci:
            return await process_view(db, process_id, p)
        await _step_change(
            db,
            process_id,
            version,
            p,
            "RACI of {role} in step {step}: {raci}",
            {
                "role": f"{role.code} {role.title}",
                "step": element_names(x.xml).get(element_id, element_id),
                "raci": body.raci,
            },
        )
        existing.raci = body.raci
    else:
        await _step_change(
            db,
            process_id,
            version,
            p,
            "{role} assigned to step {step}",
            {
                "role": f"{role.code} {role.title}",
                "step": element_names(x.xml).get(element_id, element_id),
            },
        )
        await proc_repo.add(db, process_id, element_id, body.role_id, body.raci)
    await db.commit()
    db.expire_all()
    return await process_view(db, process_id, p)


async def unassign_role(
    db: AsyncSession,
    process_id: str,
    element_id: str,
    role_id: str,
    version: int | None,
    if_match: str | None,
    p: Principal,
) -> ProcessOut:
    org = await load_org(db)
    role = org.roles.get(role_id)
    x = await common.get_or_404(db, Process, process_id)
    if await proc_repo.find(db, process_id, element_id, role_id) is None:
        raise ProblemError("not_found", "Assignment not found")
    await _step_change(
        db,
        process_id,
        common.expected_version(if_match, version),
        p,
        "{role} removed from step {step}",
        {
            "role": f"{role.code} {role.title}" if role else role_id,
            "step": element_names(x.xml).get(element_id, element_id),
        },
    )
    await proc_repo.remove(db, process_id, element_id, role_id)
    await db.commit()
    db.expire_all()
    return await process_view(db, process_id, p)


async def workflow(
    db: AsyncSession, process_id: str, body: WorkflowAction, if_match: str | None, p: Principal
) -> ProcessOut:
    org = await load_org(db)
    x = await common.get_or_404(db, Process, process_id)
    await common.workflow_action(
        db,
        "process",
        x,
        ProcessFields,
        body.action,
        body.comment,
        body.target_status,
        common.expected_version(if_match, body.version),
        p,
        org,
    )
    await db.commit()
    db.expire_all()
    return await process_view(db, process_id, p)


async def history(db: AsyncSession, process_id: str, p: Principal) -> list[Revision]:
    _need(p, "processes:read")
    return await common.revisions(db, "process", process_id, await load_org(db))


async def state(db: AsyncSession, process_id: str, revision_id: int, p: Principal) -> StateView:
    _need(p, "processes:read")
    x = await common.get_or_404(db, Process, process_id)
    return await common.state_after(
        db,
        "process",
        process_id,
        revision_id,
        common.state_of(x, ProcessFields),
        await load_org(db),
    )


# ---- risks, opportunities, controls and KPI of process steps -----------------------------------

LINK_MODELS: dict[
    str, type[WorkInstruction] | type[Risk] | type[Opportunity] | type[Control] | type[Kpi]
] = {
    "instruction": WorkInstruction,
    "risk": Risk,
    "opportunity": Opportunity,
    "control": Control,
    "kpi": Kpi,
}


async def grc_index(db: AsyncSession) -> dict[str, dict[str, tuple[str, str]]]:
    """kind → id → (code, title) of the elements that can be linked to a step."""
    return {
        kind: {e.id: (e.code, e.title) for e in await elements.list_all(db, model)}
        for kind, model in LINK_MODELS.items()
    }


async def mitigation(db: AsyncSession) -> dict[str, list[str]]:
    """control id → risks it mitigates."""
    return {c.id: list(c.mitigates_risk_ids) for c in await elements.list_all(db, Control)}


async def usages(db: AsyncSession, kind: str, target_id: str) -> list[Usage]:
    """The process steps an element is assigned to."""
    out: list[Usage] = []
    names: dict[str, tuple[str, dict[str, str]]] = {}
    for link in await proc_repo.links_to(db, kind, target_id):
        if link.process_id not in names:
            x = await elements.get(db, Process, link.process_id)
            if x is None:
                continue
            names[x.id] = (f"{x.code} {x.title}", element_names(x.xml))
        label, steps = names[link.process_id]
        out.append(
            Usage(
                process_id=link.process_id,
                process_label=label,
                element_id=link.element_id,
                element_name=steps.get(link.element_id, link.element_id),
            )
        )
    return out


async def link_element(
    db: AsyncSession,
    process_id: str,
    element_id: str,
    body: StepLinkIn,
    if_match: str | None,
    p: Principal,
) -> ProcessOut:
    target = await elements.get(db, LINK_MODELS[body.kind], body.target_id)
    if target is None:
        raise ProblemError("invalid", "Unknown element")
    x = await common.get_or_404(db, Process, process_id)
    if await proc_repo.find_link(db, process_id, element_id, body.kind, body.target_id):
        return await process_view(db, process_id, p)
    await _step_change(
        db,
        process_id,
        common.expected_version(if_match, body.version),
        p,
        "{item} assigned to step {step}",
        {
            "item": f"{target.code} {target.title}",
            "step": element_names(x.xml).get(element_id, element_id),
        },
    )
    await proc_repo.add_link(db, process_id, element_id, body.kind, body.target_id)
    await db.commit()
    db.expire_all()
    return await process_view(db, process_id, p)


async def unlink_element(
    db: AsyncSession,
    process_id: str,
    element_id: str,
    kind: str,
    target_id: str,
    version: int | None,
    if_match: str | None,
    p: Principal,
) -> ProcessOut:
    if kind not in LINK_MODELS:
        raise ProblemError("invalid", "Unknown kind")
    x = await common.get_or_404(db, Process, process_id)
    if await proc_repo.find_link(db, process_id, element_id, kind, target_id) is None:
        raise ProblemError("not_found", "Assignment not found")
    target = await elements.get(db, LINK_MODELS[kind], target_id)
    await _step_change(
        db,
        process_id,
        common.expected_version(if_match, version),
        p,
        "{item} removed from step {step}",
        {
            "item": f"{target.code} {target.title}" if target else target_id,
            "step": element_names(x.xml).get(element_id, element_id),
        },
    )
    await proc_repo.remove_link(db, process_id, element_id, kind, target_id)
    await db.commit()
    db.expire_all()
    return await process_view(db, process_id, p)
