# GRC Studio

Integriertes Managementsystem für Governance, Risk & Compliance: Prozesse mit BPMN-Editor,
Rollen, Stellen und Benutzer mit Freigabe-Workflow, Änderungshistorie und Rechtemodell.

Die Server-Version folgt dem Architektur-Blueprint ([docs/BLUEPRINT.md](docs/BLUEPRINT.md),
[docs/DESIGN.md](docs/DESIGN.md)). Sie hat zwei Dienste, eine HTTP-API und eine Weboberfläche,
und speichert in PostgreSQL. Der klickbare React-Prototyp bleibt im Repository `GRC2`; dort werden
neue Ideen abgestimmt, bevor sie hier umgesetzt werden.

**Stand:** Stufe 1 (Gerüst, Organisation, Prozesse mit BPMN). Was in welcher Stufe kommt, steht in
[SPEC.md](SPEC.md). Die Abweichungen vom Blueprint stehen in
[docs/implementation-notes.md](docs/implementation-notes.md).

---

## Betrieb (für die Administration)

### Voraussetzungen

- Linux-Server mit Docker Engine ≥ 24 und Docker Compose v2
- etwa 2 GB RAM und 5 GB Plattenplatz
- für den Zugriff aus dem Netz: ein TLS-Reverse-Proxy oder Load Balancer davor (HTTPS)

### Erster Start

```bash
git clone <repo-url> grc-studio && cd grc-studio
python3 scripts/init_env.py        # erzeugt .env mit zufälligen Passwörtern (Rechte 600)
# .env prüfen: PUBLIC_BASE_URL, DEMO_LOGIN, BOOTSTRAP_ADMIN_USER …
docker compose up -d --build
docker compose ps                  # alle Dienste "healthy"
```

Danach ist die Anwendung auf diesem Rechner unter <http://localhost:8080> erreichbar.

Beim Start spielt die API die Datenbank-Migrationen ein. Ist die Datenbank leer und
`SEED_DEMO_ON_EMPTY=true` gesetzt, lädt sie die pseudonymisierten Demodaten (20 Personen,
Rollen, Stellen und 12 Prozesse).

### Dienste

| Dienst | Image | Aufgabe |
|---|---|---|
| `db` | `postgres:16-alpine` | Datenbank, Volume `db-data` |
| `api` | `docker/api.Dockerfile` | Regeln und Datenzugriff, `/api/v1`, `/health/live`, `/health/ready` |
| `ui` | `docker/ui.Dockerfile` | Weboberfläche (HTML, kein Node zur Laufzeit) |
| `proxy` | `nginx:1.27-alpine` | einziger Einstieg auf Port 8080: `/api`, `/health` → API, Rest → Oberfläche |

Nach außen ist nur der Proxy veröffentlicht, und zwar standardmäßig nur auf `127.0.0.1`.
Datenbank, API und Oberfläche sind nur im internen Docker-Netz erreichbar.

### Im Netz bereitstellen

1. TLS-Proxy (z. B. der Firmen-Load-Balancer) auf `http://<server>:8080` zeigen lassen.
2. In `.env` setzen:
   - `PUBLIC_BASE_URL=https://grc.example.intern`. Damit werden Cookies `Secure` und HSTS aktiv.
   - `BIND_ADDRESS=0.0.0.0`, falls der Proxy auf einem anderen Rechner läuft.
3. `docker compose up -d`.

### Anmeldung

| `DEMO_LOGIN` | Verhalten |
|---|---|
| `true` | Anmeldeseite mit Kacheln und Personenauswahl, **ohne Passwort**. Nur für Demos mit Testdaten! |
| `false` | Anmeldung mit Benutzername und Passwort |

`BOOTSTRAP_ADMIN_USER` und `BOOTSTRAP_ADMIN_PASSWORD` legen beim Start einen Administrator mit
Passwort an, falls es ihn noch nicht gibt. Konten mit Passwort erscheinen nie in der Demo-Auswahl.

Weitere Administratoren legt man auf der Kommandozeile an:

```bash
docker compose exec api grc-api create-admin <benutzername>   # fragt das Passwort ab (mind. 12 Zeichen)
```

> **Wichtig:** Echte Personendaten nur mit `DEMO_LOGIN=false` und hinter TLS einspielen. Mit
> Demo-Anmeldung kann jede Person, die die Seite erreicht, jede andere Person „spielen“.

### Konfiguration (`.env`)

