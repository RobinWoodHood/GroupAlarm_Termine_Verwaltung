# Data Model: Interactive CLI TUI for GroupAlarm Appointment Management

**Date**: 2026-03-22 | **Status**: Complete

## Entities

### 1. Appointment (extended)

**Source**: `framework/appointment.py` — existing dataclass, extended with recurrence.

| Field | Type | Required | Source | Notes |
|-------|------|----------|--------|-------|
| id | `Optional[int]` | No (set by API) | API response | Primary key for updates/deletes |
| name | `str` | Yes | User input | Non-empty, max display ~200 chars |
| description | `str` | Yes | User input | Free-text |
| startDate | `datetime` | Yes | User input | Timezone-aware; displayed in configured TZ, sent as UTC |
| endDate | `datetime` | Yes | User input | Must be after startDate |
| organizationID | `int` | Yes | Config / CLI arg | From `.groupalarm.toml` or `--org-id` |
| labelIDs | `List[int]` | No | User input | References Label.id |
| isPublic | `bool` | No (default: True) | User input | |
| keepLabelParticipantsInSync | `bool` | No (default: True) | User input | |
| reminder | `Optional[int]` | No | User input | Minutes before start |
| notificationDate | `Optional[datetime]` | No | User input | Timezone-aware |
| feedbackDeadline | `Optional[datetime]` | No | User input | Timezone-aware; only for non-recurring |
| timezone | `str` | No (default: "UTC") | User input / config | IANA timezone name |
| participants | `List[Dict]` | No | API response | Read-only in TUI (complex structure) |
| recurrence | `Optional[Dict]` | No | API response | **NEW** — read-only in V1 |

**Recurrence sub-structure** (read-only, from API):

| Field | Type | Notes |
|-------|------|-------|
| frequency | `str` | "daily", "weekly", "monthly", "yearly" |
| interval | `int` | e.g., every 2 weeks → interval=2 |
| days | `Optional[List[int]]` | Weekdays for weekly: 0=Sun, 1=Mon, ..., 6=Sat |
| count | `Optional[int]` | Number of repetitions (exclusive with until) |
| until | `Optional[str]` | End date (exclusive with count) |
| week | `Optional[int]` | Week-of-month for monthly: 1, 2, -1, etc. |
| cancellations | `Optional[List]` | Cancelled occurrences (read-only) |

**Validation Rules**:
- `name` must be non-empty
- `startDate` and `endDate` must be `datetime` objects
- `endDate` must be strictly after `startDate`
- `organizationID` must be a positive integer
- `feedbackDeadline` may only be set when `recurrence` is None

**State Transitions**:
- New → (validate) → Confirmed → (POST /appointment) → Created (has id)
- Loaded → (edit fields) → Modified → (validate) → Confirmed → (PUT /appointment/{id}) → Saved
- Loaded → (delete) → Confirmed → (DELETE /appointment/{id}) → Deleted

---

### 2. Label

**Source**: GroupAlarm alarming API — `GET /labels?organization={id}&all=true`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | `int` | Yes | Primary key |
| name | `str` | Yes | Display name for filter UI |
| color | `str` | Yes | Hex color code (e.g., "#FF0000") for TUI rendering |
| organizationID | `int` | Yes | Must match configured org |
| description | `Optional[str]` | No | Tooltip / additional info |

**Usage**: Labels are fetched once on startup and cached for the session. Used for:
- Filter picker (selectable list with name + color indicator)
- Appointment detail panel (display label names instead of IDs)
- Assignment during create/edit (pick from available labels)

**Not modeled**: `assignees`, `availableUsers`, `minimumUsers`, `priority`, `pauseableUsers`, `smartLabelConfiguration`, `substitute` — these are not needed for appointment management.

---

### 3. AppConfig

**Source**: `.groupalarm.toml` — local config file

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| organization_id | `int` | Yes* | None | *Prompted on first run if missing |
| timezone | `str` | No | "Europe/Berlin" | IANA timezone for display |
| date_range_days | `int` | No | 30 | Default filter: today + N days |
| default_label_ids | `List[int]` | No | [] (all) | Pre-selected label filters on startup; validated against API |
| default_appointment_duration_hours | `int` | No | 4 | Default duration for new appointments in hours |

**TOML Structure**:
```toml
[general]
organization_id = 12345
timezone = "Europe/Berlin"

[defaults]
date_range_days = 30
label_ids = [101, 102, 103]
appointment_duration_hours = 4
```

**Behavior**:
- If file does not exist → prompt user for `organization_id`, create file with defaults
- If `organization_id` missing → prompt user, update file
- `--org-id` CLI arg overrides config value for current session (does not persist)
- Config values can be modified interactively during session (filter changes) but only `organization_id` persists back

---

### 4. ExportFile

**Source**: Generated `.xlsx` file for round-trip compatibility

| Column Header | Type | Source | Notes |
|----------------|------|--------|-------|
| name | str | Appointment.name | |
| description | str | Appointment.description | |
| startDate | str | Appointment.startDate | ISO 8601 in configured timezone |
| endDate | str | Appointment.endDate | ISO 8601 in configured timezone |
| organizationID | int | Appointment.organizationID | |
| labelIDs | str | Appointment.labelIDs | Comma-separated ints: "101,102" |
| isPublic | bool | Appointment.isPublic | |
| reminder | int/empty | Appointment.reminder | Minutes, empty if not set |
| notificationDate | str/empty | Appointment.notificationDate | ISO 8601 or empty |
| feedbackDeadline | str/empty | Appointment.feedbackDeadline | ISO 8601 or empty |
| timezone | str | Appointment.timezone | |
| groupalarm_id | int | Appointment.id | Enables update-not-create on re-import |
| ga_importer_token | str | Computed hash | ImporterToken for the existing Runner pipeline |

**Compatibility Constraint**: Column names and value formats MUST match what `ExcelImporter` + `Mapper` expect so the file can be passed directly to `Runner` for re-import.

---

## Relationships

```
AppConfig 1──* Appointment     (org ID links to API query)
Label    *──* Appointment      (via labelIDs list)
Appointment 1──1 ExportFile row (one row per appointment in export)
```

## API ↔ Data Model Mapping

| API Field | Data Model Field | Transform |
|-----------|-----------------|-----------|
| `id` | `Appointment.id` | Direct |
| `name` | `Appointment.name` | Direct |
| `description` | `Appointment.description` | Direct |
| `startDate` | `Appointment.startDate` | ISO 8601 string ↔ `datetime` (timezone-aware) |
| `endDate` | `Appointment.endDate` | ISO 8601 string ↔ `datetime` (timezone-aware) |
| `organizationID` | `Appointment.organizationID` | Direct |
| `labelIDs` | `Appointment.labelIDs` | Direct (list of ints) |
| `isPublic` | `Appointment.isPublic` | Direct |
| `keepLabelParticipantsInSync` | `Appointment.keepLabelParticipantsInSync` | Direct |
| `reminder` | `Appointment.reminder` | Direct (nullable int) |
| `notificationDate` | `Appointment.notificationDate` | ISO 8601 string ↔ `datetime` (nullable) |
| `feedbackDeadline` | `Appointment.feedbackDeadline` | ISO 8601 string ↔ `datetime` (nullable) |
| `timezone` | `Appointment.timezone` | Direct |
| `participants` | `Appointment.participants` | Direct (list of dicts, read-only in TUI) |
| `recurrence` | `Appointment.recurrence` | Direct (dict, read-only in V1) |
