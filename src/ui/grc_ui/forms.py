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

RISK: list[Section] = [
    {
        "title": N_("1 Identify"),
        "fields": [
            {"key": "code", "label": N_("Risk ID"), "kind": "readonly"},
            {"key": "status", "label": N_("Status"), "kind": "status"},
            {"key": "doc_version", "label": N_("Version"), "kind": "readonly"},
            {
                "key": "department",
                "label": N_("Department / function"),
                "kind": "select",
                "options": "risk_departments",
                "empty": True,
            },
            {
                "key": "category",
                "label": N_("Risk category"),
                "kind": "select",
                "options": "risk_categories",
                "empty": True,
            },
            {
                "key": "activity",
                "label": N_("Activity, process, product or service"),
                "kind": "text",
                "wide": True,
            },
            {
                "key": "process_ids",
                "label": N_("Linked processes"),
                "kind": "refs",
                "ref": "processes",
                "wide": True,
            },
            {
                "key": "compliance_obligation",
                "label": N_("Legal area / obligation"),
                "kind": "text",
                "hint": N_("law, contract, customer requirement, code · ISO 37301 4.5"),
                "wide": True,
            },
            {
                "key": "description",
                "label": N_("Risk description"),
                "kind": "textarea",
                "wide": True,
                "hint": N_("the first sentence is shown in lists"),
            },
            {
                "key": "cause",
                "label": N_("Cause and consequence"),
                "kind": "textarea",
                "wide": True,
            },
            {
                "key": "owner_user_id",
                "label": N_("Risk owner"),
                "kind": "ref",
                "ref": "people",
                "hint": N_("ISO 27001 6.1.2 c) 2)"),
                "owner": True,
            },
            {
                "key": "treatment_status",
                "label": N_("Treatment status"),
                "kind": "select",
                "options": "treatment_statuses",
            },
        ],
    },
    {
        "title": N_("2 Analyse"),
        "fields": [
            {
                "key": "consequence_type",
                "label": N_("Main type of consequence"),
                "kind": "select",
                "options": "consequence_types",
                "empty": True,
            },
            {"key": "scale_guide", "label": N_("Assessment scale"), "kind": "risk_guide"},
            {
                "key": "likelihood",
                "label": N_("Likelihood"),
                "kind": "scale",
                "options": "likelihood_levels",
                "hint": N_("1 = very low … 4 = high"),
            },
            {
                "key": "likelihood_reason",
                "label": N_("Reason for the likelihood"),
                "kind": "textarea",
            },
            {
                "key": "impact",
                "label": N_("Impact"),
                "kind": "scale",
                "options": "impact_levels",
                "hint": N_("1 = insignificant … 4 = serious"),
            },
            {"key": "impact_reason", "label": N_("Reason for the impact"), "kind": "textarea"},
        ],
    },
    {
        "title": N_("3 Evaluate"),
        "fields": [
            {"key": "assessment", "label": N_("Risk score"), "kind": "risk_eval", "wide": True}
        ],
    },
    {
        "title": N_("4 Treat"),
        "fields": [
            {
                "key": "treatment",
                "label": N_("Treatment option"),
                "kind": "select",
                "options": "treatments",
                "empty": True,
                "hint": N_("ISO 27001 6.1.3"),
            },
            {
                "key": "actions",
                "label": N_("Treatment actions"),
                "kind": "risk_actions",
                "wide": True,
                "hint": N_("one responsible person per action"),
            },
        ],
    },
    {
        "title": N_("5 Monitor"),
        "fields": [
            {
                "key": "assessment_reason",
                "label": N_("Reason for the assessment"),
                "kind": "select",
                "options": "assessment_reasons",
                "empty": True,
                "hint": N_("ISO 37301 A.4.6"),
            },
            {"key": "last_assessment", "label": N_("Assessment date"), "kind": "date"},
            {
                "key": "next_review",
                "label": N_("Next review"),
                "kind": "date",
                "hint": N_("regular interval 12 months"),
            },
            {
                "key": "review_note",
                "label": N_("Comment / review note"),
                "kind": "textarea",
                "wide": True,
            },
        ],
    },
    {
        "title": N_("Information security (optional)"),
        "fields": [
            {
                "key": "affected_assets",
                "label": N_("Affected assets"),
                "kind": "text",
                "hint": N_("ISO 27001 A.5.9"),
            },
            {
                "key": "protection_goals",
                "label": N_("Protection goals"),
                "kind": "multiselect",
                "options": "protection_goals",
            },
            {
                "key": "interested_parties",
                "label": N_("Interested parties"),
                "kind": "text",
                "hint": N_("ISO 9001 / 37301 4.2"),
            },
        ],
    },
    {
        "title": N_("Origin"),
        "fields": [
            {
                "key": "entity",
                "label": N_("Entity"),
                "kind": "select",
                "options": "risk_entities",
                "empty": True,
            },
            {
                "key": "source_ref",
                "label": N_("Source"),
                "kind": "text",
                "hint": N_("e.g. workshop minutes, audit report, hotline report"),
            },
        ],
    },
    {
        "title": N_("Standard references"),
        "fields": [{"key": "iso_refs", "label": N_("ISO references"), "kind": "iso", "wide": True}],
    },
]

