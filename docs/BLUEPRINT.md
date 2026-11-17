# Blueprint — the application architecture

This document describes the architecture of the Fidonis web applications: two services — an HTTP
API and a web interface — plus a versioned contract between them, the layers inside each, the
security model around them, and the repository and process conventions that carry them. It is
derived from this repository and is **binding for new projects**: a reader — human or AI agent —
who scaffolds a new project from this document alone must arrive at the same shape, without ever
opening this codebase.

Three documents, three levels:

| Document | Scope |
|---|---|
| `BLUEPRINT.md` (this file) | The architecture, reusable for every new project |
| [`DESIGN.md`](DESIGN.md) | The layout of the web interface (theming, templates, assets, i18n), reusable |
| [`docs/architecture.md`](docs/architecture.md) | This project's concrete instance of the blueprint |

---

## The contract

These rules hold everywhere. A project that breaks one of them is not this architecture.

1. **One enforcement point.** The API holds all rules and all data access and is the only component
   that decides what a user may do. Every route declares the permission it needs (or is on the
   public list); a test fails when a route has neither.
2. **The interface is a client.** It calls the API over HTTP with the signed-in user's own session
   cookie and CSRF token, has no database access and never recomputes a figure the API returns.
   Neither the interface package nor the generated client imports the API package — an
   import-linter contract fails the build if they do.
3. **The contract is versioned.** `openapi.json` lives in the repository as a checked snapshot; a
   typed Python client is generated from it. Every operation has a stable `operationId`; CI fails
   when snapshot or client drift from the code. A later consumer — an MCP server, a mobile app —
   is a third pure client of the same contract, never a second implementation of the rules.
4. **Layers point downwards.** `routers → services → domain`; database access only in
   `repositories`; core code never names a concrete integration (provider). Enforced by
   import-linter, not by convention.
5. **Sessions are server-side and shared.** A session is a row the API owns, carried by an
   `HttpOnly`, `SameSite=Lax` cookie (`Secure` behind https) with an absolute lifetime; every
   unsafe request carries a CSRF token (`X-CSRF-Token` for the interface, a form field for plain
   HTML).
6. **OpenID Connect belongs to the API.** Authorisation code with PKCE, state/nonce/verifier in a
   table bound to the browser by a cookie, only relative `return_to` addresses. The interface never
   sees an OIDC token; it forwards the session cookie.
7. **Errors are documents.** `application/problem+json` (RFC 9457) with a stable `code`; the
   interface maps codes to translated messages, fragments get toasts, full pages get an error page.
8. **Optimistic concurrency everywhere.** Every mutable resource has a `version`; a change is one
   `UPDATE … WHERE version = :v`. A stale version is `412` through `If-Match` (`428` when the header
   is missing) or `409` through the body. Requests can ask `?dryRun=true`: the real service path
   inside a transaction, rolled back.
9. **PostgreSQL, behind SQLAlchemy 2 (async, psycopg 3), relationships `lazy="raise"`.**
   Migrations are hand-written Alembic; a test applies all of them to an empty database and fails
   when the result differs from the models. Built-in roles, types and settings are reconciled at
   start, never by migrations.
10. **Configuration is environment variables**, each documented with a comment in `.env.example`
    holding only `CHANGE_ME` placeholders; `scripts/init_env.py` writes a local `.env` with
    generated secrets. `.env` is never committed. Secrets an integration stores are encrypted with
    `APP_ENCRYPTION_KEY`.
11. **Every text is translated.** The message id is the English text; each language is a `.po`
    catalogue; a test fails when a text or an error code has no translation.
12. **The interface ships a strict CSP.** Scripts, styles, fonts, images and connections only from
    its own origin; no inline script, no `eval`, no CDN. The layout rules are [`DESIGN.md`](DESIGN.md).
13. **Nothing is pushed unchecked.** The local commands are the CI commands: yamllint, ruff,
    `ruff format --check`, mypy (strict), lint-imports, the client-generation check, the i18n
    check, the wording check, pytest.
14. **A behaviour change comes with a test at the level it lives; a bug fix starts with the failing
    test.**

---

## The components

