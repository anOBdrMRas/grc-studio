# Changelog

All notable changes; format after [Keep a Changelog](https://keepachangelog.com/), versions after
[SemVer](https://semver.org/).

## [Unreleased]

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
