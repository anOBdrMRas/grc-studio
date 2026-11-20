"""Navigation model (deviation A1: rendered as the horizontal menu bar)."""

from dataclasses import dataclass

from grc_ui.i18n import N_


@dataclass(frozen=True)
class NavItem:
    href: str
    label: str
    permission: str
    ready: bool = True


NAV: list[NavItem] = [
    NavItem("/", N_("Start page"), "people:read"),
    NavItem("/ia", N_("I&A cockpit"), "cockpit:read"),
    NavItem("/processes", N_("Processes"), "processes:read"),
    NavItem("/instructions", N_("Work instructions"), "processes:read"),
    NavItem("/positions", N_("Positions"), "org:read"),
    NavItem("/roles", N_("Roles"), "org:read"),
    NavItem("/org-chart", N_("Org chart"), "org:read"),
    NavItem("/delegations", N_("Delegations & powers of attorney"), "org:read"),
    NavItem("/risks", N_("Risks"), "grc:read"),
    NavItem("/opportunities", N_("Opportunities"), "grc:read"),
    NavItem("/controls", N_("Controls (ICS)"), "grc:read"),
    NavItem("/kpi", N_("KPI"), "grc:read"),
    NavItem("/audits", N_("Audits"), "grc:read"),
    NavItem("/users", N_("User management"), "users:read"),
    NavItem("/admin", N_("Administration"), "content:manage"),
]


def nav_for(permissions: frozenset[str]) -> list[NavItem]:
    return [n for n in NAV if n.permission in permissions]


def is_active(path: str, href: str) -> bool:
    if href == "/":
        return path == href
    return path == href or path.startswith(href + "/")