| Variable | Standard | Bedeutung |
|---|---|---|
| `POSTGRES_PASSWORD` | – | Passwort der Datenbank (Pflicht) |
| `PUBLIC_BASE_URL` | `http://localhost:8080` | Adresse, unter der Benutzer die Anwendung öffnen |
| `BIND_ADDRESS` / `HTTP_PORT` | `127.0.0.1` / `8080` | Schnittstelle und Port des Proxys auf dem Host |
| `DEMO_LOGIN` | `true` | Demo-Anmeldung ohne Passwort |
| `BOOTSTRAP_ADMIN_USER` / `_PASSWORD` | leer | erster Administrator |
| `SESSION_TTL_HOURS` | `12` | Gültigkeit einer Sitzung |
| `SEED_DEMO_ON_EMPTY` | `true` | Demodaten in eine leere Datenbank laden |
| `SETTINGS_SECRET` | – | verschlüsselt in der Datenbank gespeicherte Geheimnisse (API-Schlüssel des KI-Assistenten); stabil halten – ein neuer Wert macht den gespeicherten Schlüssel unlesbar |
| `DEFAULT_LANGUAGE` | `de` | Sprache der Oberfläche (`de`, `en`) |
| `LOG_LEVEL` | `INFO` | Protokollstufe der API |
| `API_IMAGE` / `UI_IMAGE` | lokaler Build | fertige Images aus `ghcr.io` statt Build |

### KI-Assistent

Der Assistent („Wo finde ich …?“) nutzt einen KI-Dienst, den die Administration unter
**Administration → KI-Assistent** einstellt:

- **Schnittstelle:** *OpenAI-kompatibel* (z. B. die interne con-AI; Aufruf
  `POST {Adresse}/chat/completions`, Schlüssel als `Authorization: Bearer`) oder
  *Anthropic-kompatibel* (Claude über `/v1/messages`, direkt oder über ein Gateway).
- **Adresse** des Dienstes, z. B. `https://con-ai.example/v1` (bei Anthropic direkt leer lassen),
  **Modell** laut Betreiber des Dienstes und **API-Schlüssel** (von den con-AI-Admins).
- Der Schlüssel wird mit `SETTINGS_SECRET` verschlüsselt gespeichert und nie wieder angezeigt.

Der API-Container braucht ausgehend HTTPS zur Adresse des Dienstes. Ist dessen Zertifikat von
einer internen Zertifizierungsstelle ausgestellt, das CA-Zertifikat in den API-Container einbinden
und `SSL_CERT_FILE` darauf setzen. An den Dienst gehen die Frage, die letzten Gesprächsschritte und
die Elemente, die die fragende Person lesen darf (Bezeichnungen, kurze Beschreibungen, Inhaber).
Ohne Schlüssel oder wenn der Dienst nicht antwortet, durchsucht der Assistent die Elemente ohne KI.

### Aktualisieren

```bash
git pull
docker compose up -d --build       # Migrationen laufen beim Start der API automatisch
```

Mit fertigen Images: in `.env` `API_IMAGE=ghcr.io/anobdrmras/grc-studio-api:<version>` und
`UI_IMAGE=…-ui:<version>` setzen, dann `docker compose pull && docker compose up -d`.

### Sicherung und Wiederherstellung

```bash
# Sicherung
docker compose exec -T db pg_dump -U grc -d grc --format=custom > grc-$(date +%F).dump
# Wiederherstellung (in eine leere Datenbank)
docker compose exec -T db pg_restore -U grc -d grc --clean --if-exists < grc-2026-01-31.dump
```

### Überwachung und Fehlersuche

- `curl http://127.0.0.1:8080/health/ready` liefert `{"status":"ok"}`, wenn API und Datenbank bereit sind.
- `docker compose logs -f api ui`
- `docker compose ps`: Healthchecks der Container

### Demodaten zurücksetzen

```bash
docker compose down -v      # löscht das Datenbank-Volume!
docker compose up -d
```

---

## Entwicklung

Voraussetzungen: [uv](https://docs.astral.sh/uv/), Node 22 (nur zum Bauen der Oberflächen-Assets),
PostgreSQL 16 (lokal oder `docker compose up -d db`).

```bash
uv sync                                         # Python-Umgebung (Python 3.12)
(cd src/ui && npm ci && npm run build)          # CSS, Schriften, htmx, Alpine, bpmn-js nach static/
export DATABASE_URL=postgresql+psycopg://grc:grc@localhost:5432/grc
uv run grc-api migrate && uv run grc-api seed-demo
uv run grc-api serve --port 8000                # API
uv run uvicorn grc_ui.main:app --port 8001      # Oberfläche → http://localhost:8001
```

Prüfungen, wie sie die CI ausführt:

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run lint-imports
uv run python scripts/generate_client.py --check   # API-Vertrag und Client aktuell?
uv run python scripts/i18n.py missing              # alle Texte übersetzt?
TEST_DATABASE_URL=postgresql+psycopg://grc:grc@localhost:5432/grc_test uv run pytest -q
E2E_BASE_URL=http://localhost:8001 uv run pytest -m e2e tests/e2e   # Browser gegen laufenden Stack
```

Hinweise für Menschen und KI-Agenten stehen in [AGENTS.md](AGENTS.md), die Architektur in
[docs/architecture.md](docs/architecture.md).
