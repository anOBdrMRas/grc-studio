"""Permissions and the built-in system roles that hold them."""

from typing import Final

PERMISSIONS: Final[dict[str, str]] = {
    "people:read": "See persons by name (for references)",
    "users:read": "Open the user management",
    "users:manage": "Create, edit and delete users and assign system roles",
    "org:read": "Read roles and positions",
    "org:manage": "Create, edit and delete roles and positions, set their owners",
    "processes:read": "Read processes",
    "processes:manage": "Create, edit and delete processes, set their owners",
    "grc:read": "Read risks, opportunities, controls and KPI",
    "grc:record": "Record new risks and opportunities",
    "grc:manage": "Create, edit and delete all GRC elements, set their owners",
    "cockpit:read": "Open the I&A cockpit (quality checks, review queue)",
    "quality:approve": "Give or refuse the I&A quality approval",
    "workflow:set-status": "Set the approval status directly",
    "content:manage": "Maintain custom fields and additional dropdown values",
    "ai:manage": "Configure the AI assistant (API key, model)",
}

SYSTEM_ROLES: Final[dict[str, frozenset[str]]] = {
    "employee": frozenset({"people:read", "org:read", "processes:read", "grc:read", "grc:record"}),
    "ia": frozenset(
        {
            "people:read",
            "org:read",
            "org:manage",
            "processes:read",
            "processes:manage",
            "grc:read",
            "grc:record",
            "grc:manage",
            "quality:approve",
            "cockpit:read",
            "workflow:set-status",
        }
    ),
    "admin": frozenset(
        {
            "people:read",
            "users:read",
            "users:manage",
            "org:read",
            "org:manage",
            "processes:read",
            "processes:manage",
            "grc:read",
            "grc:record",
            "grc:manage",
            "cockpit:read",
            "workflow:set-status",
            "content:manage",
            "ai:manage",
        }
    ),
}


def permissions_of(system_roles: list[str]) -> frozenset[str]:
    out: set[str] = set()
    for r in system_roles:
        out |= SYSTEM_ROLES.get(r, frozenset())
    return frozenset(out)
