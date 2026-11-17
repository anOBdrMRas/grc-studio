"""Form definitions (sections and fields) of the modules. Labels are English message ids."""

from typing import Any

from grc_ui.i18n import N_

Section = dict[str, Any]

ROLE: list[Section] = [
    {
        "title": N_("Master data"),
        "fields": [
            {"key": "code", "label": N_("ID"), "kind": "readonly"},
            {"key": "title", "label": N_("Title"), "kind": "text"},
            {"key": "description", "label": N_("Description"), "kind": "textarea", "wide": True},
            {
                "key": "role_type",
                "label": N_("Role type"),
                "kind": "select",
                "options": "role_types",
            },
            {
                "key": "org_unit",
                "label": N_("Organisational unit"),
                "kind": "select",
                "options": "org_units",
            },
            {
                "key": "mandatory",
                "label": N_("Mandatory role"),
                "kind": "bool",
                "hint": N_(
                    "required by a standard, law or authority, e.g. CISO, DPO, export control officer"
                ),
            },
            {
                "key": "compliance_relevant",
                "label": N_("Compliance function / sensitive role"),
                "kind": "bool",
            },
            {
                "key": "role_owner_user_id",
                "label": N_("Role owner"),
                "kind": "ref",
                "ref": "people",
                "hint": N_("defines and reviews the role"),
                "owner": True,
            },
        ],
    },
    {
        "title": N_("Responsibilities & competence"),
        "fields": [
            {
                "key": "responsibilities",
                "label": N_("Responsibilities"),
                "kind": "textarea",
                "wide": True,
                "hint": N_("ISO 9001 5.3"),
            },
            {
                "key": "authorities",
                "label": N_("Functional authorities of the role"),
                "kind": "textarea",
                "wide": True,
                "hint": N_(
                    "applies to every holder, e.g. right to information, audit, veto; amounts and powers belong to the position or a transfer"
                ),
            },
            {
                "key": "competencies",
                "label": N_("Required competencies"),
                "kind": "textarea",
                "hint": N_("ISO 9001 7.2"),
            },
            {"key": "trainings", "label": N_("Mandatory training / awareness"), "kind": "textarea"},
        ],
    },
    {
        "title": N_("Segregation of duties"),
        "fields": [
            {
                "key": "incompatible_role_ids",
                "label": N_("Incompatible roles (SoD)"),
                "kind": "refs",
                "ref": "roles",
                "wide": True,
            },
        ],
    },
    {
        "title": N_("Required transfer"),
        "fields": [
            {
                "key": "required_mandate",
                "label": N_("Personal transfer required"),
                "kind": "select",
                "options": "mandate_types",
            },
            {"key": "written_form", "label": N_("Written form required"), "kind": "bool"},
            {
                "key": "authority_notice",
                "label": N_("Notification to authority / register"),
                "kind": "text",
            },
        ],
    },
    {
        "title": N_("Standards reference"),
        "fields": [
            {"key": "iso_refs", "label": N_("Standard references"), "kind": "iso", "wide": True},
        ],
    },
    {
        "title": N_("Validity & review"),
        "fields": [
            {"key": "doc_version", "label": N_("Version"), "kind": "readonly"},
            {"key": "status", "label": N_("Status"), "kind": "status"},
            {"key": "last_review", "label": N_("Last review"), "kind": "date"},
            {"key": "next_review", "label": N_("Next review"), "kind": "date"},
        ],
    },
]

