"""A BPMN diagram with automatic layout from a simple list of steps (process draft).

Steps run left to right; a decision is an exclusive gateway that continues on "yes" and ends in
its own end event on "no". Without AI the steps come from text: one line per step, a line ending
in "?" is a decision, "(role)" at the end names the role.
"""

import re
from dataclasses import dataclass
from xml.sax.saxutils import quoteattr

STEP_TYPES = ("task", "system", "manual", "decision")
TASK_TYPES = {"task": "userTask", "system": "serviceTask", "manual": "manualTask"}
MAX_STEPS = 30

HEADER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
    'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
    'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
    'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
    'id="Definitions_1" targetNamespace="http://grc.example/bpmn">'
)


@dataclass
class Step:
    name: str
    type: str = "task"  # task, system, manual, decision
    role: str = ""  # role name or id as written (matched to a role later)
    raci: str = "R"
    no: str = ""  # decision only: end event on "no"


@dataclass
class _Node:
    id: str
    type: str
    name: str
    x: int
    y: int


@dataclass
class _Flow:
    id: str
    source: str
    target: str
    points: list[tuple[int, int]]
    name: str = ""


def _size(type_: str) -> tuple[int, int]:
    if type_.endswith("Event"):
        return 36, 36
    if type_.endswith("Gateway"):
        return 50, 50
    return 100, 80


def generate(
    title: str, steps: list[Step], prefix: str, start: str = "Start", end: str = "Ende"
) -> tuple[str, list[str]]:
    """BPMN XML and the element id of every step (same order)."""
    nodes: list[_Node] = [_Node(f"{prefix}_Start", "startEvent", start or "Start", 152, 182)]
    flows: list[_Flow] = []
    ids: list[str] = []
    prev_id, prev_right, x = nodes[0].id, 188, 240

    def link(source: str, target: str, x1: int, x2: int, name: str = "") -> None:
        flows.append(
            _Flow(f"{prefix}_F{len(flows) + 1}", source, target, [(x1, 200), (x2, 200)], name)
        )

    for i, s in enumerate(steps[:MAX_STEPS], start=1):
        after_gateway = "ja" if "_G" in prev_id else ""
        if s.type == "decision":
            id_ = f"{prefix}_G{i}"
            nodes.append(_Node(id_, "exclusiveGateway", s.name, x, 175))
            link(prev_id, id_, prev_right, x, after_gateway)
            end_id = f"{id_}_End"
            nodes.append(_Node(end_id, "endEvent", s.no or "Abbruch", x + 7, 312))
            flows.append(
                _Flow(
                    f"{prefix}_F{len(flows) + 1}",
                    id_,
                    end_id,
                    [(x + 25, 225), (x + 25, 312)],
                    "nein",
                )
            )
            prev_id, prev_right, x = id_, x + 50, x + 100
        else:
            id_ = f"{prefix}_T{i}"
            nodes.append(_Node(id_, TASK_TYPES.get(s.type, "userTask"), s.name, x, 160))
            link(prev_id, id_, prev_right, x, after_gateway)
            prev_id, prev_right, x = id_, x + 100, x + 150
        ids.append(id_)
    end_id = f"{prefix}_End"
    nodes.append(_Node(end_id, "endEvent", end or "Ende", x + 2, 182))
    link(prev_id, end_id, prev_right, x + 2, "ja" if "_G" in prev_id else "")

    pid = f"Process_{prefix}"
    lines = [HEADER, f'  <bpmn:process id="{pid}" name={quoteattr(title)} isExecutable="false">']
    for n in nodes:
        lines.append(f"    <bpmn:{n.type} id={quoteattr(n.id)} name={quoteattr(n.name)}>")
        lines += [f"      <bpmn:incoming>{f.id}</bpmn:incoming>" for f in flows if f.target == n.id]
        lines += [f"      <bpmn:outgoing>{f.id}</bpmn:outgoing>" for f in flows if f.source == n.id]
        lines.append(f"    </bpmn:{n.type}>")
    for f in flows:
        name = f" name={quoteattr(f.name)}" if f.name else ""
        lines.append(
            f'    <bpmn:sequenceFlow id="{f.id}"{name} sourceRef="{f.source}" '
            f'targetRef="{f.target}" />'
        )
    lines += [
        "  </bpmn:process>",
        '  <bpmndi:BPMNDiagram id="BPMNDiagram_1">',
        f'    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="{pid}">',
    ]
    for n in nodes:
        w, h = _size(n.type)
        lines += [
            f'      <bpmndi:BPMNShape id="{n.id}_di" bpmnElement="{n.id}">',
            f'        <dc:Bounds x="{n.x}" y="{n.y}" width="{w}" height="{h}" />',
            "      </bpmndi:BPMNShape>",
        ]
    for f in flows:
        lines.append(f'      <bpmndi:BPMNEdge id="{f.id}_di" bpmnElement="{f.id}">')
        lines += [f'        <di:waypoint x="{px}" y="{py}" />' for px, py in f.points]
        lines.append("      </bpmndi:BPMNEdge>")
    lines += ["    </bpmndi:BPMNPlane>", "  </bpmndi:BPMNDiagram>", "</bpmn:definitions>"]
    return "\n".join(lines), ids


_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")
_ROLE = re.compile(r"^(.*?)\s*\(([^)]+)\)\s*(\??)$")


def steps_from_text(text: str) -> list[Step]:
    """One step per line (or ";"); "?" at the end makes a decision; "(role)" names the role."""
    out: list[Step] = []
    for raw in re.split(r"\n|;", text):
        line = _BULLET.sub("", raw).strip()
        if not line:
            continue
        m = _ROLE.match(line)
        name = (m.group(1) + m.group(3) if m else line).strip()[:120]
        role = m.group(2).strip() if m else ""
        out.append(Step(name, "decision" if name.endswith("?") else "task", role))
    return out[:MAX_STEPS]


def match_role(name: str, roles: dict[str, str]) -> str:
    """Role id for a name or id as written (roles: id → title); "" when none fits."""
    n = name.strip().casefold()
    if not n:
        return ""
    for rid, title in roles.items():
        if n in (rid.casefold(), title.casefold()):
            return rid
    for rid, title in roles.items():
        t = title.casefold()
        if n in t or t in n:
            return rid
    return ""