```
  browser ──► reverse proxy (yours; one address)
                ├── /api/…, /openapi.json, /health/… ──► api  (FastAPI, /api/v1)  ──► PostgreSQL
                └── everything else ──────────────────► ui   (FastAPI, Jinja2, HTMX)
                                                          │
                                                          └── calls /api/v1 with the user's own
                                                              session cookie and CSRF token
```

| Component | Package | Responsibility |
|---|---|---|
| API | `src/api/<thing>_api` | All rules and all data access; the only place deciding what a user may do |
| Web interface | `src/ui/<thing>_ui` | Renders pages and fragments from API data; no rule, no recompute |
| Contract | `src/contracts` | `openapi.json` (drift-checked) and `<thing>_client`, the typed client from it |

The proxy routes `/api/`, `/openapi.json` and `/health/` to the API and everything else to the
interface. One public address is what makes single sign-on, API tokens and the published contract
work; set `PUBLIC_BASE_URL` to it (an `https://` address switches cookies to `Secure` and adds
HSTS). The proxy and the identity provider are the operator's; `docker/nginx.conf` shows the
routing, and a development Compose file can add a throw-away nginx and Keycloak.

Two services, two images, one worker each. The API applies migrations at start, then reconciles
built-ins, then serves. The interface image builds its assets with Node and contains no Node at
run time.

---

## The workspace

The repository root is a uv workspace; `uv.lock` at the root is the one lock file; Python 3.12 is
the floor.

```
src/api/         <thing>_api    – HTTP API: routers, services, domain, repositories, models,
                                  schemas, auth, providers, sync, migrations (Alembic), cli
src/ui/          <thing>_ui     – the interface: routes, templates, static files, locale
src/contracts/  openapi.json, <thing>_client (generated)
tests/           unit, api (against a real PostgreSQL), ui (interface in front of the real API),
                 e2e (browser, against a running stack)
docker/          api.Dockerfile, ui.Dockerfile, nginx.conf, compose files, dev identity provider
docs/            architecture.md, providers.md, implementation-notes.md, …
scripts/         init_env.py, generate_client.py, i18n.py, check_wording.py
```

The root `pyproject.toml` declares the members and the workspace sources; the dev dependency group
contains the three packages plus the tooling. The specification with requirement IDs
(`FR-…`, `NFR-…`) lives at the root; every deviation and every "not done" is written down in
`docs/implementation-notes.md` — a new project starts both documents on day one.

Naming, generalised:

| This repo | A new project |
|---|---|
| `planner-api` (`planner_api`) | `<thing>-api` (`<thing>_api`) |
| `planner-ui` (`planner_ui`) | `<thing>-ui` (`<thing>_ui`) |
| `planner-client` (`planner_client`) | `<thing>-client` (`<thing>_client`) |
| entry-point group `resource_planner.providers` | `<thing>.providers` |
| `ghcr.io/fidonis/resource-planner-api` / `-ui` | `ghcr.io/<org>/<thing>-api` / `-ui` |
| themes `fidonis-light` / `fidonis-dark`, brand layer | keep, verbatim (see [`DESIGN.md`](DESIGN.md)) |
| localStorage keys `rp-theme`, `rp-sidebar` | `<xx>-theme`, `<xx>-sidebar` (short, project-unique) |

---

## The API and its layers

```
routers  →  services  →  domain
                │
                └──►  repositories  →  models (SQLAlchemy)
```

**Placement rules — where new code goes:**

- **routers** are thin HTTP adapters: parse the request, call one service, shape the response.
  Each route declares its permission; the permission also lives on the contract (`x-permission`),
  so the client and the contract documentation agree with the code.
- **services** are the use cases. They receive the authenticated principal and check its
  permissions themselves — so the CLI (`seed-demo`, bootstrap) and background jobs go through the
  same code as HTTP does. A service that needs another service's data calls it, not its
  repository.
- **domain** is pure: the rules as functions on value objects, `Decimal` for amounts, no I/O.
  If a rule needs a database or a clock, it is not domain.
- **repositories** are the only code that talks to the database. The big read models (board,
  overview, availability here) are a few SQLAlchemy Core queries plus the maths in Python, so a
  heavy page stays well below a second.