POSITION: list[Section] = [
    {
        "title": N_("Master data"),
        "fields": [
            {"key": "code", "label": N_("ID"), "kind": "readonly"},
            {"key": "title", "label": N_("Title"), "kind": "text"},
            {"key": "description", "label": N_("Description"), "kind": "textarea", "wide": True},
            {
                "key": "org_unit",
                "label": N_("Organisational unit"),
                "kind": "select",
                "options": "org_units",
            },
            {
                "key": "is_manager",
                "label": N_("Management position"),
                "kind": "bool",
                "hint": N_("with line management responsibility"),
            },
            {"key": "headcount", "label": N_("Headcount (planned)"), "kind": "number"},
            {"key": "location", "label": N_("Location"), "kind": "text"},
        ],
    },
    {
        "title": N_("Job description"),
        "fields": [
            {
                "key": "purpose",
                "label": N_("Purpose of the position"),
                "kind": "textarea",
                "wide": True,
            },
            {
                "key": "tasks",
                "label": N_("Main tasks"),
                "kind": "textarea",
                "wide": True,
                "hint": N_("ISO 9001 5.3"),
            },
        ],
    },
    {
        "title": N_("Authorities of the position"),
        "fields": [
            {
                "key": "authorities",
                "label": N_("Authorities of the position"),
                "kind": "textarea",
                "wide": True,
            },
            {
                "key": "signing_authority",
                "label": N_("Target power of attorney of the position"),
                "kind": "select",
                "options": "signing_authorities",
            },
            {"key": "approval_limit", "label": N_("Approval limit (EUR)"), "kind": "number"},
        ],
    },
    {
        "title": N_("Requirements & competence"),
        "fields": [
            {"key": "qualification", "label": N_("Education / qualification"), "kind": "textarea"},
            {"key": "experience", "label": N_("Professional experience"), "kind": "textarea"},
            {
                "key": "competencies",
                "label": N_("Professional & personal competencies"),
                "kind": "textarea",
                "wide": True,
            },
            {
                "key": "trainings",
                "label": N_("Mandatory training / awareness"),
                "kind": "textarea",
                "wide": True,
            },
            {
                "key": "screening_required",
                "label": N_("Background screening required"),
                "kind": "bool",
            },
            {
                "key": "nda_required",
                "label": N_("Confidentiality agreement required"),
                "kind": "bool",
            },
        ],
    },
    {
        "title": N_("Hierarchy & reporting lines"),
        "fields": [
            {
                "key": "reports_to_disciplinary_id",
                "label": N_("Reports disciplinarily to"),
                "kind": "ref",
                "ref": "positions",
                "owner": True,
            },
            {
                "key": "reports_to_functional_id",
                "label": N_("Reports functionally to"),
                "kind": "ref",
                "ref": "positions",
            },
            {
                "key": "deputy_position_id",
                "label": N_("Deputised by position"),
                "kind": "ref",
                "ref": "positions",
            },
            {"key": "deputy_inducted", "label": N_("Deputy inducted"), "kind": "bool"},
        ],
    },
    {
        "title": N_("Assigned roles"),
        "fields": [
            {"key": "roles", "label": N_("Assigned roles"), "kind": "position_roles", "wide": True},
        ],
    },
    {
        "title": N_("Standards reference"),
        "fields": [
            {"key": "iso_refs", "label": N_("Standard references"), "kind": "iso", "wide": True},
        ],
    },
    {
        "title": N_("Validity & review"),
        "fields": [
            {"key": "doc_version", "label": N_("Version"), "kind": "readonly"},
            {"key": "status", "label": N_("Status"), "kind": "status"},
            {"key": "last_review", "label": N_("Last review"), "kind": "date"},
            {"key": "next_review", "label": N_("Next review"), "kind": "date"},
        ],
    },
]

USER: list[Section] = [
    {
        "title": N_("User"),
        "fields": [
            {"key": "code", "label": N_("User ID"), "kind": "readonly"},
            {"key": "last_name", "label": N_("Last name"), "kind": "text"},
            {"key": "first_name", "label": N_("First name"), "kind": "text"},
            {
                "key": "division",
                "label": N_("Area"),
                "kind": "select",
                "options": "divisions",
                "empty": True,
            },
            {
                "key": "department",
                "label": N_("Department"),
                "kind": "select",
                "options": "departments",
                "empty": True,
            },
            {"key": "position_id", "label": N_("Position"), "kind": "ref", "ref": "positions"},
            {"key": "description", "label": N_("Remarks"), "kind": "textarea", "wide": True},
        ],
    },
    {
        "title": N_("System roles (permissions in the tool)"),
        "fields": [
            {
                "key": "system_roles",
                "label": N_("System roles (permissions in the tool)"),
                "kind": "multiselect",
                "options": "system_roles",
                "wide": True,
            },
        ],
    },
]

PROCESS: list[Section] = [
    {
        "title": N_("Process profile (ISO 9001 4.4)"),
        "fields": [
            {"key": "code", "label": N_("ID"), "kind": "readonly"},
            {"key": "title", "label": N_("Title"), "kind": "text"},
            {
                "key": "category",
                "label": N_("Process category"),
                "kind": "select",
                "options": "process_categories",
            },
            {
                "key": "owner_role_id",
                "label": N_("Process owner"),
                "kind": "ref",
                "ref": "roles",
                "owner": True,
            },
            {"key": "area", "label": N_("Process area"), "kind": "text"},
            {"key": "doc_version", "label": N_("Version"), "kind": "readonly"},
            {"key": "status", "label": N_("Status"), "kind": "status"},
            {"key": "next_review", "label": N_("Next review"), "kind": "date"},
            {
                "key": "standards",
                "label": N_("Relevant management systems"),
                "kind": "multiselect",
                "options": "standards",
                "wide": True,
            },
            {
                "key": "description",
                "label": N_("Purpose & scope"),
                "kind": "textarea",
                "wide": True,
            },
            {"key": "inputs", "label": N_("Inputs"), "kind": "textarea", "wide": True},
            {"key": "outputs", "label": N_("Outputs"), "kind": "textarea", "wide": True},
            {"key": "resources", "label": N_("Resources"), "kind": "textarea", "wide": True},
        ],
    },
]

FORMS: dict[str, list[Section]] = {
    "role": ROLE,
    "position": POSITION,
    "user": USER,
    "process": PROCESS,
}
