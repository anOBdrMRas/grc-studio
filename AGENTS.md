# AGENTS.md – working on GRC Studio

Context for humans and coding agents. Read this first, then the documents it links.

## What this is

GRC Studio is an integrated management system: processes modelled in BPMN 2.0, roles, positions
and people, approval workflow with four-eyes principle, change history; later risks,
opportunities, controls, KPI, audits and delegations. The behaviour is specified in
[SPEC.md](SPEC.md) (requirement IDs `FR-…`, `NFR-…`); the clickable React prototype in the
`GRC2` repository is where new ideas are tried with the users before they come here.

## The rules this project follows

- **Architecture:** [docs/BLUEPRINT.md](docs/BLUEPRINT.md) – two services (API, interface), one
  contract (`src/contracts/openapi.json`), PostgreSQL, Docker.
- **Interface:** [docs/DESIGN.md](docs/DESIGN.md) – Jinja2 + HTMX + Alpine (CSP build), Tailwind +
  daisyUI with the Fidonis themes, strict CSP, no CDN.
- **This project's shape and deviations:** [docs/architecture.md](docs/architecture.md) and
  [docs/implementation-notes.md](docs/implementation-notes.md) (A1–A7). A deviation is written
  down there before it is built.

## Invariants (checked by tools – keep them green)

1. The interface and the generated client never import `grc_api` (`uv run lint-imports`).
2. API layers point downwards: routers → services → repositories → models; `domain/` is pure.
3. Every route declares its permission with `**secured("perm")`, or is listed in `PUBLIC_PATHS`
   (`tests/api/test_contract.py`).
4. Every endpoint change refreshes the contract in the same commit:
   `uv run python scripts/generate_client.py` (CI runs `--check`). Never change an `operationId`.
5. Every schema change is an Alembic migration in `src/api/grc_api/migrations/versions/`;
   the migration-against-models test must pass.
6. Every user-visible text goes through gettext with the **English** text as message id; German
   lives in `src/ui/grc_ui/locale/de/LC_MESSAGES/messages.po`
   (`uv run python scripts/i18n.py extract`, then translate, then `… missing` reports nothing).
7. Changes to an element go through `services/common.save_element`: version check (`If-Match` →
   412, body version → 409, none → 428), rights, reopening of released elements, audit log.
8. No inline scripts, no inline event handlers, no `eval`: the CSP forbids them. Behaviour lives
   in `static/js/*.js` behind `data-action` attributes; Alpine only in its CSP build.
9. Only pseudonymised demo data in the repository. Real personal data never goes into git,
   fixtures, screenshots or issues.
10. A bug fix starts with a failing test.

## Layout

```
src/api/grc_api/        FastAPI: config, db, errors, models, migrations, repositories,
                        domain (pure rules), services (use cases + rights), schemas, auth, routers, cli
src/contracts/          openapi.json (snapshot) + grc_client (generated typed client)
src/ui/grc_ui/          interface: routes, templates, static/js, locale, forms.py (field definitions)
src/ui/                 package.json + tailwind config: build-time assets only (npm run build)
tests/unit|api|ui|e2e   the four suites (see README)
docker/                 Dockerfiles and the nginx entry proxy
scripts/                generate_client.py, i18n.py, init_env.py
```

## Commands

```bash
uv sync
(cd src/ui && npm ci && npm run build)       # after changing templates' classes or tailwind.*.css
uv run ruff check . && uv run ruff format .
uv run mypy && uv run lint-imports
uv run python scripts/generate_client.py [--check]
uv run python scripts/i18n.py extract|missing
TEST_DATABASE_URL=postgresql+psycopg://grc:grc@localhost:5432/grc_test uv run pytest -q
E2E_BASE_URL=http://localhost:8001 uv run pytest -m e2e tests/e2e
```

`TEST_DATABASE_URL` points at a database the tests **empty**. Never point it at real data.

## How a typical change flows

1. Find or add the requirement in `SPEC.md`.
2. API: model + migration → domain rule (pure, unit-tested) → service → schema → router with
   permission → API test → `generate_client.py`.
3. Interface: route calls the generated client → template/fragment → texts through `_()` →
   `i18n.py extract` + German translation → CSS build if new classes.
4. Run all checks; commit with a Conventional Commit message (`feat(processes): …`).

## Branches and commits

`main` is protected (PRs only, squash merge). Work on `feat/…`, `fix/…`, `docs/…`, `ci/…`,
`chore/…`. PR titles are Conventional Commits, lowercase, imperative, no trailing period.
