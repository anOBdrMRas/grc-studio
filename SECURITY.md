# Security

## Reporting a vulnerability

Please do **not** open a public issue. Report it privately to the repository owners (GitHub:
"Report a vulnerability" under *Security*, or directly to the code owners). We answer within five
working days.

## What the application does

- Strict Content Security Policy without inline scripts; all libraries served locally.
- Server-side sessions (HttpOnly cookie, `SameSite=Lax`, `Secure` behind HTTPS) and a CSRF token
  on every changing request.
- A declared permission on every API route (enforced by a test); rights checked in the services.
- Passwords hashed with argon2id; accounts locked after five failed attempts.
- BPMN uploads parsed with defusedxml (no DTDs or entities), size-limited.
- Containers run as a non-root user; only the entry proxy is published, on loopback by default.

## What the operator must do

- Put a TLS-terminating proxy in front and set `PUBLIC_BASE_URL=https://…`.
- Set `DEMO_LOGIN=false` before real personal data is loaded: the demo sign-in lets anyone who
  reaches the page act as any person without a password.
- Keep `.env` private (generated with mode 600 by `scripts/init_env.py`) and back up the database.
