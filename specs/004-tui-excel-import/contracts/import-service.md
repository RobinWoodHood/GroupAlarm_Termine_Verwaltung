# Contract: ImportService

**Module**: `cli/services/import_service.py`  
**Feature**: 004-tui-excel-import

## Purpose

Orchestrate the full Excel import lifecycle: parse a file into appointments, and upload them to GroupAlarm. This service is stateless — each method receives its inputs and returns results without storing state across calls.

## Public Interface

### `load_mapping_module(mapping_file: str) -> tuple[dict, dict]`

Load a Python mapping module from a file path and extract `mapping` and `defaults` dicts.

**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `mapping_file` | `str` | Absolute or project-relative path to a `.py` file |

**Returns**: `(mapping, defaults)` — the `mapping` dict (required) and `defaults` dict (may be empty).

**Errors**:
- `FileNotFoundError` — file does not exist
- `ValueError` — file is not a `.py` file, has syntax errors, or does not export a `mapping` dict

**Behaviour**:
1. Resolve path (relative to project root if not absolute)
2. Validate file exists and has `.py` extension
3. Load via `importlib.util.spec_from_file_location()` + `module_from_spec()` + `loader.exec_module()`
4. Extract `module.mapping` (must be a dict) and `module.defaults` (optional dict, default `{}`)
5. Return `(mapping, defaults)`

---

### `parse_excel(file_path: str, import_config: ImportConfig | None, organization_id: int, timezone: str) -> ImportSession`

Parse an Excel file into a list of `Appointment` objects using the three-tier mapping strategy.

**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `file_path` | `str` | Absolute path to the Excel file |
| `import_config` | `ImportConfig \| None` | Import settings from config. `None` → Tier 1 default mapping |
| `organization_id` | `int` | Default organization ID for appointments without one |
| `timezone` | `str` | Default timezone for date parsing (e.g. `"Europe/Berlin"`) |

**Returns**: `ImportSession` containing parsed appointments and any skipped rows.

**Errors**:
- `FileNotFoundError` — file does not exist
- `ValueError` — file is not a valid Excel file, has no data rows, or mapping module has errors

**Tier Selection Behaviour**:
1. **Tier 2** (module): If `import_config` is not `None` and `import_config.mapping_file` is set:
   - Call `load_mapping_module(import_config.mapping_file)` to get `(mapping, defaults)`
   - Merge `defaults` with function params (`timezone`, `organization_id` as fallbacks)
   - Create `Mapper(mapping, defaults)` and use it to transform each row
   - Record `column_mapping_used = "tier2-module:{path}"`
2. **Tier 1** (default): If `import_config` is `None` or `mapping_file` is not set:
   - Use built-in `DEFAULT_IMPORT_COLUMNS` mapping (see table below)
   - Record `column_mapping_used = "tier1-default"`

**Common steps** (after tier selection):
1. Open file with `ExcelImporter(file_path, sheet_name=import_config.sheet_name if import_config else None)`
2. For each row:
   a. Apply the selected mapping (Tier 1: direct column lookup; Tier 2: `Mapper.map_row()`)
   b. If `groupalarm_id` present → set `appointment.id`
   c. If `ga_importer_token` present → append to description
   d. On parse error → record `SkippedRow` and continue
3. Return `ImportSession` with results

---

### `upload(appointments: list[Appointment], client: GroupAlarmClient, dry_run: bool) -> ImportSummary`

Upload a list of appointments to GroupAlarm, creating or updating as appropriate.

**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `appointments` | `list[Appointment]` | Appointments to upload |
| `client` | `GroupAlarmClient` | Authenticated API client |
| `dry_run` | `bool` | If `True`, log payloads but do not send requests |

**Returns**: `ImportSummary` with per-appointment results.

**Behaviour**:
1. For each appointment:
   a. If appointment description contains a `GA-IMPORTER` token:
      - Search server appointments in the appointment time window via `client.list_appointments(...)`
      - Match by token presence in server appointment description
      - If exactly one match found: set `appointment.id` to matched id and call `client.update_appointment(appointment)`
      - If no match found: record `UploadResult(action="failed", error="No server appointment found for GA-IMPORTER token ...")`
      - If multiple matches found: record `UploadResult(action="failed", error="Ambiguous GA-IMPORTER token match ...")`
   b. If no `GA-IMPORTER` token is present:
      - If `appointment.id` is not `None`: record failure (unsafe to update by mutable ID only)
      - If `appointment.id` is `None`: call `ImporterToken.ensure_token(appointment)` and create via `client.create_appointment(appointment)`
   c. On any exception → record `UploadResult(action="failed", error=str(exc))`
2. Return `ImportSummary` aggregating all results

---

## Default Column Mapping

When `import_config` is `None` or `import_config.mapping_file` is not set, the following mapping is used (matches `framework/exporter.COLUMNS`):

| Appointment Field | Excel Column | Parse Logic |
|-------------------|-------------|-------------|
| `name` | `name` | String, direct |
| `description` | `description` | String, direct |
| `startDate` | `startDate` | `dateutil.parser.isoparse()` |
| `endDate` | `endDate` | `dateutil.parser.isoparse()` |
| `organizationID` | `organizationID` | `int()` |
| `labelIDs` | `labelIDs` | Split on `,`, map to `int` |
| `isPublic` | `isPublic` | `bool()` |
| `reminder` | `reminder` | `int()` or `None` if empty |
| `notificationDate` | `notificationDate` | `isoparse()` or `None` if empty |
| `feedbackDeadline` | `feedbackDeadline` | `isoparse()` or `None` if empty |
| `timezone` | `timezone` | String, direct |
| `id` (Appointment.id) | `groupalarm_id` | `int()` or `None` if empty |
| (description append) | `ga_importer_token` | Re-appended to description if present |

## Dependencies

- `importlib.util` — dynamic Python module loading (Tier 2)
- `framework.importers.ExcelImporter` — file reading
- `framework.appointment.Appointment` — data model
- `framework.mapper.Mapper` — row-to-appointment mapping (Tier 2)
- `framework.importer_token.ImporterToken` — token management
- `framework.client.GroupAlarmClient` — API calls (for upload)
- `framework.client.AppointmentNotFound` — update race-condition handling
- `framework.utils.parse_date` — date parsing with format support (used in Tier 1 default mapping)
