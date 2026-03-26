# Research: Interactive CLI TUI for GroupAlarm Appointment Management

**Date**: 2026-03-22 | **Status**: Complete

## R-001: Textual Framework — Layout & Widget Patterns

**Task**: Determine best patterns for split-view layout with scrollable list + editable detail panel.

**Decision**: Use `Horizontal` container with `VerticalScroll` (left pane: appointment list) and `Vertical` (right pane: editable form). CSS controls pane ratios (`width: 1fr` / `width: 2fr`).

**Rationale**: Textual's built-in container widgets (`Horizontal`, `Vertical`, `VerticalScroll`) provide native scroll support without custom logic. CSS-based sizing enables responsive layout on terminal resize.

**Key Patterns**:
- `App` subclass with `compose()` method returning widget tree
- `Footer` widget auto-renders `BINDINGS` list; use `show=False` for internal bindings
- Context-dependent bindings via screen-level `BINDINGS` override
- `OptionList` or `DataTable` for the appointment list widget
- `Input` widgets with `restrict` regex for structured fields (dates, numbers)

**Alternatives Considered**:
- Rich (no interactive widgets, no event loop — rejected)
- urwid (lower-level, more boilerplate, less maintained — rejected)
- Blessed/curses (no Python-native async, poor Windows support — rejected)

---

## R-002: Textual — Modal Confirmation Dialogs

**Task**: Determine best approach for confirmation dialogs (Constitution Principle II).

**Decision**: Use `ModalScreen[bool]` subclass with typed dismiss result. Push via `self.push_screen(ConfirmDialog(payload), callback)`.

**Rationale**: `ModalScreen` dims background, blocks parent bindings, and provides a typed return channel. This ensures the user cannot interact with the main UI while the confirmation is pending.

**Key Patterns**:
```python
class ConfirmDialog(ModalScreen[bool]):
    def compose(self) -> ComposeResult:
        with Grid(id="dialog"):
            yield Static(self.diff_text)  # rendered diff
            yield Button("Confirm", id="yes", variant="error")
            yield Button("Cancel", id="no", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")
```

**Alternatives Considered**:
- Non-modal overlay (user could accidentally click through — rejected per Constitution II)
- Standard `Screen` (does not block parent bindings — rejected)

---

## R-003: Textual — Async API Operations

**Task**: Determine how to keep UI responsive during API calls.

**Decision**: Use `@work(thread=True, exclusive=True)` decorator for API calls since `requests` is a blocking library. Use `call_from_thread()` to update UI from worker threads.

**Rationale**: The existing `GroupAlarmClient` uses `requests` (blocking). Wrapping calls in `@work(thread=True)` offloads them to a thread pool while keeping the Textual event loop responsive. `exclusive=True` prevents concurrent conflicting operations.

**Key Patterns**:
```python
@work(thread=True, exclusive=True)
def load_appointments(self) -> None:
    data = self.client.list_appointments(start, end, ...)
    self.call_from_thread(self.populate_list, data)
```

**Alternatives Considered**:
- Rewriting GroupAlarmClient with httpx/aiohttp (significant refactor, violates Constitution IV — rejected)
- Running API calls on main thread (blocks UI — rejected)

---

## R-004: Textual — Testing with Pilot API

**Task**: Determine testing strategy for TUI widgets and screens.

**Decision**: Use `app.run_test()` async context manager with `pilot` object for simulating user interactions. Combine with monkeypatch for API mocking.

**Rationale**: Textual's pilot API supports key presses, clicks, and widget queries in async tests. This aligns with the existing pytest-based test infrastructure (Constitution VI).

**Key Patterns**:
```python
async def test_appointment_list_loads():
    app = GroupAlarmApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        table = app.query_one("#appointment-list")
        assert table.row_count > 0
```

**Alternatives Considered**:
- Snapshot testing (fragile on different terminal sizes — use only for CSS regression, not primary)
- Manual testing only (violates Constitution VI — rejected)

---

## R-005: Label API — Fetching Available Labels

**Task**: Determine how to fetch labels for the filter picker (FR-023).

**Decision**: Use `GET /labels?organization={id}&all=true` from the alarming API (`https://app.groupalarm.com/api/v1/labels`). This returns all labels for the given organization directly — no post-filtering needed.

**Rationale**: The alarming API provides three label-listing endpoints. `GET /labels` is the best fit because it takes the organization ID as a direct query parameter and supports `all=true` to bypass pagination limits (max 50 per page otherwise). The same `Personal-Access-Token` header works for both APIs.

**API Details**:
- **Primary**: `GET /labels?organization={org_id}&all=true`
  - Response: `LabelList` → `{ labels: Label[], total: int }`
  - Supports optional `type` param: `"normal"` (default), `"smart"`, `"all"`
  - Supports optional `search` param for name filtering
  - Supports optional `user` param to limit to a user's labels
- **Alternative**: `GET /labels/export/{organizationID}` (operationId: `GetLabelsCSV`)
  - Returns CSV file (`text/csv`) with all labels — useful for bulk export but not needed for the TUI picker
