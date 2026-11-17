# Implementierungsnotizen

Entscheidungen und Abweichungen vom [Blueprint](BLUEPRINT.md) und vom [Design](DESIGN.md).
Eine Abweichung wird hier eingetragen, bevor sie gebaut wird.

## Abweichungen

### A1 – Querbalken statt Seitenleiste (DESIGN.md: Layout)

Die Navigation ist ein horizontaler Menübalken unter der Kopfzeile: ⌂ und Textpunkte ohne Icons,
rechts „Administration“. So haben es die Fachbereiche im Prototyp abgestimmt. Die Inhaltsfläche
bekommt die volle Breite, was der BPMN-Editor braucht. Umsetzung: `templates/base.html`
(`.app-menubar`) und `grc_ui/nav.py`. Auf schmalen Bildschirmen bricht der Balken um.

### A2 – Geteilte Listen- und Detailansicht mit Leseansicht (DESIGN.md: CRUD im Dialog)

Liste ⅓ und Detail ⅔ nebeneinander. Das Detail öffnet als Leseansicht, „Bearbeiten“ tauscht das
Formular per HTMX ein. Statt eines Dialogs aktualisiert HTMX `#detail`, und die URL
(`/roles/RO-006`, `?edit=1`, `?view=released`, `?revision=…`) zeigt die Auswahl, damit Links und
der Zurück-Knopf funktionieren. Ein veralteter Stand liefert 409; das Formular zeigt dann die
Konfliktmeldung und behält die Eingaben. Umsetzung: `routes/modules.py` und `templates/entity/*`.

### A3 – BPMN-Editor als clientseitige Insel (DESIGN.md: „kein clientseitiges Rendering“)

`bpmn-js` 18 (Modeler bzw. Viewer je nach Recht) wird lokal ausgeliefert (`static/vendor`) und
von `static/js/process.js` gestartet. Das ist CSP-tauglich: kein `eval`, Styles über
`style-src-attr`. Das Diagramm-XML kommt über `GET /processes/{id}/diagram.xml` und wird mit
`PUT /processes/{id}/diagram` (JSON, CSRF-Header, Version) gespeichert. Die Oberfläche reicht die
Anfrage an die API weiter, die gültiges BPMN prüft (defusedxml, keine DTD) und versioniert.
Schrittauswahl, Zuordnungen und Workflow-Leiste bleiben HTMX-Fragmente. Ereignisse
(`badgesChanged`, `processChanged`) halten Badges, Version und Statusleiste aktuell.

### A4 – Demo-Anmeldung statt OIDC (BLUEPRINT.md: Sign-in)

Kein Keycloak/OIDC in Stufe 1. Mit `DEMO_LOGIN=true` gibt es die Kacheln und die Personenauswahl
des Prototyps, aber mit echter Server-Sitzung (HttpOnly-Cookie, CSRF-Token, Ablauf). Mit
`DEMO_LOGIN=false` meldet man sich mit Benutzername und Passwort an (argon2id, Sperre nach fünf
Fehlversuchen). Konten mit Passwort sind nie per Demo-Anmeldung erreichbar. Wo OIDC später
andockt: `auth/` (neuer Provider) und `services/auth.py`. Die Sitzungsmechanik bleibt.

### A5 – GitHub statt GitLab

Repository und CI liegen auf GitHub: `.github/workflows/ci.yml` und `docker.yml`, Images unter
`ghcr.io/anobdrmras/grc-studio-{api,ui}`, signiert mit cosign (keyless).

### A6 – Fidonis-Markenebene aus den Token-Werten

Die Originaldateien der Markenebene (`fidonis-brand`) lagen nicht vor. Die Themes `fidonis` und
`fidonis-dark` sind aus den Farb-, Schrift- und Radius-Token von DESIGN.md nachgebaut
(`src/ui/tailwind.brand.css`, `tailwind.config.js`). Sobald die Originaldateien vorliegen, werden
sie 1:1 übernommen und diese Dateien ersetzt.

### A7 – Noch nicht umgesetzte Blueprint-Teile (folgen)

- **Workflows** `license-check.yml` und `release-drafter.yml` sowie `TRADEMARK.md`.
  `THIRD_PARTY_LICENSES.md` ist von Hand gepflegt.
- **`tests/ui`** prüft die Oberfläche ohne laufende API (Templates, Sicherheitsheader,
  Weiterleitung, Formularauswertung). Die Strecke Oberfläche plus echte API decken die e2e-Tests ab.
- **testcontainers:** Die API-Tests nutzen `TEST_DATABASE_URL` (in der CI ein
  PostgreSQL-Service-Container).
- **Entry-Proxy:** `docker-compose.yml` enthält zusätzlich einen nginx als einzigen Einstieg auf
  Port 8080. So muss der Betrieb nur einen Port an seinen TLS-Proxy hängen.

## Entscheidungen

- **Englische Message-IDs, Deutsch als Standardsprache.** Katalogwerte (Rollentypen, Bereiche, …)
  speichert die API englisch; die Oberfläche übersetzt sie. Inhalte werden nicht übersetzt.
- **Versionierung:** Jede Tabelle eines Elements hat `version` (optimistische Sperre).
  Fachliche Versionen (`doc_version` 1.0, 1.1, …) vergibt nur der Workflow.
- **Historie** im Audit-Log (`audit_log.changes` mit `from`/`to`). „Diesen Stand ansehen“
  rechnet die späteren Änderungen zurück (`domain/history.state_at`); Diagramm-XML und
  freigegebene Kopie sind ausgenommen.
- **Schrittzuordnungen** (`step_assignments`) sind eigene Zeilen (Prozess, BPMN-Element, Rolle,
  RACI). Jede Änderung erhöht die Version des Prozesses und erzeugt einen Historieneintrag.
- **Freigegebener Stand:** Bearbeitet der Owner ein freigegebenes Element, speichert der Dienst
  den bisherigen Stand in `released` (JSONB) und setzt es auf Entwurf. Die nächste
  Qualitätsfreigabe leert `released`.
- **Demodaten** (`grc_api/seed/demo.json`) sind aus dem Prototyp exportiert und pseudonymisiert.
  Echte Daten kommen nie ins Repository.
- **Einschränkung:** Ein Konto ist nach fünf Fehlversuchen gesperrt. Entsperren geht in Stufe 1
  nur über die Datenbank (`failed_logins = 0`); eine Oberfläche dafür folgt mit der
  Benutzerverwaltung in Stufe 2.
