"""Fixed value lists (English values; the interface translates them)."""

from typing import Final

ROLE_TYPES: Final = ["Leadership role", "Functional role", "Committee", "Appointed officer"]
ORG_UNITS: Final = [
    "Generic",
    "Technology",
    "Operation",
    "Marketing",
    "Sales",
    "Finance and Admin",
    "Business Enablement",
    "Other",
]
MANDATE_TYPES: Final = [
    "None",
    "Appointment / designation",
    "Delegation of duties",
    "Prokura (general commercial power)",
    "Commercial power of attorney",
    "Bank / payment authority",
    "Internal approval authority",
]
SIGNING_AUTHORITIES: Final = [
    "None",
    "Commercial power of attorney",
    "Prokura (general commercial power)",
    "Statutory representation (officer)",
]
PROCESS_CATEGORIES: Final = ["Management process", "Core process", "Support process"]
STANDARDS: Final = ["ISO 9001", "ISO 14001", "ISO 27001", "ISO 37301"]
DIVISIONS: Final = [
    "Management",
    "Business Enablement (BE)",
    "Marketing and Communication",
    "Sales",
    "Operations",
    "Finance & Admin",
]
DEPARTMENTS: Final = [
    "Global IT",
    "I&A",
    "Purchasing",
    "Finance",
    "Controlling",
    "Logistics",
    "Quality management",
    "Legal & Compliance",
    "Export Control & Customs",
    "Sales",
    "Internal audit",
]
RACI: Final = ["R", "A", "C", "I"]
STATUSES: Final = ["draft", "review", "released", "archived"]
SYSTEM_ROLE_IDS: Final = ["employee", "ia", "admin"]


def all_catalogs() -> dict[str, list[str]]:
    return {
        "role_types": list(ROLE_TYPES),
        "org_units": list(ORG_UNITS),
        "mandate_types": list(MANDATE_TYPES),
        "signing_authorities": list(SIGNING_AUTHORITIES),
        "process_categories": list(PROCESS_CATEGORIES),
        "standards": list(STANDARDS),
        "divisions": list(DIVISIONS),
        "departments": list(DEPARTMENTS),
        "raci": list(RACI),
        "statuses": list(STATUSES),
        "system_roles": list(SYSTEM_ROLE_IDS),
    }
