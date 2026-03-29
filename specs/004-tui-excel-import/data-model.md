# Data Model: TUI Excel Import with Preview and Upload

**Feature**: 004-tui-excel-import  
**Date**: 2026-03-28

## Entities

### ImportConfig (new dataclass in `framework/config.py`)

Configuration for the Excel import workflow. Loaded from the `[import]` section of `.groupalarm.toml`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mapping_file` | `str \| None` | `None` | Path to a Python mapping module (Tier 2). `None` = use built-in default mapping (Tier 1) |
| `sheet_name` | `str \| None` | `None` | Excel sheet name. `None` = first sheet |

**Relationships**: Stored as a field on `AppConfig`. Used by `ImportService` to determine the mapping tier and configure the import.

**Validation rules**:
- `mapping_file`, if present, must be a valid path to an existing `.py` file
- The referenced Python module must export a `mapping` dict attribute
- `sheet_name`, if present, must be a non-empty string

**Tier selection logic**:
- Tier 2: `mapping_file` is set → load module, extract `mapping` + `defaults` dicts, use `Mapper`
- Tier 1: `mapping_file` is `None` → use built-in `DEFAULT_IMPORT_COLUMNS` (matches TUI export format)

**State transitions**: N/A (immutable configuration)

---

### ImportSession (new dataclass in `cli/services/import_service.py`)

Transient in-memory state representing one import workflow. Created when a file is parsed, discarded when the preview screen is dismissed.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `source_path` | `str` | required | Absolute path to the imported Excel file |
| `appointments` | `list[Appointment]` | required | Successfully parsed appointments |
| `skipped_rows` | `list[SkippedRow]` | `[]` | Rows that failed to parse |
| `column_mapping_used` | `str` | required | `"tier1-default"` or `"tier2-module:{path}"` — indicates which mapping tier was applied |

**Relationships**: Contains `Appointment` objects (existing entity). Referenced by `ImportPreviewScreen` for display and `ImportService.upload()` for execution.

**Validation rules**: `appointments` must not be empty (checked before entering preview).

**State transitions**:
- Created → Preview (displayed in `ImportPreviewScreen`)
- Preview → Upload (passed to `ImportService.upload()`)
- Upload → Discarded (after summary screen is dismissed)

---

### SkippedRow (new dataclass in `cli/services/import_service.py`)

Record of a row that could not be parsed into an appointment.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `row_index` | `int` | required | 0-based row index in the Excel file |
| `reason` | `str` | required | Human-readable explanation of why parsing failed |

**Relationships**: Part of `ImportSession.skipped_rows`.

---

### UploadResult (new dataclass in `cli/services/import_service.py`)

Outcome of a single appointment upload operation.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `appointment_name` | `str` | required | Name of the appointment for display |
| `action` | `str` | required | `"created"`, `"updated"`, or `"failed"` |
| `error` | `str \| None` | `None` | Error message if action is `"failed"` |
| `appointment_id` | `int \| None` | `None` | Server-assigned ID after successful create/update |

**Relationships**: Collected into `ImportSummary.results`.

**State transitions**: N/A (immutable result)

---

### ImportSummary (new dataclass in `cli/services/import_service.py`)

Aggregate outcome of the full upload operation.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `total` | `int` | required | Total appointments processed |
| `created` | `int` | `0` | Successfully created count |
| `updated` | `int` | `0` | Successfully updated count |
| `failed` | `int` | `0` | Failed count |
| `dry_run` | `bool` | `False` | Whether this was a dry-run upload |
| `results` | `list[UploadResult]` | `[]` | Per-appointment outcomes |

**Relationships**: Contains `UploadResult` objects. Displayed by `ImportSummaryScreen`.

**Computed properties**:
- `failed_results` → `[r for r in results if r.action == "failed"]`
- `success_rate` → `(created + updated) / total * 100` if total > 0

---

## Existing Entities (unchanged)

### Appointment (`framework/appointment.py`)

Used as-is. Import-parsed appointments are standard `Appointment` instances. The `id` field is populated from `groupalarm_id` column when present (for updates). The `description` field may include a `GA-IMPORTER` token (re-appended from `ga_importer_token` column or generated on create).

### AppConfig (`framework/config.py`)

Extended with one new field:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `import_config` | `ImportConfig \| None` | `None` | Import settings from `[import]` TOML section |

All existing fields unchanged.

---

## Entity Relationship Diagram

```
AppConfig ──has-one──▶ ImportConfig (optional)
                           │
                           ▼
                    ImportService.parse()
                           │
                           ▼
                     ImportSession
                     ├── appointments: list[Appointment]
                     └── skipped_rows: list[SkippedRow]
                           │
                    ImportService.upload()
                           │
                           ▼
                     ImportSummary
                     └── results: list[UploadResult]
```