OPPORTUNITY: list[Section] = [
    {
        "title": N_("Master data"),
        "fields": [
            {"key": "code", "label": N_("ID"), "kind": "readonly"},
            {"key": "status", "label": N_("Status"), "kind": "status"},
            {"key": "doc_version", "label": N_("Version"), "kind": "readonly"},
            {"key": "title", "label": N_("Title"), "kind": "text"},
            {"key": "description", "label": N_("Description"), "kind": "textarea", "wide": True},
            {
                "key": "category",
                "label": N_("Category"),
                "kind": "select",
                "options": "opportunity_categories",
                "empty": True,
            },
            {
                "key": "progress_status",
                "label": N_("Implementation status"),
                "kind": "select",
                "options": "progress_statuses",
            },
            {
                "key": "owner_role_id",
                "label": N_("Responsible"),
                "kind": "ref",
                "ref": "roles",
                "owner": True,
            },
        ],
    },
    {
        "title": N_("Assessment"),
        "fields": [
            {"key": "benefit", "label": N_("Expected benefit"), "kind": "textarea", "wide": True},
            {
                "key": "likelihood",
                "label": N_("Likelihood of realisation"),
                "kind": "scale",
                "max": 5,
                "hint": N_("1 = very low … 5 = very high"),
            },
            {
                "key": "benefit_score",
                "label": N_("Benefit potential"),
                "kind": "scale",
                "max": 5,
                "hint": N_("1 = very low … 5 = very high"),
            },
            {
                "key": "measures",
                "label": N_("Measures to seize it"),
                "kind": "textarea",
                "wide": True,
            },
            {"key": "next_review", "label": N_("Next review"), "kind": "date"},
        ],
    },
    {
        "title": N_("Standard references"),
        "fields": [{"key": "iso_refs", "label": N_("ISO references"), "kind": "iso", "wide": True}],
    },
]

