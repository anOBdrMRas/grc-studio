# GRC Studio – Spezifikation

Abgeleitet aus dem abgestimmten Prototyp (Repository `GRC2`, Stand November 2026). Jede
Anforderung hat eine ID; Code, Tests und Notizen verweisen darauf.

**Stufen:** **S1** = in dieser Version umgesetzt · **S2** / **S3** = folgt.

---

## 1. Allgemein

| ID | Anforderung | Stufe |
|---|---|---|
| FR-GEN-01 | Kopfzeile „GRC Studio · Prototyp“ mit Sprache (DE/EN), angemeldeter Person, Abmelden | S1 |
| FR-GEN-02 | Querbalken-Menü: ⌂ (Startseite) und Textpunkte ohne Icons; rechts „Administration“ | S1 |
| FR-GEN-03 | Listen und Details nebeneinander: Liste ⅓ (2–3 Kernspalten, Suche), Detail ⅔; die URL zeigt die Auswahl | S1 |
| FR-GEN-04 | Detail als Leseansicht; „Bearbeiten“ öffnet das Formular, „Speichern“ / „Abbrechen“ | S1 |
| FR-GEN-05 | Neu angelegte Elemente öffnen direkt im Bearbeitungsmodus | S1 |
| FR-GEN-06 | IDs werden automatisch vergeben (`RO-019`, `ST-020`, `P-013`, `U-021`) | S1 |
| FR-GEN-07 | Normbezüge über einen Katalog aller Kapitel von ISO 9001, ISO/IEC 27001 (inkl. Annex A), ISO 37301, ISO 14001; Auswahl fügt hinzu | S1 |
| FR-GEN-08 | Rollen- und Stellenbeschreibung als druckbare Ansicht (📄-Symbol) | S1 |
| FR-GEN-09 | Modulpunkte späterer Stufen zeigen „In Vorbereitung“ | S1 |
| FR-GEN-10 | Excel-Import und -Export je Modul mit Vorschau (neu / geändert / unverändert) | S3 |
| FR-GEN-11 | KI-Assistent („Wo finde ich …?“, Textvorschläge, Prozessentwurf) | S3 |
| FR-GEN-12 | Inhaltsverwaltung: eigene Felder und zusätzliche Auswahlwerte je Modul | S3 |

## 2. Anmeldung und Rechte

| ID | Anforderung | Stufe |
|---|---|---|
| FR-AUTH-01 | Demo-Anmeldung: Kacheln (Mitarbeiter, Führungskraft, I&A-Team, Administrator) und „Andere Person wählen“ | S1 |
| FR-AUTH-02 | Abschaltbar (`DEMO_LOGIN=false`): dann Benutzername und Passwort (argon2id, Sperre nach Fehlversuchen) | S1 |
| FR-AUTH-03 | Konten mit Passwort sind nie per Demo-Anmeldung erreichbar | S1 |
| FR-AUTH-04 | Systemrollen: Mitarbeiter (lesen), I&A-Team (alle Fachmodule bearbeiten, Qualitätsfreigabe), Administrator (Benutzerverwaltung, Status setzen, keine Qualitätsfreigabe) | S1 |
| FR-AUTH-05 | Owner bearbeiten ihre Elemente: Rollenverantwortlicher (Rolle), disziplinarischer Vorgesetzter (Stelle), Inhaber der verantwortlichen Rolle (Prozess) | S1 |
| FR-AUTH-06 | Owner-Felder (Verantwortliche) ändern nur I&A und Administration | S1 |
| FR-AUTH-07 | Benutzerverwaltung nur für die Administration | S1 |
| FR-AUTH-08 | Anmeldung über das Firmen-SSO (OIDC) | später |

## 3. Freigabe-Workflow und Historie

| ID | Anforderung | Stufe |
|---|---|---|
| FR-WF-01 | Entwurf → fachliche Freigabe (Owner) → I&A-Review → freigegeben; kompakte Statusleiste | S1 |
| FR-WF-02 | Qualitätsfreigabe nur durch das I&A-Team; Zurückweisen mit Pflichtkommentar | S1 |
| FR-WF-03 | Vier-Augen-Prinzip: wer fachlich freigegeben hat, gibt nicht die Qualität frei | S1 |
| FR-WF-04 | Erste Freigabe = Version 1.0, danach +0.1 | S1 |
| FR-WF-05 | Ändert der Owner ein freigegebenes Element, geht es auf Entwurf; der freigegebene Stand bleibt sichtbar (Umschalter „Entwurf / Freigegeben vX“) | S1 |
| FR-WF-06 | Administration setzt den Status direkt (ohne Qualitätsfreigabe) | S1 |
| FR-WF-07 | Änderungshistorie je Element: wer, wann, welches Feld alt → neu; Diagramm- und Zuordnungsänderungen als Notiz | S1 |
| FR-WF-08 | „Diesen Stand ansehen“ zeigt einen früheren Stand (lesend, keine Wiederherstellung) | S1 |
| FR-WF-09 | Startseite: „In meiner Verantwortung“ und für I&A „Wartet auf I&A-Freigabe“ | S1 |
| FR-WF-10 | Workflow auch für Risiken, Chancen und Delegationen (Delegation: Bestätigung durch Erteilenden und Empfänger) | S2 |

## 4. Organisation