- **Alternative**: `GET /label/organizations` (operationId: `GetOrganizationsWithLabels`)
  - Returns labels grouped by organization — more complex, requires client-side filtering
- Label schema: `{ id, name, color, organizationID, description, assignees, ... }`
- Auth: Same `Personal-Access-Token` header as appointment API
- Base URL: Same (`https://app.groupalarm.com/api/v1`)

**Alternatives Considered**:
- `GET /label/organizations` (returns grouped data, requires extraction per org — unnecessarily complex)
- `GET /labels/export/{organizationID}` CSV endpoint (returns CSV, would need parsing — overkill for TUI picker)
- Hardcoding label IDs in config (user requested API-driven labels — rejected)
- Scraping labels from existing appointments (incomplete if some labels have no appointments — rejected)

---

## R-006: Config File — `.groupalarm.toml` Format

**Task**: Determine config file format and read/write approach.

**Decision**: Use TOML format with `tomllib` (stdlib in Python 3.11+) for reading and `tomli-w` for writing. File location: `.groupalarm.toml` in the current working directory (project root).

**Rationale**: TOML is human-readable, well-supported in Python 3.11+ stdlib, and appropriate for the small set of configuration values we need. `tomli-w` is the only additional dependency (lightweight, pure Python).

**Schema**:
```toml
[general]
organization_id = 12345
timezone = "Europe/Berlin"

[defaults]
date_range_days = 30           # default filter range: today + N days
label_ids = [101, 102, 103]    # pre-selected labels on startup (empty = all)
```

**Alternatives Considered**:
- JSON (less human-friendly, no comments — rejected)
- YAML (additional dependency, more complex than needed — rejected)
- INI (no native list/integer types — rejected)

---

## R-007: Excel Export — Round-Trip Compatibility

**Task**: Determine export format to be compatible with existing `Runner` / `ExcelImporter`.