CONTROL: list[Section] = [
    {
        "title": N_("Master data"),
        "fields": [
            {"key": "code", "label": N_("ID"), "kind": "readonly"},
            {"key": "title", "label": N_("Title"), "kind": "text"},
            {"key": "description", "label": N_("Description"), "kind": "textarea", "wide": True},
            {
                "key": "objective",
                "label": N_("Control objective"),
                "kind": "textarea",
                "wide": True,
            },
            {"key": "key_control", "label": N_("Key control"), "kind": "bool"},
        ],
    },
    {
        "title": N_("Control design"),
        "fields": [
            {
                "key": "control_type",
                "label": N_("Control type"),
                "kind": "select",
                "options": "control_types",
                "empty": True,
            },
            {
                "key": "automation",
                "label": N_("Degree of automation"),
                "kind": "select",
                "options": "automation",
                "empty": True,
            },
            {
                "key": "frequency",
                "label": N_("Frequency"),
                "kind": "select",
                "options": "control_frequencies",
                "empty": True,
            },
            {
                "key": "owner_role_id",
                "label": N_("Control owner"),
                "kind": "ref",
                "ref": "roles",
                "owner": True,
            },
            {
                "key": "executor_role_id",
                "label": N_("Performed by"),
                "kind": "ref",
                "ref": "roles",
            },
            {
                "key": "evidence",
                "label": N_("Evidence / documentation"),
                "kind": "text",
                "hint": N_("ISO 9001 7.5"),
            },
            {
                "key": "mitigates_risk_ids",
                "label": N_("Risks addressed"),
                "kind": "refs",
                "ref": "risks",
                "wide": True,
            },
        ],
    },
    {
        "title": N_("Statement of Applicability (ISO 27001)"),
        "fields": [
            {
                "key": "annex_a",
                "label": N_("Annex A controls"),
                "kind": "iso",
                "prefix": "27001:A.",
                "wide": True,
            },
            {
                "key": "soa_applicable",
                "label": N_("Applicable"),
                "kind": "select",
                "options": "yes_no",
                "empty": True,
            },
            {
                "key": "implementation",
                "label": N_("Implementation status"),
                "kind": "select",
                "options": "implementation",
                "empty": True,
            },
            {
                "key": "soa_justification",
                "label": N_("Justification (inclusion / exclusion)"),
                "kind": "textarea",
                "wide": True,
            },
        ],
    },
    {
        "title": N_("Effectiveness test"),
        "fields": [
            {
                "key": "test_method",
                "label": N_("Test method"),
                "kind": "select",
                "options": "test_methods",
                "empty": True,
            },
            {
                "key": "design_effectiveness",
                "label": N_("Design effectiveness"),
                "kind": "select",
                "options": "effectiveness",
            },
            {
                "key": "operating_effectiveness",
                "label": N_("Operating effectiveness"),
                "kind": "select",
                "options": "effectiveness",
            },
            {"key": "last_test", "label": N_("Last test"), "kind": "date"},
            {"key": "next_test", "label": N_("Next test"), "kind": "date"},
            {
                "key": "test_result",
                "label": N_("Test result / findings"),
                "kind": "textarea",
                "wide": True,
            },
        ],
    },
    {
        "title": N_("Standard references"),
        "fields": [
            {
                "key": "iso_refs",
                "label": N_("Further ISO references"),
                "kind": "iso",
                "wide": True,
            }
        ],
    },
]

KPI: list[Section] = [
    {
        "title": N_("Master data"),
        "fields": [
            {"key": "code", "label": N_("ID"), "kind": "readonly"},
            {"key": "title", "label": N_("Title"), "kind": "text"},
            {"key": "description", "label": N_("Description"), "kind": "textarea", "wide": True},
            {
                "key": "objective",
                "label": N_("Related objective"),
                "kind": "text",
                "wide": True,
                "hint": N_("ISO 9001 6.2 / ISO 27001 6.2"),
            },
        ],
    },
    {
        "title": N_("Measurement rule"),
        "fields": [
            {"key": "formula", "label": N_("Formula"), "kind": "text", "wide": True},
            {"key": "unit", "label": N_("Unit"), "kind": "text"},
            {
                "key": "direction",
                "label": N_("Direction"),
                "kind": "select",
                "options": "kpi_directions",
            },
            {"key": "target", "label": N_("Target value"), "kind": "decimal"},
            {"key": "warning", "label": N_("Warning threshold"), "kind": "decimal"},
            {"key": "critical", "label": N_("Critical threshold"), "kind": "decimal"},
            {
                "key": "frequency",
                "label": N_("Measurement frequency"),
                "kind": "select",
                "options": "kpi_frequencies",
                "empty": True,
            },
            {"key": "data_source", "label": N_("Data source"), "kind": "text"},
            {
                "key": "owner_role_id",
                "label": N_("Responsible for measuring"),
                "kind": "ref",
                "ref": "roles",
                "owner": True,
                "hint": N_("ISO 9001 9.1.1"),
            },
            {
                "key": "evaluator_role_id",
                "label": N_("Responsible for evaluation"),
                "kind": "ref",
                "ref": "roles",
            },
        ],
    },
    {
        "title": N_("Standard references"),
        "fields": [{"key": "iso_refs", "label": N_("ISO references"), "kind": "iso", "wide": True}],
    },
]