| ID | Anforderung | Stufe |
|---|---|---|
| FR-ORG-01 | Rollen: Titel, Beschreibung, Rollentyp, Organisationseinheit, Pflichtrolle, Compliance-relevant, Rollenverantwortlicher, Verantwortung, Befugnisse, Kompetenzen, Schulungen, Normbezug, Review | S1 |
| FR-ORG-02 | Unvereinbare Rollen werden bei beiden Rollen eingetragen (symmetrisch) | S1 |
| FR-ORG-03 | Rollen zeigen Stellen und Personen, abgeleitet aus den Stellen | S1 |
| FR-ORG-04 | Stellen: Zweck, Aufgaben, Befugnisse, Anforderungen, disziplinarische/fachliche Hierarchie, Vertretung, Inhaber, Rollen mit Kommentar | S1 |
| FR-ORG-05 | Funktionstrennung: Warnung, wenn eine Stelle unvereinbare Rollen vereint | S1 |
| FR-ORG-06 | Benutzer: Nachname, Vorname, Bereich, Abteilung, Stelle, Bemerkung, Systemrollen | S1 |
| FR-ORG-07 | Delegationen und Vollmachten mit Gültigkeit, Annahme, Überwachung; Prüfungen zur Rechtssicherheit | S2 |
| FR-ORG-08 | Organigramm und Rollenzuordnungsmatrix | S2 |

## 5. Prozesse

| ID | Anforderung | Stufe |
|---|---|---|
| FR-PRC-01 | Prozesslandschaft nach Führungs-, Kern- und Unterstützungsprozessen; Klick öffnet den Prozess | S1 |
| FR-PRC-02 | BPMN-2.0-Editor (bpmn-js) im Browser; Speichern über die API mit Versionsprüfung | S1 |
| FR-PRC-03 | Nur gültige BPMN-Dokumente werden gespeichert (keine DTD/Entitäten, max. 5 MB) | S1 |
| FR-PRC-04 | Prozesssteckbrief (ISO 9001 4.4): Verantwortliche Rolle, Inputs, Outputs, Ressourcen, Normbezug, Review | S1 |
| FR-PRC-05 | Schrittbereich: Klick auf eine Aktivität zeigt deren Zuordnungen; Rollen mit RACI zuordnen und entfernen | S1 |
| FR-PRC-06 | Badges im Diagramm zeigen die Zuordnungen je Schritt | S1 |
| FR-PRC-07 | Änderungen an Diagramm und Zuordnungen zählen als Änderung des Prozesses (Version, Workflow, Historie) | S1 |
| FR-PRC-08 | Risiken, Chancen, Controls, KPI je Schritt; IKS-Hinweis bei Risiko ohne Kontrolle | S2 |
| FR-PRC-09 | Subprozesse mit Drill-down, Aufrufaktivitäten verknüpft, Import/Export `.bpmn` und `.svg` | S2 |

## 6. Risiken, Chancen, IKS, KPI, Audits

| ID | Anforderung | Stufe |
|---|---|---|
| FR-RSK-01 | Risikoregister mit 4×4-Matrix (mittel ab 4, hoch über 8), Ursache und Auswirkung, Owner (Person), Maßnahmenliste mit Verantwortlichen, Gesellschaft (CDE/CUS/CTW/CMY/CCZ) | S2 |
| FR-RSK-02 | Chancen nach ISO 9001 6.1 | S2 |
| FR-RSK-03 | Jede Person darf Risiken und Chancen erfassen; Freigabe über den Workflow | S2 |
| FR-ICS-01 | Controls (IKS) mit Wirksamkeit und Statement of Applicability (ISO 27001 Annex A) | S2 |
| FR-KPI-01 | KPI mit Schwellen, Messreihe und Ampel | S2 |
| FR-AUD-01 | Audits, Zertifikate und Feststellungen; Qualitätsprüfungen | S3 |

## 7. Nicht-funktionale Anforderungen

| ID | Anforderung | Stufe |
|---|---|---|
| NFR-ARCH-01 | Zwei Dienste (API, Oberfläche) nach docs/BLUEPRINT.md; die Oberfläche spricht nur über den generierten Client mit der API | S1 |
| NFR-ARCH-02 | API-Vertrag `openapi.json` versioniert; CI erkennt Abweichungen | S1 |
| NFR-SEC-01 | Strenge CSP ohne Inline-Skripte; keine externen Quellen (kein CDN) | S1 |
| NFR-SEC-02 | Server-Sitzung mit HttpOnly-Cookie (SameSite=Lax, Secure bei HTTPS) und CSRF-Token | S1 |
| NFR-SEC-03 | Jede Route deklariert ihre Berechtigung; ein Test schlägt fehl, wenn eine fehlt | S1 |
| NFR-SEC-04 | Container ohne root, Ports nur auf localhost, Geheimnisse nur in `.env` | S1 |
| NFR-DATA-01 | Optimistische Sperre je Element (Version); Konflikt wird gemeldet, Eingaben bleiben erhalten | S1 |
| NFR-DATA-02 | Audit-Log jeder Änderung, Anmeldung und Freigabe | S1 |
| NFR-DATA-03 | Schemaänderungen nur über Migrationen; Start spielt sie ein | S1 |
| NFR-DATA-04 | Nur pseudonymisierte Demodaten im Repository | S1 |
| NFR-I18N-01 | Oberfläche Deutsch (Standard) und Englisch über gettext; Inhalte werden nicht übersetzt | S1 |
| NFR-UX-01 | Fidonis-Design (hell/dunkel), Tastaturbedienung, sichtbarer Fokus | S1 |
| NFR-OPS-01 | `docker compose up` startet db, api, ui und Proxy; Healthchecks `/health/live`, `/health/ready` | S1 |
| NFR-QA-01 | Vier Testebenen (unit, api gegen PostgreSQL, ui, e2e im Browser) in der CI | S1 |
