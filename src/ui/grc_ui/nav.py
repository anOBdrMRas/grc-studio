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
    NavItem("/processes", N_("Processes"), "processes:read"),
    NavItem("/ia", N_("I&A cockpit"), "quality:approve", ready=False),
    NavItem("/risks", N_("Risks"), "grc:read"),
    NavItem("/opportunities", N_("Opportunities"), "grc:read"),
    NavItem("/controls", N_("Controls (ICS)"), "org:read", ready=False),
    NavItem("/roles", N_("Roles"), "org:read"),
    NavItem("/positions", N_("Positions"), "org:read"),
    NavItem("/delegations", N_("Delegations & powers of attorney"), "org:read", ready=False),
    NavItem("/kpi", N_("KPI"), "org:read", ready=False),
    NavItem("/audits", N_("Audits"), "org:read", ready=False),
    NavItem("/users", N_("User management"), "users:read"),
]


def nav_for(permissions: frozenset[str]) -> list[NavItem]:
    return [n for n in NAV if n.permission in permissions]


def is_active(path: str, href: str) -> bool:
    return path == href if href == "/" else path == href or path.startswith(href + "/")
