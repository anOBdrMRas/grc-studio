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
