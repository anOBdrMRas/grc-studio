# Contributing

1. Read [AGENTS.md](AGENTS.md): invariants, layout, commands.
2. Branch from `main`: `feat/…`, `fix/…`, `docs/…`, `refactor/…`, `test/…`, `ci/…`, `chore/…`.
3. Change the specification first if behaviour changes ([SPEC.md](SPEC.md)); a deviation from the
   blueprint goes into [docs/implementation-notes.md](docs/implementation-notes.md) first.
4. Keep the checks green locally (`ruff`, `mypy`, `lint-imports`, `generate_client.py --check`,
   `i18n.py missing`, `pytest`). A bug fix starts with a failing test.
5. Open a pull request with a Conventional Commit title (`feat(processes): add step matrix`).
   PRs are squash-merged; the title becomes the commit message.

Only pseudonymised demo data in commits, tests, screenshots and issues.
