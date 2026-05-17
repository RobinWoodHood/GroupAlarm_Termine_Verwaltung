# GroupAlarm Terminverwaltung

Eine interaktive **Terminal-Oberfläche (TUI)** zum Verwalten von GroupAlarm-Terminen: anzeigen, erstellen, bearbeiten, löschen und exportieren — alles per Tastatur.

---

## 🚀 Schnellstart (für Anfänger)

### Schritt 1: Python installieren

Falls Python noch nicht installiert ist:

1. Gehe auf **https://www.python.org/downloads/**
2. Lade die neueste Version herunter (≥ 3.11)
3. **Wichtig:** Bei der Installation muss die Option **"Add Python to PATH"** angehakt sein
4. Klicke auf "Install Now"
5. Nach der Installation kannst du das Fenster schließen

### Schritt 2: Abhängigkeiten installieren

1. Öffne im Projektverzeichnis die Datei **`install.bat`** (Doppelklick)
2. Ein schwarzes Fenster öffnet sich und installiert automatisch alles Notwendige
3. Das Fenster schließt sich automatisch, wenn fertig
4. **Fertig!** Die Umgebung ist jetzt einsatzbereit

### Schritt 3: Tool starten

1. Doppelklick auf **`start.bat`** — das Tool startet sofort
2. Alternativ kannst du auch eine Verknüpfung auf dem Desktop erstellen (siehe nächster Schritt)

### Schritt 4: Eigene Desktop-Verknüpfung erstellen (optional)

So erstellst du eine bequeme Verknüpfung auf deinem Desktop — ohne Dateien zu kopieren:

### Schnell via Rechtsklick

1. Öffne **`start.bat`** im Projektverzeichnis (im Explorer)
2. Mache einen **Rechtsklick** darauf → **"Senden an"** → **"Desktop (Verknüpfung erstellen)"**
3. Eine neue Verknüpfung namens **"Verknüpfung mit start"** erscheint auf deinem Desktop
4. Benenne sie um in **"GroupAlarm TUI"** (optional):
   - Rechtsklick → "Umbenennen" → neuen Namen eingeben

#### Icon der Verknüpfung ändern (optional)

Um die Verknüpfung mit einem eigenen Icon zu versehen:

