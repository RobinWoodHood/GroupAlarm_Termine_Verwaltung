# GroupAlarm Terminverwaltung

Eine interaktive **Terminal-Oberfläche (TUI)** zum Verwalten von GroupAlarm-Terminen: anzeigen, erstellen, bearbeiten, löschen und exportieren — alles per Tastatur.

---

## Inhaltsverzeichnis

- [Installation](#installation)
- [Konfiguration](#konfiguration)
- [TUI starten](#tui-starten)
- [Bedienung & Tastenkürzel](#bedienung--tastenkürzel)
- [Dry-Run-Modus](#dry-run-modus)
- [Tests](#tests)
- [API-Referenz](#api-referenz)

---

## Installation

**Voraussetzungen**: Python ≥ 3.11

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

---

## Konfiguration

Die TUI liest ihre Einstellungen aus `.groupalarm.toml` im Projektverzeichnis. Eine Vorlage liegt in `.groupalarm.example.toml`:

```bash
cp .groupalarm.example.toml .groupalarm.toml
```

Passe mindestens `organization_id` an:

```toml
[general]
organization_id = 12345       # Deine GroupAlarm Organisations-ID
timezone = "Europe/Berlin"    # IANA-Zeitzone für Datumsanzeige

[defaults]
date_range_days = 30                # Standardzeitraum: Termine der nächsten N Tage
label_ids = []                      # Vorausgewählte Label-IDs (leer = alle)
appointment_duration_hours = 4      # Standard-Dauer für neue Termine (Stunden)
```

Zusätzlich wird ein **API-Token** als Umgebungsvariable benötigt:

```powershell
$env:GROUPALARM_API_KEY = "dein-personal-access-token"
```

Den Token erstellst du in deinem GroupAlarm-Account unter **Profil → Sicherheit**. **Gib diesen Token niemals weiter** — er hat die gleichen Berechtigungen wie dein Account.

---

## TUI starten

```bash
python groupalarm_cli.py
```

Optionale Argumente:

| Argument | Beschreibung |
|---|---|
| `--org-id ORG_ID` | Organisations-ID für diese Sitzung überschreiben |
| `--dry-run` | Keine Server-Schreiboperationen — Payloads werden nur geloggt |
| `--verbose` | DEBUG-Logging aktivieren |

---

## Bedienung & Tastenkürzel

### Navigation

| Taste | Aktion |
|---|---|
| ↑ / ↓ | Termin in der Liste auswählen (Detail-Vorschau aktualisiert sich live) |
| Enter / → | Fokus auf Detail-Panel wechseln |
| ← | Zurück zur Liste (nur im Lesemodus; warnt bei ungespeicherten Änderungen) |
| Ctrl+F | Textsuche in Terminen |
| Ctrl+T | Datums-/Zeitfilter fokussieren |

### Aktionen

| Taste | Aktion |
|---|---|
| E | Bearbeitungsmodus öffnen |
| Ctrl+S | Änderungen speichern (mit Bestätigungsdialog) |
| Escape | Bearbeitung abbrechen / Dialog schließen |
| N | Neuen Termin erstellen |
| D | Ausgewählten Termin löschen |
| X | Gefilterte Liste als Excel exportieren |
| R | Terminliste vom Server neu laden |
| F1 | Hilfe-Overlay anzeigen |
| Q | Beenden (warnt bei ungespeicherten Änderungen) |

### Im Bearbeitungsmodus

| Taste | Aktion |
|---|---|
| ← / → | Textcursor im Eingabefeld bewegen |
| ↑ / ↓ | Zwischen Eingabefeldern wechseln (in mehrzeiligen Feldern: interne Navigation) |
| Tab | Vorschlag akzeptieren (Labels, Teilnehmer) oder nächstes Feld |
| Escape | Bearbeitungsmodus verlassen |

### Zoom

| Taste | Aktion |
|---|---|
| Ctrl + / Ctrl − | Terminal-Zoom vergrößern / verkleinern |

---

## Dry-Run-Modus

Im Dry-Run-Modus werden keine Änderungen an den GroupAlarm-Server gesendet. Stattdessen werden die API-Payloads in die Logdatei (`groupalarm_cli.log`) geschrieben. Ideal zum Testen:

```bash
python groupalarm_cli.py --dry-run
```

---

## Tests

Die Test-Suite befindet sich im Verzeichnis `tests/` und verwendet Mock-HTTP-Responses:

```bash
pytest -q
```

---

## API-Referenz

Eine vollständige Übersicht aller Klassen und Methoden findest du in [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md).

Generierung:
```bash
python scripts/generate_api_docs.py --root . --output docs/API_REFERENCE.md
```