MANDATE: list[Section] = [
    {
        "title": N_("Master data"),
        "fields": [
            {"key": "code", "label": N_("ID"), "kind": "readonly"},
            {"key": "state", "label": N_("State"), "kind": "mandate_state"},
            {"key": "title", "label": N_("Title"), "kind": "text"},
            {"key": "description", "label": N_("Description"), "kind": "textarea", "wide": True},
            {
                "key": "mandate_type",
                "label": N_("Type of transfer"),
                "kind": "select",
                "options": "mandate_kinds",
                "empty": True,
            },
            {
                "key": "legal_basis",
                "label": N_("Legal basis / requirement"),
                "kind": "text",
                "hint": N_("e.g. Art. 37 GDPR, § 13 (2) ArbSchG, §§ 48 ff. HGB"),
            },
        ],
    },
    {
        "title": N_("Parties & reference"),
        "fields": [
            {
                "key": "recipient_user_id",
                "label": N_("Recipient (person)"),
                "kind": "ref",
                "ref": "people",
            },
            {
                "key": "granted_by_user_id",
                "label": N_("Granted by (person)"),
                "kind": "ref",
                "ref": "people",
                "owner": True,
            },
            {
                "key": "granted_by_body",
                "label": N_("Granted by (body)"),
                "kind": "text",
                "hint": N_("e.g. shareholders' meeting"),
                "owner": True,
            },
            {"key": "role_id", "label": N_("Reference: role"), "kind": "ref", "ref": "roles"},
            {
                "key": "position_id",
                "label": N_("Reference: position"),
                "kind": "ref",
                "ref": "positions",
            },
        ],
    },
    {
        "title": N_("Content & scope"),
        "fields": [
            {
                "key": "scope",
                "label": N_("Duties / tasks transferred"),
                "kind": "textarea",
                "wide": True,
                "hint": N_("clearly delimited"),
            },
            {
                "key": "powers",
                "label": N_("Powers (instruction, decision, information rights)"),
                "kind": "textarea",
                "wide": True,
            },
            {"key": "budget", "label": N_("Resources / budget"), "kind": "text"},
            {
                "key": "amount_limit",
                "label": N_("Amount limit (EUR)"),
                "kind": "number",
                "hint": N_("0 = none"),
            },
            {
                "key": "representation",
                "label": N_("Representation"),
                "kind": "select",
                "options": "representation",
                "empty": True,
            },
            {
                "key": "sub_delegation_allowed",
                "label": N_("Sub-delegation allowed"),
                "kind": "bool",
            },
        ],
    },
    {
        "title": N_("Validity & evidence"),
        "fields": [
            {"key": "valid_from", "label": N_("Valid from"), "kind": "date"},
            {
                "key": "valid_until",
                "label": N_("Valid until"),
                "kind": "date",
                "hint": N_("empty = unlimited"),
            },
            {
                "key": "document",
                "label": N_("Document"),
                "kind": "text",
                "hint": N_("document name, storage location or link"),
            },
            {"key": "accepted_at", "label": N_("Accepted / countersigned on"), "kind": "readonly"},
            {
                "key": "register_entry",
                "label": N_("Register entry / notification to authority"),
                "kind": "text",
                "hint": N_("e.g. commercial register, BAFA, data protection authority"),
            },
            {"key": "registered_at", "label": N_("Registered / notified on"), "kind": "date"},
            {"key": "revoked_at", "label": N_("Revoked on"), "kind": "readonly"},
        ],
    },
    {
        "title": N_("Supervision by the delegating person"),
        "fields": [
            {
                "key": "supervision",
                "label": N_("Supervision measure"),
                "kind": "textarea",
                "wide": True,
                "hint": N_("selection, instruction, supervision (§ 130 OWiG)"),
            },
            {
                "key": "supervision_frequency",
                "label": N_("Frequency"),
                "kind": "select",
                "options": "supervision_frequencies",
                "empty": True,
            },
            {"key": "last_supervision", "label": N_("Last check"), "kind": "date"},
            {"key": "next_supervision", "label": N_("Next check"), "kind": "date"},
        ],
    },
]

FORMS: dict[str, list[Section]] = {
    "role": ROLE,
    "position": POSITION,
    "user": USER,
    "process": PROCESS,
    "risk": RISK,
    "opportunity": OPPORTUNITY,
    "control": CONTROL,
    "kpi": KPI,
    "mandate": MANDATE,
}