- **schemas** (Pydantic) frame the wire: request and response models; the OpenAPI snapshot is
  generated from them.
- **auth** holds passwords (argon2id, lock-out, rate limit), sessions, OIDC, tokens, the
  principal and the permission registry.
- **providers** and **sync** sit beside the services (below); core code finds them through entry
  points only.

**Long-running work lives in the API, never in the interface.** Here that work is the sync engine
and the scheduler; a project with hours-long operations gives them the same treatment: a job in
the API, progress through the contract, the interface only requests and renders.

**Integrations (when the product needs them):**

- A **provider** implements one protocol (task source, directory, absence source — whatever the
  domain calls for), is found through the entry-point group, and describes its settings with a
  Pydantic model. The interface draws the settings form from that schema, so a new provider needs
  no interface code. Two schema markers add behaviour: `x-showWhen` (a setting appears only while
  another has a value) and `x-remoteOptions` (choices loaded from the source, also for an unsaved
  form).
- The **sync engine** reads a source, hands records to an applier, writes a run with counts and a
  log, takes an advisory lock so one integration runs once at a time, closes what disappeared only
  after a complete read, supports the dry run, and acts as the system principal `sync:<name>` in
  the audit log. The scheduler (APScheduler, in the API process) starts runs by cron expressions.
- The **ingest API** (`POST /ingest/…`) is the push alternative for programs with an API token;
  records go through the same applier.

**An audit log records every change** (who, what, target, result, parameters) — a table here, and
never a secret or a password in its parameters.

**The API is prepared for a third consumer**: `openapi.json` is published at one address, every
operation has a stable id and a declared permission, and nothing about the interface is baked into
a route. A later MCP server becomes another pure client without touching the API.

---

## The contract member

`src/contracts` holds two things, both generated but both committed:

- `openapi.json` — the snapshot of the API. A change to an endpoint, a model or a description
  refreshes it; the API version is part of the contract.
- `<thing>_client` — the typed Python client generated from it by
  `scripts/generate_client.py` (run with `--check` in CI to fail on drift).

The interface, the tests and any later consumer use only the client to talk to the API. Regenerate
on every endpoint change in the same commit; never edit the client by hand.

---

## The interface member

The interface is a server-rendered Jinja2 application with HTMX for partial updates (the layout
itself — template chain, theming, asset pipeline, page recipes — is [`DESIGN.md`](DESIGN.md) and
travels to a new project verbatim per its porting checklist). What the architecture adds:

- It calls the API through the generated client, with the signed-in user's session cookie and CSRF
  token. A `401` from the API becomes a redirect to the sign-in page (an `HX-Redirect` for a
  fragment request); `409`, `412` and `422` answers are swapped in as content, so conflicts and
  field errors render as toasts or next to the field.
- A change on a page is a request to the interface, which calls the API and answers with the page
  drawn again from the API's numbers. The URL always matches the view (`hx-push-url`), and every
  page works without JavaScript.
- Translations: gettext catalogues under `src/ui/<thing>_ui/locale/<code>/LC_MESSAGES/`,
  read at start; the account's language, else the browser's; the language is a setting of the
  account, not of the browser.
- The browser files are vendored at build time from npm — never a CDN, no Node at run time — and
  the content security policy admits only the interface's own origin.

---

## Sign-in, sessions and permissions

Three ways in, one session out:

- **Local accounts**: argon2id passwords, lock after repeated failures, rate limit on the sign-in,
  a forced password change for the first administrator (`BOOTSTRAP_ADMIN_USER` /
  `BOOTSTRAP_ADMIN_PASSWORD`).
- **OIDC** (authorisation code with PKCE): handled by the API, which then sets the same session
  cookie. Roles from the identity provider are stored at sign-in and resolved through the role
  mapping on every request.
- **Credentials for programs**: API tokens (`<prefix>_…`, stored hashed) and bearer tokens of the
  identity provider.

Sessions: a row in the database, an absolute lifetime (`SESSION_TTL_HOURS`), the cookie of
invariant 5, and a CSRF token that must come back on every unsafe request.

