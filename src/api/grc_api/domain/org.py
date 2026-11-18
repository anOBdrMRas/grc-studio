"""Organisation rules: who holds a role, who owns an element, segregation of duties."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PersonRef:
    id: str
    position_id: str | None


def role_holders(
    role_id: str, position_roles: dict[str, list[str]], users: list[PersonRef]
) -> list[str]:
    """Persons holding a role through the positions they hold."""
    positions = {p for p, roles in position_roles.items() if role_id in roles}
    return [u.id for u in users if u.position_id in positions]


def position_owners(reports_to: str | None, users: list[PersonRef]) -> list[str]:
    """The supervisor (holder of the disciplinary superior position) owns a position."""
    if not reports_to or reports_to == "n/a":
        return []
    return [u.id for u in users if u.position_id == reports_to]


def sod_conflicts(role_ids: list[str], incompatible: dict[str, list[str]]) -> list[tuple[str, str]]:
    """Pairs of incompatible roles combined in one position."""
    out: list[tuple[str, str]] = []
    for i, a in enumerate(role_ids):
        for b in role_ids[i + 1 :]:
            if b in incompatible.get(a, []) or a in incompatible.get(b, []):
                out.append((a, b))
    return out


@dataclass(frozen=True)
class Tree:
    roots: list[str]
    children: dict[str, list[str]]
    # roots without children and without a reporting line ("n/a"), shown apart
    separate: list[str]


def tree(nodes: list[tuple[str, str | None]]) -> Tree:
    """Hierarchy of positions from (id, parent id); unknown parents and cycles become roots."""
    ids = {n for n, _ in nodes}
    parent = {n: p for n, p in nodes}
    children: dict[str, list[str]] = {}
    for n, p in nodes:
        if p in ids and p != n:
            children.setdefault(p, []).append(n)
    roots = [n for n, p in nodes if p not in ids or p == n]
    reached: set[str] = set()
    stack = list(roots)
    while stack:
        n = stack.pop()
        if n not in reached:
            reached.add(n)
            stack.extend(children.get(n, []))
    for n, _ in nodes:  # members of a cycle: start the cycle at its first member
        if n not in reached:
            roots.append(n)
            stack = [n]
            while stack:
                m = stack.pop()
                if m not in reached:
                    reached.add(m)
                    stack.extend(children.get(m, []))
    separate = (
        [n for n in roots if not children.get(n) and parent[n] == "n/a"] if len(roots) > 1 else []
    )
    return Tree([n for n in roots if n not in separate], children, separate)
