"""Fixed value lists (English values; the interface translates them)."""

from typing import Final

from grc_api.domain import risk

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

# ---- risk register (ISO 37301 4.6 / A.4.6), 4-level scales ----------------------------------
RISK_DEPARTMENTS: Final = [
    "ECC",
    "I&A",
    "Global IT",
    "HR",
    "Finance",
    "Controlling",
    "EHS",
    "Global Sourcing",
    "Sales",
    "Marketing",
    "Product Marketing",
    "Engineering",
    "Facility",
    "Customer Repair & Service",
    "Manufacturing Engineering",
    "Product Qualification",
    "Test System Solutions",
    "Global Order Processing",
    "Project Management (PJM)",
    "Management Board - CTO/COO",
    "Management Board - CEO",
]
RISK_ENTITIES: Final = ["CDE", "CUS", "CTW", "CMY", "CCZ"]
RISK_CATEGORIES: Final = [
    "Quality",
    "Information security",
    "Environmental",
    "Compliance",
    "Financial",
    "Strategic",
    "Operational",
]
CONSEQUENCE_TYPES: Final = [
    "Personal or environmental harm",
    "Economic loss",
    "Reputational harm",
    "Administrative measures",
    "Civil or criminal liability",
]
ASSESSMENT_REASONS: Final = [
    "Periodic (department session)",
    "New or changed activity, product or service",
    "Change of structure or strategy",
    "Significant external change",
    "Change of compliance obligation",
    "Merger or acquisition",
    "Noncompliance",
    "Near-miss",
    "Audit or hotline finding",
    "Other",
]
TREATMENTS: Final = ["Reduce", "Avoid", "Transfer", "Accept"]
TREATMENT_STATUSES: Final = ["Identified", "Assessed", "In treatment", "Accepted", "Closed"]
PROTECTION_GOALS: Final = ["Confidentiality", "Integrity", "Availability"]
LIKELIHOOD_LEVELS: Final = ["Very low", "Low", "Medium", "High"]
LIKELIHOOD_DESCRIPTIONS: Final = [
    "Has not happened yet – not even at comparable companies – but cannot be ruled out.",
    "May occur within 5–10 years.",
    "May occur within 3–5 years.",
    "May occur within 3 years or has already occurred.",
]
IMPACT_LEVELS: Final = ["Insignificant", "Medium", "Significant", "Serious to existential"]
IMPACT_DESCRIPTIONS: Final = {
    "Personal or environmental harm": [
        "No or minor injury or environmental impact without lasting effects.",
        "Injury with lost time or local, reversible environmental impact.",
        "Serious injury or significant environmental damage requiring lengthy remediation.",
        "Permanent harm or death, or widespread irreversible environmental damage.",
    ],
    "Economic loss": ["< 25 TUSD", "25–300 TUSD", "300 TUSD – 3 m USD", "≥ 3 m USD"],
    "Reputational harm": [
        "No incident, or one noticed only internally.",
        "Complaints from individual customers or partners, local media coverage.",
        "Loss of important customers or partners, national media coverage.",
        "Lasting loss of trust in the market, international media coverage.",
    ],
    "Administrative measures": [
        "Notice or inquiry from an authority.",
        "Official requirement or warning.",
        "Fine, inspection or withdrawal of individual permits.",
        "Prohibition of operations, withdrawal of essential permits or exclusion from tenders.",
    ],
    "Civil or criminal liability": [
        "Unfounded or minor claims.",
        "Justified civil claims of limited amount.",
        "Significant damage claims or criminal investigation.",
        "Criminal conviction of officers or employees, existential claims.",
    ],
}
OPPORTUNITY_CATEGORIES: Final = [
    "Customer satisfaction",
    "Efficiency",
    "Innovation",
    "Market",
    "Compliance",
    "Information security",
]
CONTROL_TYPES: Final = ["Preventive", "Detective", "Corrective"]
AUTOMATION: Final = ["Manual", "IT-dependent manual", "Semi-automated", "Automated"]
CONTROL_FREQUENCIES: Final = [
    "Event-driven",
    "Daily",
    "Weekly",
    "Monthly",
    "Quarterly",
    "Semi-annually",
    "Annually",
]
YES_NO: Final = ["Yes", "No"]
IMPLEMENTATION: Final = ["Planned", "Partially implemented", "Implemented", "Not implemented"]
EFFECTIVENESS: Final = ["Not tested", "Effective", "Partially effective", "Not effective"]
TEST_METHODS: Final = ["Inquiry", "Observation", "Inspection", "Re-performance", "Sampling"]
KPI_FREQUENCIES: Final = ["Daily", "Weekly", "Monthly", "Quarterly", "Annually"]
KPI_DIRECTIONS: Final = ["higher", "lower"]
PROGRESS_STATUSES: Final = [
    "Identified",
    "Assessed",
    "In implementation",
    "Realised",
    "Discarded",
]
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
        "risk_departments": list(RISK_DEPARTMENTS),
        "risk_entities": list(RISK_ENTITIES),
        "risk_categories": list(RISK_CATEGORIES),
        "consequence_types": list(CONSEQUENCE_TYPES),
        "assessment_reasons": list(ASSESSMENT_REASONS),
        "treatments": list(TREATMENTS),
        "treatment_statuses": list(TREATMENT_STATUSES),
        "protection_goals": list(PROTECTION_GOALS),
        "likelihood_levels": list(LIKELIHOOD_LEVELS),
        "likelihood_descriptions": list(LIKELIHOOD_DESCRIPTIONS),
        "impact_levels": list(IMPACT_LEVELS),
        "opportunity_categories": list(OPPORTUNITY_CATEGORIES),
        "progress_statuses": list(PROGRESS_STATUSES),
        "control_types": list(CONTROL_TYPES),
        "automation": list(AUTOMATION),
        "control_frequencies": list(CONTROL_FREQUENCIES),
        "yes_no": list(YES_NO),
        "implementation": list(IMPLEMENTATION),
        "effectiveness": list(EFFECTIVENESS),
        "test_methods": list(TEST_METHODS),
        "kpi_frequencies": list(KPI_FREQUENCIES),
        "kpi_directions": list(KPI_DIRECTIONS),
        # level of every cell of the 4×4 matrix, row by row (likelihood 1..4 × impact 1..4)
        "risk_matrix": [
            str(risk.level(risk.score(li, im)))
            for li in range(1, risk.SCALE + 1)
            for im in range(1, risk.SCALE + 1)
        ],
        "statuses": list(STATUSES),
        "system_roles": list(SYSTEM_ROLE_IDS),
    } | {f"impact:{k}": list(v) for k, v in IMPACT_DESCRIPTIONS.items()}