1. **Rechtsklick** auf die Desktop-Verknüpfung → **"Eigenschaften"**
2. Klicke auf den Button **"Anderes Symbol"** (oder **"Icon ändern"**)
3. Wähle ein Icon aus:
   - Windows Standard-Icons sind meist im `C:\Windows\System32\` Verzeichnis (z.B. `shell32.dll`)
   - **Tipp:** Probiere diese Icons aus: `THW.svg.ico`
4. Klicke **"OK"** → **"Übernehmen"** → **"OK"**

### Schritt 5: Desktop-App unter Linux erstellen (optional)

Unter Linux (z. B. Fedora KDE Plasma, Ubuntu, Debian) kannst du eine bequeme Desktop-Verknüpfung als Anwendung registrieren:

#### Methode 1: Automatisch über GUI (einfach)

1. Öffne deinen **Application Menu** oder **Application Launcher**
2. Suche nach "Anwendungs-Editor" oder "Desktop Entry Editor"
3. Erstelle einen neuen Eintrag mit folgenden Informationen:
   - **Name**: `GroupAlarm Terminverwaltung`
   - **Beschreibung**: `GroupAlarm Terminverwaltung TUI`
   - **Befehl**: `konsole -e bash -c "cd /pfad/zum/projekt && ./start_groupalarm.sh"`
   - **Icon**: Wähle `THW.svg.ico` oder ein anderes Icon aus deinem Projektverzeichnis
4. Speichern und fertig!

#### Methode 2: Manuell via Texteditor (vollständige Kontrolle)

1. Öffne einen Texteditor und erstelle eine neue Datei:
   ```bash
   nano ~/.local/share/applications/groupalarm.desktop
   ```

2. Füge folgenden Inhalt ein (passe die Pfade an deine Installation an):
   ```ini
   [Desktop Entry]
   Version=1.0
   Type=Application
   Name=GroupAlarm Terminverwaltung
   Comment=GroupAlarm Terminverwaltung TUI
   Exec=konsole -e bash -c "cd /pfad/zum/workspace/GroupAlarm_Termine_Verwaltung && ./start_groupalarm.sh; read -p 'Drücke Enter zum Schließen...' "
   Icon=/pfad/zum/workspace/GroupAlarm_Termine_Verwaltung/THW.svg.ico
   Terminal=false
   Categories=Utility;Development;
   Keywords=python;termin;verwaltung;
   StartupNotify=true
   ```

3. Speichern (Ctrl+X → Y → Enter)

4. Die Anwendung sollte jetzt in deinem **Application Menu** sichtbar sein

#### Desktop-Entry-Felder erklärt

| Feld | Beschreibung |
|---|---|
| `Version` | Version des Desktop Entry Standards (üblicherweise `1.0`) |
| `Type` | `Application` für ausführbare Programme |
| `Name` | Anwendungsname wie im Menü angezeigt |
| `Comment` | Kurzbeschreibung (Tooltip) |
| `Exec` | Befehl zum Starten der Anwendung |
| `Icon` | Pfad zum Icon (absolut oder Name aus Icon-Theme) |
| `Terminal` | `false` = verstecktes Terminal; `true` = sichtbares Terminal |
| `Categories` | Menü-Kategorien (z. B. `Utility`, `Development`, `Office`) |
| `Keywords` | Suchbegriffe zum Auffinden in der App-Suche |
| `StartupNotify` | `true` = Loading-Cursor anzeigen während Start |

#### Icon hinzufügen

1. **Icon bereitstellen**: Kopiere eine Icon-Datei (`.ico`, `.png`, `.svg`) in dein Projektverzeichnis oder ein System-Verzeichnis
2. **Icon-Pfad setzen**: 
   - Absoluter Pfad: `/pfad/zum/workspace/GroupAlarm_Termine_Verwaltung/THW.svg.ico`
   - Icon-Name (falls in Theme): `groupalarm-icon` (muss in `/usr/share/icons/` liegen)
3. Speichern und die Desktop-App neustarten (oder `pkill -f groupalarm.desktop`)

#### Verschiedene Desktop-Umgebungen

Die Anwendung wird automatisch registriert in:
- **KDE Plasma** (Fedora, openSUSE)
- **GNOME** (Ubuntu, Fedora)
- **Cinnamon** (Linux Mint)
- **XFCE** (Xubuntu, Xfce4)

Nach dem Erstellen der `.desktop`-Datei einfach den Application Launcher neu laden (oder neustarten).

---

## Inhaltsverzeichnis

- [🚀 Schnellstart (für Anfänger)](#-schnellstart-für-anfänger)
- [📖 Technische Beschreibung](#-technische-beschreibung)
  - [Installation (Fortgeschrittene)](#installation-fortgeschrittene)
  - [Konfiguration](#konfiguration)
  - [TUI starten](#tui-starten)
  - [Bedienung & Tastenkürzel](#bedienung--tastenkürzel)
  - [Excel-Import (Tier 1 & Tier 2)](#excel-import-tier-1--tier-2)
  - [Dry-Run-Modus](#dry-run-modus)
  - [Tests](#tests)
  - [API-Referenz](#api-referenz)
  - [FAQ — Häufige Fragen](#faq--häufige-fragen)
  - [Rechtliches & Lizenzen](#rechtliches--lizenzen)

---

## 📖 Technische Beschreibung

### Installation (Fortgeschrittene)

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
show_startup_welcome = true   # Detail-Panel startet mit Willkommensseite

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
| ↑ / ↓ | Termin in der Liste auswählen (nach Auswahl per Enter aktualisiert sich die Detailansicht) |
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
| Ctrl+O | Termine aus Excel importieren |
| Ctrl+P | Textual Command Palette (z. B. Theme-Wechsel, Startup-Willkommensseite umschalten) |
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

## Excel-Import (Tier 1 & Tier 2)

Der Import wird in der TUI mit `Ctrl+O` gestartet.

### Tier 1 (Standard)

- Nutzt die eingebaute Standard-Spaltenzuordnung.
- Funktioniert ohne zusätzliche Konfiguration.

### Tier 2 (eigene Mapping-Logik)

Für abweichende Excel-Strukturen kann ein eigenes Mapping-Modul in der Konfiguration gesetzt werden:

```toml
[import]
mapping_file = "import.example.py"
# Optional:
# sheet_name = "Tabelle1"
```

Hinweise zu `mapping_file`:

- Pfad relativ zum Projektverzeichnis oder als absoluter Pfad.
- Das Modul muss ein `mapping`-Dict bereitstellen; optional sind `defaults`.
- In der Import-Vorschau wird der verwendete Modus angezeigt (`Tier 1` oder `Tier 2`).


Automatisierte Tests für die Import-Logik:

```bash
pytest -q tests/test_import_service.py tests/test_import_config.py
```

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

---

## FAQ — Häufige Fragen

### Warum schlägt der Import mit „label does not belong to organization" fehl?

Der Import arbeitet immer gegen eine bestimmte **Organisations-ID** (`organization_id` in `.groupalarm.toml`). Beim eingebauten Excel-Export werden die Org-ID, die Termin-ID und der GA-IMPORTER-Token mit in die Datei geschrieben. Wenn du diese Datei anschließend in eine **andere Organisation** importierst, versucht das Tool, die bestehenden Termine per Token zu aktualisieren — und scheitert, weil die IDs und Labels zur alten Org gehören.

**Lösung:** Wenn du Termine von einer Org in eine andere übertragen willst, lösche in der Excel-Datei folgende Spalten bzw. Werte:

1. **Org-ID** — damit die Termine der neuen Org zugeordnet werden.
2. **Termin-ID (`id`)** — damit keine bestehenden Termine überschrieben werden.
3. **GA-IMPORTER-Token** (in der Beschreibung, Format `[GA-IMPORTER:…]`) — damit das Tool den Create-Pfad wählt statt den Update-Pfad.

Nur dann werden die Termine als **neue Einträge** in der Ziel-Organisation angelegt.

### Warum werden Termine als „Update" statt als „Neu" behandelt?

Die Upload-Logik entscheidet in zwei Stufen, ob ein Termin aktualisiert oder neu angelegt wird:

```
Termin aus Excel
│
├─ GA-IMPORTER-Token in Beschreibung vorhanden?
│  │
│  ├─ JA → Update-Pfad
│  │   └─ Server-Termine im gleichen Zeitfenster abfragen
│  │       ├─ Genau 1 Treffer mit gleichem Token
│  │       │   └─ Termin-ID vom Server übernehmen → PUT (Update)
│  │       ├─ 0 Treffer → Fehlschlag („update skipped to avoid duplicates")
│  │       └─ >1 Treffer → Fehlschlag („ambiguous match")
│  │
│  └─ NEIN → Create-Pfad
│       ├─ Termin-ID gesetzt?
│       │   └─ JA → Fehlschlag („no token, cannot perform safe update")
│       └─ Termin-ID leer (None)?
│           └─ Neuen Token generieren → POST (Erstellen)
```

**Wichtig:** Die Entscheidung Create vs. Update hängt **ausschließlich vom GA-IMPORTER-Token** ab, nicht von der Termin-ID. Die Termin-ID allein reicht nicht aus — ohne Token wird ein Update bewusst verweigert, weil IDs sich serverseitig ändern können und keine sichere Identifikation bieten.

| Zustand in der Excel | Ergebnis |
|---|---|
| Kein Token, keine ID | **Neuer Termin** (Token wird automatisch erzeugt) |
| Kein Token, ID vorhanden | **Fehlschlag** (unsichere Identität) |
| Token vorhanden, keine ID | **Update** (Server-ID wird per Token-Lookup ermittelt) |
| Token vorhanden, ID vorhanden | **Update** (Server-ID wird per Token-Lookup ermittelt, Excel-ID wird ignoriert) |

Wenn du aus einem Export importierst und neue Termine erzeugen willst, entferne **sowohl den Token als auch die ID** aus der Excel-Datei.

---

## Rechtliches & Lizenzen

- Projektlizenz: MIT, siehe `LICENSE`.
- Drittanbieterhinweise: siehe `THIRD_PARTY_NOTICES.md`.
- Keine Gewährleistung: Die Software wird ohne Zusicherung bereitgestellt (siehe MIT-Lizenztext).

### GroupAlarm API-Dokumentation

Die Dateien unter `api-docs/` (OpenAPI-Spezifikationen) dienen der Interoperabilität mit GroupAlarm. Sie stammen nicht aus diesem Projekt und sind nicht automatisch von der MIT-Lizenz dieses Repositories umfasst. Nutzung und Weitergabe richten sich nach den Bedingungen des jeweiligen Rechteinhabers (GroupAlarm).
