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
    "quality:approve": "Give or refuse the I&A quality approval",
    "workflow:set-status": "Set the approval status directly",
}

SYSTEM_ROLES: Final[dict[str, frozenset[str]]] = {
    "employee": frozenset({"people:read", "org:read", "processes:read"}),
    "ia": frozenset(
        {
            "people:read",
            "org:read",
            "org:manage",
            "processes:read",
            "processes:manage",
            "quality:approve",
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
            "workflow:set-status",
        }
    ),
}


def permissions_of(system_roles: list[str]) -> frozenset[str]:
    out: set[str] = set()
    for r in system_roles:
        out |= SYSTEM_ROLES.get(r, frozenset())
    return frozenset(out)