Authorisation: **roles hold permissions** (a route lists its permission; `GET /roles/permissions`
lists them all); a role can be limited to teams; a principal's rights are "all" or a set of team
ids; an operation that moves data between teams checks both. The JSON API is restricted exactly
like the pages, because both end in the same service call behind the same declared permission.

---

## Testing

| Suite | Level | Mechanism |
|---|---|---|
| `tests/unit` | domain, services, providers | pure code, fakes for the edges, `respx` for provider HTTP |
| `tests/api` | routers, services, repositories, migrations | a **real PostgreSQL** (testcontainers) |
| `tests/ui` | routes, templates, fragments | the interface in front of the real API |
| `tests/e2e` | the running stack | a browser (Playwright) against the Compose services |

`TEST_DATABASE_URL` points the API tests at an existing database, which they empty. Other mechanics
that matter: one event loop for the whole run so an engine and a pool can be shared
(`asyncio_default_test_loop_scope = "session"`); markers for slow tests and for browser tests that
provoke a 4xx on purpose; a migration-against-models test; a public-routes test; contract-drift
and translation checks as scripts. Bug fix → failing test first (invariant 14).

---

## Engineering conventions

**Root files every project carries:** `AGENTS.md` (project context for humans and agents),
`README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `TRADEMARK.md`, `LICENSE`, `NOTICE`,
`CHANGELOG.md`, `THIRD_PARTY_LICENSES.md`, `CODEOWNERS`, `.env.example`, `docker-compose.yml`,
the specification, `ruff.toml`, `.yamllint`, `.editorconfig` (LF line endings via
`.gitattributes`), `.python-version`.

**Style:** ruff with E, F, I, B, UP, N, RET, SIM, ASYNC at line length 100 plus `ruff format`;
mypy strict with the pydantic plugin; yamllint with the project config; import-linter with three
contracts — the interface and the client never import the API; the API layers point downwards;
core code never references a concrete provider.

**Branches:** `main` is the integration branch (PRs only, never force-push, never delete);
`releases/<x.y.z>` milestone branches; `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `ci/`,
`chore/` for work. PR titles are Conventional Commits (`<type>[(<scope>)][!]: <subject>`,
lowercase imperative, no trailing period); CI enforces the format. Every PR is **squash-merged**
(the title becomes the commit message); the one merge commit is the release cut into `main`.

**Releases:** in a PR into the milestone branch, bump the version by hand — the root
`pyproject.toml`, the members' `pyproject.toml` files, the API package version, the UI
`package.json` — refresh the OpenAPI snapshot and the client (the API version is part of the
contract), write the `CHANGELOG.md` entry. Merge `releases/x.y.z` into `main` with a merge commit
(the PR body lists every issue as `Closes #N`). Publish `vX.Y.Z` on `main`; publishing builds,
pushes and signs the images on `ghcr.io`.

**CI** (same commands run locally first — `uv sync`, then the checks of invariant 13):

- **`ci.yml`** — push to `main`, every PR: yamllint, ruff, mypy, contracts and wording, pytest,
  the Compose stack starts and answers, the PR title format.
- **`license-check.yml`** — push to `main`, PRs into `main`: rejects copyleft dependencies,
  refreshes `THIRD_PARTY_LICENSES.md`.
- **`release-drafter.yml`** — push to `main`, every PR: maintains the draft release, labels PRs
  by their title.
- **`docker.yml`** — release published: builds, pushes and signs the images.

---

## Deployment

`docker-compose.yml` starts `db`, `api` (migrations first) and `ui`, ports published on the
loopback address only — the operator puts a TLS-terminating proxy in front (see *The
components*). The API image runs one worker; neither image contains Node or the test tools.
The UI image has a Node stage that builds the stylesheet and the vendored browser files
(see [`DESIGN.md`](DESIGN.md)). Health endpoints under `/health/` (live, ready) are unauthenticated
and routed to the API.

---

## Scaffolding a new project

For an AI agent starting a new project from zero. In order:

1. **Write the specification first**, with requirement IDs (`FR-…`, `NFR-…`), and open
   `docs/implementation-notes.md` for decisions and deviations. Everything later is traceable to
   an ID.
