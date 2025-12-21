# GroupAlarm Import-Framework ✅

Eine **leichte Bibliothek**, um Termine aus CSV/Excel in GroupAlarm zu importieren und bei Folgeausführungen automatisch zu aktualisieren (anstatt Duplikate zu erstellen). Dieses Repository enthält ein Mapping-Framework (Mapper), Importer (CSV/Excel), einen Runner, sowie Token-basierte Persistenz für robuste Zuordnung von Terminen.

---

## Inhaltsverzeichnis
- Installation & Abhängigkeiten 🧩
- Schnellstart 🚀
- Konzeptübersicht (Mapper, Runner, Importer) 🧭
- Token / UUID (ImporterToken) 🔐
- Beispiele (CSV/Excel) 🗂️
- Optionen & Konfiguration ⚙️
- Troubleshooting & Hinweise ⚠️
- Tests 🔬

---

## Installation & Abhängigkeiten 🧩

Empfohlen: Erstelle ein virtuelles Environment (venv / conda) und installiere Abhängigkeiten:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# oder conda
conda create -n ga-env python=3.13
conda activate ga-env

pip install -r requirements.txt
```

Wichtiger Hinweis:
- Für Excel-Lese-/Schreiboperationen wird **openpyxl** empfohlen (falls nicht Teil Ihrer `requirements.txt`):
  ```bash
  pip install openpyxl
  ```
- Test-Utilities: `pytest` ist erforderlich, um die Test-Suite auszuführen.

---

## Schnellstart 🚀

1. Passe `example_usage.py` an (Dateipfad, Mapping, Zeitzone).
1. Passe `label_mapper.py` an (Die Label ID kann man bei GroupAlarm unter `konfiguration>labels` auslesen.)
1. Teste erstmal im **Dry-Run**-Modus, um Payloads zu prüfen (keine HTTP-Anfragen):

    ```python
    # In example_usage.py -> Runner(..., dry_run=True)
    python example_usage.py
    ```

1. Wenn alles passt, führe das Skript ohne `dry_run` aus. Das Skript fragt nach deinem **Personal-Access-Token** (wenn nicht als Argument übergeben):

    ```bash
    python example_usage.py
    ```

Beim Erstellen werden `groupalarm_id` und `ga_importer_token` (Standardspalten) **zurück in die CSV/Excel** geschrieben, sodass bei einem nächsten Lauf die Zeilen erkannt und aktualisiert werden (anstatt neu erzeugt zu werden).

**WICHTIG:** Wenn die Excel/CSV noch offen ist, werden die `groupalarm_id` und `ga_importer_token` nicht geschrieben. **Also immer die Excel schließen!!**

---

## Konzeptübersicht 🧭

### Runner
- Klasse: `framework.runner.Runner`
- Aufgabe: Iteriert über Zeilen eines Importers (CSV/Excel), wandelt jede Zeile via `Mapper` in ein `Appointment` und entscheidet, ob `create` oder `update` aufgerufen wird.
- Standardspalten (können konfiguriert werden):
  - **id_column** (default: `groupalarm_id`) — enthält die GroupAlarm-`id` wenn bereits vorhanden
  - **token_column** (default: `ga_importer_token`) — kompakte Importer-Token zur robusten Suche
- Verhalten:
  - Create: Token wird erzeugt, dem `description`-Feld angehängt; nach erfolgreicher Erstellung wird die vom Server zurückgegebene `id` und das Token in die Datenquelle geschrieben.
  - Update: Wenn `id` vorhanden, wird ein `PUT` mit `id` im Payload gesendet. Wenn Server `404` zurückgibt, wird versucht einen Termin im Zeitfenster per Token-Suche (Beschreibung) zu finden und dann erneut zu aktualisieren.

### Importer
- `framework.importers.CSVImporter` und `ExcelImporter`:
  - Laden die Datei über `pandas` in einen DataFrame.
  - Stellen `rows()` als Iterator bereit (pandas rows mit `row.name` = Index).
  - Unterstützen `set_value(index, column, value)` und `save()` um `groupalarm_id` und `token` zurückzuschreiben.

### Mapper
- Klasse: `framework.mapper.Mapper`
- Zweck: Übersetzt eine Zeile (dict-like) in ein `framework.appointment.Appointment` Objekt.
- Mapping-Definition: Ein `dict`, in dem Schlüssel den gewünschten Feldnamen im `Appointment` entsprechen (z. B. `name`, `description`, `startDate`, `endDate`, `organizationID`, `labelIDs`, `reminder`, ...).
- Feldwerte können Konstanten, oder Callables sein, die `(row, helpers)` erhalten (z. B. `helpers['parse_date']` für Datumspaarsing).

Beispiel-Mapping (aus `example_usage.py`):
```py
mapping = {
    "name": lambda r, helpers: f"{r['Dienstart']}",
    "description": lambda r, helpers: f"Ort: {r.get('Ort')}\nThema: {r.get('Thema')}",
    "startDate": lambda r, helpers: helpers['parse_date'](r['Beginn'], fmt="%d.%m.%Y %H:%M:%S", tz="Europe/Berlin"),
    "endDate": lambda r, helpers: helpers['parse_date'](r['Ende'], fmt="%d.%m.%Y %H:%M:%S", tz="Europe/Berlin"),
    "organizationID": 13915,
    "labelIDs": lambda r, helpers: map_labels_from_participants(r.get('Teilnehmer')),
}
```

---

## Token / UUID 🔐 (ImporterToken)

- Zweck: Wenn die Server-seitige `id` eines Termins sich ändert (z. B. Migration), erlaubt ein eingebetteter **kurzer Token** in der Terminbeschreibung (`description`), den Termin zuverlässig wiederzufinden.
- Implementierung: `framework.importer_token.ImporterToken`
  - Token-Format (kurz): `[GA-IMPORTER:8hex|YYYYMMDDHHMMSS|4hex]`
    - 8hex = erste 8 Zeichen einer UUID4
    - Zeitstempel (UTC) im Format `YYYYMMDDHHMMSS`
    - 4hex = Prüfsumme (sha1) der Kombination `shortid + ts` (erste 4 hex)
  - Funktionen:
    - `create_token()` → erzeugt Token
    - `find_in_text(text)` → findet Token in Text
    - `validate_token(token)` → prüft Prüfsumme
- Workflow:
  - Neu erstellte Termine bekommen Token in der Beschreibung und die Token-Spalte (`ga_importer_token`) wird gefüllt.
  - Bei Update-Fehlern (404) sucht der Runner per List-API im Zeitfenster nach Terminen, deren Beschreibung diesen Token enthält. Wird ein Treffer gefunden, wird das Update erneut mit der neuen `id` versucht.

---

## Beispiele (CSV / Excel) 🗂️

Beispiel CSV/Excel-Spalten, die nützlich sind:

| Spalte | Beschreibung |
|---|---|
| `Dienstart` | Titel/Name des Termins |
| `Beginn` / `Ende` | Datums-Strings (z. B. `06.01.2026 19:00`) |
| `Thema`, `Teilnehmer`, `Ort` | zusätzliche Felder |
| `groupalarm_id` | **wird vom Runner geschrieben** — enthält die `id` bei Erfolg |
| `ga_importer_token` | **wird vom Runner geschrieben** — kompakter Token zur Wiedererkennung |

Wenn du eine bestehende Datei verwendest, füge optional die beiden Spalten `groupalarm_id` und `ga_importer_token` hinzu, damit die Zeilen beim nächsten Lauf erkannt werden.

---

## Optionen & Konfiguration ⚙️

Wichtige Runner-Parameter:

- `dry_run` (bool): Standard `True` — keine HTTP-Aufrufe, nur Logging.
- `id_column` (str): Standard `'groupalarm_id'` — Spaltenname, in dem die GroupAlarm-ID gespeichert wird.
- `token_column` (str): Standard `'ga_importer_token'` — Spaltenname für das Importer-Token.

Hilfsfunktionen:
- `helpers['parse_date']` (aus `framework.utils`) um konsistent Datumsstrings zu parsen (konfigurierbarer Format-String `fmt` und `tz`).

---

## Troubleshooting & Hinweise ⚠️

- CSV-Encoding: Windows-Excel CSV-Dateien verwenden oft `cp1252` (Windows-1252). Wenn du `UnicodeDecodeError` oder fehlerhafte Zeichen siehst, setze beim CSVImporter `encoding='cp1252'` oder `utf-8-sig`.
- Excel Write-Back: Um `ExcelImporter.save()` zuverlässig zu benutzen, installiere `openpyxl`.
- Datumspunkte: Achte auf genaue Format-Strings in `parse_date`. Bei abweichenden Formaten kannst du alternativ `dateutil.parse` verwenden (falls nötig, kann ich einen robusten Fallback vorschlagen).
- Tests: Wenn `pytest` nicht vorhanden ist, installiere es (`pip install pytest`).

---

## Tests 🔬

Die Test-Suite befindet sich im Verzeichnis `tests/`.

```bash
pip install -r requirements.txt
pytest -q
```

Die Tests verwenden Mock-HTTP-Responses, um API-Aufrufe abzukapseln.

---

## Noch zu tun / Empfehlungen 💡

- Optional: `requirements.txt` um `openpyxl` ergänzen, falls Excel-Writeback standardmäßig unterstützt werden soll.
- README mit einem kurzen Beispiel für Excel-Export/Import erweitern (wenn du möchtest, mache ich das).

---

## Kontakt & Mitwirkung 🤝


Viel Erfolg! 🎯

---

*Dieser Leitfaden wurde automatisch generiert*
