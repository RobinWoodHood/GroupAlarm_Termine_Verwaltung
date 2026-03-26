# Contract: Exporter Module

**Scope**: New module `framework/exporter.py` — export appointments to Excel

## export_appointments

Exports a list of appointments to an `.xlsx` file compatible with the existing import pipeline.

**Signature**:
```python
def export_appointments(
    appointments: List[Appointment],
    output_path: Path,
    timezone: str = "Europe/Berlin",
) -> Path:
```

**Parameters**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| appointments | List[Appointment] | Yes | — | Appointments to export |
| output_path | Path | Yes | — | Target `.xlsx` file path |
| timezone | str | No | "Europe/Berlin" | Timezone for datetime display in export |

**Returns**: `Path` — the written file path (same as `output_path`).

**Raises**:
| Exception | Condition |
|-----------|-----------|
| ValueError | Empty appointment list |
| OSError | Cannot write to output_path |

**Output Format**: Excel workbook with single sheet, header row + one row per appointment.

**Columns** (in order):
1. `name` — str
2. `description` — str
3. `startDate` — ISO 8601 string in configured timezone
4. `endDate` — ISO 8601 string in configured timezone
5. `organizationID` — int
6. `labelIDs` — comma-separated ints (e.g., "101,102")
7. `isPublic` — bool
8. `reminder` — int or empty
9. `notificationDate` — ISO 8601 string or empty
10. `feedbackDeadline` — ISO 8601 string or empty
11. `timezone` — str
12. `groupalarm_id` — int (Appointment.id)
13. `ga_importer_token` — str (computed via `ImporterToken`)

**Round-trip guarantee**: The exported file MUST be re-importable by `ExcelImporter` + `Mapper` + `Runner` without manual changes, producing updates (not duplicates) for existing appointments.

**Security**: The API key MUST NOT appear anywhere in the exported file.