**Decision**: Use `openpyxl` to write `.xlsx` files with a header row matching the existing import column mapping. Include `groupalarm_id` (the appointment's API id) and `ga_importer_token` (the `ImporterToken` hash) as columns for update-not-duplicate behavior.

**Rationale**: The existing `ExcelImporter` reads `.xlsx` via openpyxl. The existing `Runner` uses `ImporterToken` to detect whether to create or update. Including both columns in the export ensures the round-trip works without manual intervention (Constitution V).

**Column Mapping** (matches existing `Mapper` field expectations):
| Column | Source |
|--------|--------|
| name | `appointment.name` |
| description | `appointment.description` |
| startDate | `appointment.startDate` (ISO 8601 in configured timezone) |
| endDate | `appointment.endDate` (ISO 8601 in configured timezone) |
| organizationID | `appointment.organizationID` |
| labelIDs | `appointment.labelIDs` (comma-separated) |
| isPublic | `appointment.isPublic` |
| reminder | `appointment.reminder` |
| notificationDate | `appointment.notificationDate` (ISO 8601 or empty) |
| feedbackDeadline | `appointment.feedbackDeadline` (ISO 8601 or empty) |
| timezone | `appointment.timezone` |
| groupalarm_id | `appointment.id` |
| ga_importer_token | computed `ImporterToken` hash |

**Alternatives Considered**:
- CSV export (less robust with special characters, no native date formatting — rejected as default, may add as option later)
- JSON export (not round-trip compatible with existing Runner — rejected)

---

## R-008: Delete Appointment — API Contract

**Task**: Confirm DELETE endpoint details and design the client method.

**Decision**: Add `delete_appointment(id, strategy, time)` to `GroupAlarmClient`.

**API Details** (from OpenAPI spec):
- Method: `DELETE /appointment/{id}`
- Query params:
  - `strategy`: `"single"` | `"upcoming"` | `"all"` (default: `"all"`)
  - `time`: ISO 8601 datetime (required when strategy is `"single"` or `"upcoming"` for recurring appointments)
- Response: `200` on success (no body), `500` on database error
- Auth: `Personal-Access-Token` header

**Rationale**: Directly maps to the OpenAPI spec. The `strategy` param handles the V1 requirement for recurring appointment deletion (FR-024). The `time` param specifies which occurrence to target.

**Alternatives Considered**: None — the API contract is fixed.

---

## R-009: Date/Time Input in Textual

**Task**: Determine how to handle date/time editing in the TUI (no built-in date picker in Textual).

**Decision**: Use `Input` widgets with `restrict` regex pattern and a custom `DateTimeValidator`. Display format: `YYYY-MM-DD HH:MM` in the configured timezone. Store and send as UTC ISO 8601.

**Rationale**: Textual has no built-in date picker. A restricted `Input` with validation is the simplest approach that works with both keyboard and mouse. The validator provides immediate feedback on invalid dates.

**Key Pattern**:
```python
Input(
    restrict=r"[0-9\-: ]",
    placeholder="YYYY-MM-DD HH:MM",
    validators=[DateTimeValidator(timezone=self.config.timezone)],
)
```

**Alternatives Considered**:
- Multi-field compound widget (year/month/day/hour/minute separately — more complex, harder to type — rejected for V1)
- Calendar popup widget (not available in Textual, would need custom implementation — deferred)

---

## R-010: Recurring Appointments — V1 Scope

**Task**: Clarify what recurrence data to display and how to handle update/delete for recurring appointments.

**Decision**: Display recurrence fields (frequency, interval, days, count/until) as read-only `Static` widgets in the detail panel. For update and delete operations, show a strategy selector (`OptionList` with "This occurrence only", "This and upcoming", "All occurrences"). Creating recurring appointments is out of scope for V1.

**Rationale**: The OpenAPI spec defines `AppointmentRecurrence` with `frequency`, `interval`, `days`, `count`, `until`, `week`, and `cancellations`. The API's PUT and DELETE endpoints accept a `strategy` query param. Displaying this info read-only and supporting strategy selection for mutations is the minimal viable scope per FR-025.

**Data Model Impact**: Add optional `recurrence: Optional[dict]` field to `Appointment` dataclass. Populate from API response but do not include in `to_api_payload()` for create operations (V1).

**Alternatives Considered**:
- Full recurrence editing (complex RRULE-like UI, high risk of errors, deferred to V2)
- Ignoring recurrence entirely (users need to know if an appointment recurs before deleting — rejected)

---

## R-011: Logging Infrastructure

**Task**: Determine logging approach for the TUI (FR-031).

**Decision**: Use Python's `logging` module with a `FileHandler` writing to `groupalarm_cli.log` in CWD. Default level `INFO`; `--verbose` flag sets level to `DEBUG`. A custom `logging.Filter` strips the API key from all log records.

**Rationale**: The stdlib `logging` module is the standard Python approach. File-based logging avoids polluting the TUI output. The custom filter ensures compliance with FR-016 (API key sanitization across all log sources).

**Key Patterns**:
```python
class ApiKeySanitizer(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if api_key and api_key in str(record.msg):
            record.msg = str(record.msg).replace(api_key, "***")
        return True
```

**Alternatives Considered**:
- Logging to stderr (would interfere with Textual's terminal — rejected)
- Structured JSON logging (overkill for V1 — rejected)
- No logging (user explicitly requested logging — rejected)

---

## R-012: Textual — Search & Sort in OptionList / DataTable

**Task**: Determine how to implement search filtering and sort toggling in the appointment list (FR-026).

**Decision**: Maintain the full appointment list in memory. Search applies a case-insensitive substring match on name and description, rebuilding the displayed list. Sort toggles between start date ascending (default) and name alphabetical. Use `DataTable` (not `OptionList`) for built-in column header support.

**Rationale**: `DataTable` supports `sort()` by column key. Filtering is done at the data level by clearing and re-adding rows. `Ctrl+F` binding opens a search `Input` above the list; `Esc` clears the search.

**Alternatives Considered**:
- Server-side search (API has no search param for appointments — not available)
- Fuzzy matching (unnecessary complexity for V1 — rejected)

---

## R-013: Textual — Unsaved Changes Guard

**Task**: Determine how to detect and prompt for unsaved changes when navigating away (FR-029).

**Decision**: Track a `dirty` flag on the detail panel. Set `dirty = True` when any `Input.Changed` event fires. Reset on successful save or explicit discard. On list selection change or quit, check `dirty` and push a `ModalScreen` with Save/Discard/Cancel options.

**Rationale**: Textual's `Input.Changed` event reliably fires on every change. A simple boolean flag is sufficient since the detail panel always shows exactly one appointment. The three-way modal (Save/Discard/Cancel) is the standard UX pattern.

**Key Pattern**:
```python
class UnsavedChangesDialog(ModalScreen[str]):
    # dismiss with "save", "discard", or "cancel"
```

**Alternatives Considered**:
- Deep comparison of form state vs. original (more complex, unnecessary when a simple flag works — rejected)
- Auto-save (violates Constitution II — rejected)

---

## R-014: Graceful Shutdown & Ctrl+C Handling

**Task**: Determine how Textual handles Ctrl+C and how to add unsaved changes protection on quit (FR-032).

**Decision**: Override `App.action_quit()` to check for unsaved changes and in-flight workers before exiting. Textual catches `KeyboardInterrupt` internally; bind `ctrl+c` as a custom binding that triggers the same quit flow.

**Rationale**: Textual does not terminate on Ctrl+C by default — it treats it as a key event. This allows interception and graceful handling. In-flight `@work` threads can be cancelled via `worker.cancel()`.

**Key Pattern**:
```python
def action_quit(self) -> None:
    if self.detail_panel.dirty:
        self.push_screen(UnsavedChangesDialog(), self._handle_quit_response)
    else:
        self.exit()
```

**Alternatives Considered**:
- Ignoring Ctrl+C entirely (poor UX — rejected)
- Immediate exit with atexit handler (can't show modal — rejected)
