# Architecture of GRC Studio

The general rules are in [BLUEPRINT.md](BLUEPRINT.md) and [DESIGN.md](DESIGN.md); this page
describes how GRC Studio fills them in. Deviations: [implementation-notes.md](implementation-notes.md).

## Components

```
browser ──HTTPS──▶ TLS proxy (operator) ──▶ proxy (nginx :8080)
                                              ├─ /api, /health, /docs ─▶ api (FastAPI :8000) ──▶ db (PostgreSQL 16)
                                              └─ everything else ──────▶ ui  (FastAPI + Jinja2 :8001) ──▶ api
```

- **api** (`grc_api`) holds every rule and every data access. Session cookie → principal →
  permission per route → service → repository. It answers JSON and errors as
  `application/problem+json` with stable codes (`errors.py`).
- **ui** (`grc_ui`) renders HTML from API data and decides nothing on its own. It reads the
  session cookie and the CSRF token from the browser and forwards them to the API through the
  generated client (`grc_client`). It relays the API's `Set-Cookie` when signing in.
- **contract** (`src/contracts/openapi.json`) is the snapshot of the API; `grc_client` is
  generated from it (`scripts/generate_client.py`).

## API layers

| Layer | Package | May use |
|---|---|---|
| routers | `grc_api.routers` | services, schemas, auth |
| services | `grc_api.services` | repositories, domain, models, schemas |
| repositories | `grc_api.repositories` | models |
| models | `grc_api.models` | db |
| domain | `grc_api.domain` | nothing but the standard library (and defusedxml) |

Enforced by import-linter (`pyproject.toml`).

## Data model (stage 1)

| Table | Content |
|---|---|
| `users` | people: name, division, department, position, system roles, optional local account |
| `roles` | roles incl. incompatible roles, ISO references, workflow fields, `released` snapshot |
| `positions`, `position_roles` | positions, hierarchy, roles of a position with comment |
| `processes` | process profile, category, owner role, BPMN XML, workflow fields |
| `step_assignments` | process × BPMN element × role with RACI (unique) |
| `risks` | risk register: assessment (likelihood, impact 1–4), treatment actions (JSONB), recorder, workflow fields |
| `opportunities` | opportunities: likelihood × benefit, responsible role, recorder, workflow fields |
| `controls` | internal controls: design, risks addressed, SoA (Annex A), effectiveness (no workflow) |
| `kpis`, `kpi_measurements` | KPI with thresholds; measured values, one per KPI and date |
| `step_links` | process × BPMN element × risk / opportunity / control / KPI (unique) |
| `audit_log` | every change (field diffs), sign-in, diagram and assignment notes |
| `workflow_entries` | workflow steps per element (submitted, approved, rejected, reopened, status) |
| `sessions` | server sessions (token hash, CSRF token, expiry) |

Every element table carries `version`, `created_at` and `updated_at` (mixin `Versioned`); workflow
elements also carry `status`, `doc_version`, `next_review` and `released` (mixin `Approvable`).

## Request flow: saving a role

1. Browser: `POST /roles/RO-006` (HTMX form, `X-CSRF-Token` header).
2. ui: `values_from_form(FORMS["role"], …)` → `api.roles_update("RO-006", {"version": v, "values": …})`.
3. api: `secured("org:read")` → `services/org.update_role` → `common.save_element`:
   rights (owner or manager) → schema validation of the merged values → reopening of a released
   element → `UPDATE … WHERE version = v` (409 if stale) → audit entry with field diffs.
4. ui: renders `entity/_detail.html` from the fresh API data, triggers `refreshList` and a toast.

## Interface

- Jinja2 with `StrictUndefined`, gettext (newstyle), templates under `grc_ui/templates`.
- HTMX 2 for fragments; Alpine (CSP build) for small local state; `static/js/app.js` handles
  `data-action` buttons, toasts and the modal; `static/js/process.js` the BPMN island.
- Tailwind 3 + daisyUI 4, themes `fidonis` / `fidonis-dark`; fonts and libraries are vendored by
  `src/ui/scripts/vendor.mjs` at build time (`npm run build`), nothing is loaded from a CDN.
- Strict CSP (`grc_ui/security.py`): `script-src 'self'`, no inline scripts or handlers.
