# Changelog

All notable changes; format after [Keep a Changelog](https://keepachangelog.com/), versions after
[SemVer](https://semver.org/).

## [Unreleased]

### Changed
- The org chart has its own entry in the menu bar (after Positions).

### Changed (I&A cockpit like the prototype)
- Figures per module on top (processes with their activities), quality overview as cards with
  status bars (processes, roles, positions), treatment / progress / effectiveness bars (risks,
  opportunities, controls) and the quality grade.
- "Waiting for the I&A approval" with owners, the comment of the business approval, waiting days
  and approve / reject right in the cockpit (a comment is required to reject).
- New: delegations in approval, drafts in progress with the owner (rejected ones first with the
  reason), recently released.
- Quality checks as compact tiles by area; a click shows the elements concerned.
- New GRC situation: risk matrix, risks by department, ICS operating effectiveness, role
  coverage of the process steps, KPI traffic lights, open audit findings by type.
- API: the cockpit carries owners, comment and version per queue item, `in_work`,
  `recently_released` and `situation`; the KPI list carries the target.

### Added (stage 4a)
- Org chart of the positions: disciplinary and functional hierarchy (cycles and unknown
  superiors become roots, positions without reporting line shown apart), positions by unit,
  holders, roles (can be hidden) and a segregation-of-duties hint; role matrix position × role
  with comments as tooltip. Reached from Positions and Roles (`GET /api/v1/org-chart`).

### Added (stage 4b)
- Call activities link to the process they call: chosen in the step panel, with a jump to the
  called process; the called process lists "Called by", the calling one "Calls"; changes are
  versioned and recorded like step assignments (migration 0007, column `call_links`).
- Diagram import from a `.bpmn` file (replaces the diagram after the BPMN check) and export as
  `.bpmn` and `.svg` (the diagram as shown). Collapsed sub-processes open with drill-down in the
  editor.

### Fixed
- The history note "Created from a draft" (process draft) is translated.

### Added (stage 3d-2)
- "Suggest with AI" on roles, positions, risks, controls and delegations: the AI proposes the
  text fields; the person edits and chooses per field what is applied. Applying is a normal
  update (rights, version check, history); the suggestion itself saves nothing.
- "Draft a process": a description becomes steps, decisions and role assignments (with AI, or
  without AI one line per step, "?" for a decision, "(role)" for the role). The editable preview
  creates a draft process with a generated BPMN diagram and the roles of its steps
  (`POST /api/v1/processes/from-draft`).

### Added (stage 3d)
- AI assistant ("Where do I find …?") on the start page and as a dialog from the header. It
  answers with links to processes, process steps, roles, positions, delegations, risks,
  opportunities, controls, KPI and audits – only elements the asking person may read; links the
  AI invents are turned into plain text. Without an API key, or when the AI service fails, the
  assistant answers with a catalogue search.
- Administration → AI assistant (permission `ai:manage`): switch on/off, interface
  (OpenAI-compatible, e.g. the internal con-AI, or Anthropic-compatible for Claude directly or
  through a gateway), address, model, API key (encrypted with `SETTINGS_SECRET`, never shown
  again; only its last four characters), connection test. Changes go into the history without
  the key.
- Claude directly is called through the Anthropic SDK with prompt caching of the catalogue and
  the server-side fallback on refusals (Opus/Sonnet). New setting `SETTINGS_SECRET`.

### Added (stage 3c)
- Content administration (menu "Administration", permission `content:manage`, administrators
  only): custom fields per module (text, long text, number, date, yes/no, dropdown, multiple
  choice, person) placed in a section of the form, and additional values for the standard
  dropdowns. They apply at once in the forms, the detail view, the history and the Excel
  export and import.
- The API checks custom values against type and value list and records them in the history
  field by field. A custom field is never deleted, only hidden (its values are kept); its type
  cannot change. New table `settings`, column `custom` on every element (migration 0006).

### Added (stage 3b)
- Excel export per module and for all modules (with KPI values, audit findings and process
  steps as additional sheets); columns in the current language.
- Excel import per module with preview (new / changed / unchanged / errors per row, unknown
  columns reported). Headers in German or English, selection values in either language,
  elements by ID, persons by name or user ID. Saving goes through the API, so rights, version
  checks, validation and history apply as for an edit in the browser. Uploads are limited to
  5 MB and parsed with defusedxml.

### Added (stage 3a)
- Audits with scope, criteria, participants, dates, result and certificate validity; findings
  with root cause, corrective action, due date and effectiveness check. The responsible person
  documents cause, action and progress; checking and closing stays with the auditors.
- Auditor independence check (ISO 19011).
- I&A cockpit: review queue, workflow status and quality grade per module, 33 quality checks
  (processes, roles, positions, risks, opportunities, controls, reviews, audits and
  certificates, delegations, users) linking straight to the element or process step.
- Permission `cockpit:read` (I&A team, administration).

### Fixed (stage 3a)
- A toast and a further HTMX event in one response overwrote each other (e.g. the list did
  not refresh after saving); both now travel in one HX-Trigger header.
- Unexpected API errors are logged with their traceback and answered as problem+json
  (`internal`) without internal details.

### Added (stage 2c)
- Delegations & powers of attorney (appointments, delegation of duties, Prokura, commercial and
  payment authorities, internal approval authority, deputy) with their own approval: granted by
  the grantor, accepted by the recipient, returned or revoked; effective state (draft, not yet
  valid, acceptance missing, effective, expired, revoked).
- Legal-certainty checks: roles needing a formal transfer, written form and notification to
  authorities, leavers, expiry, overdue supervision, sole payment authority, role no longer held,
  powers and amounts above the target of the position, target powers of positions not granted.
  Shown on roles, positions, persons, delegations and the start page.
- Start page: everything in my responsibility (all modules), my delegations, and "for me to do".

### Added (stage 2b)
- Controls (ICS): control design, risks addressed, Statement of Applicability with the
  ISO 27001 Annex A picker, design and operating effectiveness.
- KPI: measurement rule, thresholds, series of measured values (one per date) with a
  server-rendered trend chart and traffic light; owners, the evaluating role and managers record.
- Risks, opportunities, controls and KPI assigned to process steps, with badges per kind in the
  diagram and the ICS check (risk without a mitigating control in the step, with suggestions).
- "Used in process steps" on every element, linking straight into the step (`?step=`).

### Fixed (stage 2b)
- The translation extractor missed ISO clause titles that the formatter wraps across lines.

### Added (stage 2a)
- Risk register: 4×4 matrix (medium from 4, higher risk above 8) with filter, assessment scale
  per type of consequence, treatment actions with responsible persons, entity, linked processes.
- Opportunities with likelihood × benefit potential, owned by the holders of the responsible role.
- Everybody records risks and opportunities; the recorder edits the own draft, chooses the owner
  and deletes a draft that was never submitted. Approval workflow as for roles and processes.
- Permissions `grc:read`, `grc:record`, `grc:manage`; demo risks and opportunities.

## [0.1.0] – stage 1

### Added
- Workspace after the blueprint: API (`grc_api`), interface (`grc_ui`), contract and generated
  client (`grc_client`), PostgreSQL with Alembic migrations, Docker images and Compose stack, CI.
- Sign-in by demo person choice (switchable) or user name and password; server sessions with CSRF.
- Roles, positions and users with split list/detail view, read view and edit mode.
- Approval workflow (business approval → I&A review → released) with four-eyes principle,
  released snapshot and change history with "view this state".
- Process landscape, process profile, BPMN editor (bpmn-js) with versioned saving, role
  assignment per step with RACI and badges.
- German and English interface (gettext), Fidonis light and dark theme, strict CSP.
- Pseudonymised demo data from the prototype.