2. **Create the uv workspace**: root `pyproject.toml` with the three members and workspace
   sources; `.python-version` 3.12; one `uv.lock`. Apply the naming table above.
3. **The API member**, inside out: `config.py` (Pydantic settings over env vars) → `db.py`
   (async engine, `lazy="raise"`) → `errors.py` (problem+json, the stable codes) → `models/` →
   `migrations/` (Alembic, hand-written) → `repositories/` → `domain/` (pure) → `services/`
   (principal-checked use cases) → `schemas/` → `auth/` (passwords, sessions, OIDC, tokens,
   principal, permissions) → `routers/` (thin, permission per route, `/health/…`, `/api/v1`
   prefix) → `cli.py` (bootstrap admin, seed) → `main.py` (factory + lifespan: migrations,
   reconcile built-ins).
4. **The contract member**: commit `src/contracts/openapi.json`; put `scripts/generate_client.py`
   in place; generate the client; add `--check` to CI. Refresh in the same commit as any endpoint
   change; keep `operationId`s stable for ever.
5. **The interface member**: follow the DESIGN.md porting checklist (brand layer verbatim,
   template skeleton, `init.js`/`app.js`, feeder code: Jinja environment, `render()`,
   `asset_url`, security-header middleware, the exception handlers — login redirect,
   failure-as-toast, unreachable). Wire it to the API through the generated client only.
6. **The import-linter contracts** (three, exactly as under *Engineering conventions*) — the
   mechanical proof of invariants 2 and 4.
7. **The four test suites** with the mechanics under *Testing*; the first test written is the
   migration-against-models test.
8. **Docker**: `docker/api.Dockerfile` and `docker/ui.Dockerfile` (multi-stage, non-root user,
   healthcheck, one worker), `docker-compose.yml` (`db`, `api`, `ui`, loopback ports),
   `docker/nginx.conf`, `.env.example` (every variable, `CHANGE_ME` placeholders only),
   `scripts/init_env.py`.
9. **The CI workflows** of the table above; branch rules; code owners.
10. **The root files** of *Engineering conventions*, including `AGENTS.md` linking to this
    blueprint, DESIGN.md and the project's own `docs/architecture.md`.

**Definition of done for the skeleton** (each item is a check, not a feeling):

- [ ] `uv run lint-imports` passes with all three contracts
- [ ] `uv run python scripts/generate_client.py --check` passes
- [ ] `uv run python scripts/i18n.py missing` reports nothing
- [ ] `uv run pytest -q` runs the four suites against a real PostgreSQL
- [ ] `docker compose up` starts db, api and ui; `/health/ready` answers; the interface signs in
      and renders a page built from API data
- [ ] a route without a permission fails the build
- [ ] the interface and the client do not import the API anywhere in the tree

---

## Appendix: projects that do not follow this blueprint

**papaia-manager** (github.com/Fidonis/papaia-manager), the papAIa control plane, is a sibling
project that predates this blueprint and is meant to be brought onto it. As of this writing it
deviates in the ways below; a project scaffolded from this document copies **none** of them — the
reference is this file, not that repository:

- One FastAPI process (`src/app`) serves both the pages and the JSON API; there is no workspace
  split, no `src/contracts` member, no snapshot and no drift check.
- The use cases live in a `core/` package that wraps a CLI subprocess and reads the files of the
  stack it manages; there is no `services`/`domain`/`repositories` layering, no database, and no
  migration model — state is YAML/JSONL on disk.
- Access is gated by three realm-role tiers, not by roles that hold permissions; there are no
  local accounts and no API tokens.
- The interface loads the standard Alpine build, not the CSP build, so it does not meet the
  interface contract of [`DESIGN.md`](DESIGN.md) as it stands.
- The audit log is a JSONL file, and long-running work is a job queue with detached runner
  containers — a shape that belongs behind the API of this blueprint, not beside the routes.

What it already shares with this blueprint — and what a new project inherits from both — is the
working method: AGENTS.md, the specification, the Fidonis brand layer (`fidonis-brand` stamp),
gettext catalogues, uv and the same tooling and CI skeletons.
