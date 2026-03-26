# Feature Specification: Interactive CLI TUI for GroupAlarm Appointment Management

**Feature Branch**: `001-interactive-cli-tui`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "Update this tool to a nice visual CLI Tool to update and manage the appointments in GroupAlarm. The CLI should do the same as the framework can do, with interactive editing, split view terminal, filtering by labels and time, Excel export for re-upload, API key from GROUPALARM_API_KEY env var, and explicit confirmation for all server changes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Browse & Filter Appointments (Priority: P1)

As a GroupAlarm administrator, I want to launch the CLI and immediately see a list of my organization's appointments so I can quickly find the ones I need to work with. I must be able to filter by label and by start/end date range to narrow down results.

**Why this priority**: Browsing and filtering is the foundational interaction — every other story (editing, exporting, creating) depends on being able to see and select appointments first. Without this, the tool has no value.

**Independent Test**: Launch the CLI, verify the appointment list is populated from the API, apply a label filter, verify only matching appointments remain visible, apply a date range filter, verify the list narrows further.

**Acceptance Scenarios**:

1. **Given** the `GROUPALARM_API_KEY` environment variable is set and valid, **When** the user launches the CLI, **Then** the tool displays a scrollable list of appointments showing name, start date, end date, and labels, filtered to the configured default date range (today + 1 month) and default labels (if set in config).
2. **Given** the appointment list is visible, **When** the user activates the label filter and selects one or more labels, **Then** only appointments tagged with at least one of the selected labels are shown. The filter presents all available labels fetched from the API as a selectable list.
3. **Given** the appointment list is visible, **When** the user sets a start-date and/or end-date filter, **Then** only appointments whose time range overlaps the filter are shown.
4. **Given** filters are active, **When** the user clears a filter, **Then** the list returns to the previous unfiltered (or less-filtered) state immediately.
5. **Given** the `GROUPALARM_API_KEY` environment variable is not set, **When** the user launches the CLI, **Then** an error message with setup instructions is displayed and the tool exits.

---

### User Story 2 — View & Edit a Single Appointment (Priority: P2)

As an administrator, I want to select an appointment from the list and see all its details in a side panel. I then want to edit any field (name, description, dates, labels, reminder, visibility, etc.) inline, preview my changes, and confirm before they are sent to the server.

**Why this priority**: Editing is the core management action. Once a user can browse (P1), editing individual appointments is the next most valuable capability. It replaces the current workflow of editing CSV files and re-running the import script.

**Independent Test**: Select an appointment, verify all fields are displayed in the detail panel, edit the name field, verify the confirmation dialog shows the diff, confirm, verify the change is sent to the server.

**Acceptance Scenarios**:

1. **Given** the appointment list is visible, **When** the user selects an appointment, **Then** a detail panel opens alongside the list showing all editable fields (name, description, start date, end date, labels, reminder, notification date, feedback deadline, visibility, participants).
2. **Given** the detail panel is open, **When** the user modifies one or more fields, **Then** the changed fields are visually highlighted to indicate unsaved changes.
3. **Given** the user has unsaved changes, **When** the user triggers "save", **Then** a confirmation dialog appears showing a summary of all pending changes (old value → new value for each modified field).
4. **Given** the confirmation dialog is displayed, **When** the user confirms, **Then** the update is sent to the server, the detail panel refreshes with the server response, and a success indicator is shown.
5. **Given** the confirmation dialog is displayed, **When** the user cancels, **Then** no server request is made and the user returns to the editing state with changes preserved.
6. **Given** the user is editing, **When** the user presses a "discard" key, **Then** all local changes are reverted to the server-side values.

---

### User Story 3 — Export Appointments to Excel (Priority: P3)

As an administrator, I want to export a filtered set of appointments to an Excel file that is fully compatible with the existing CSV/Excel import pipeline, so I can edit appointments offline in a spreadsheet and re-upload them later.

**Why this priority**: Export closes the round-trip loop. Users already have the import pipeline; export enables the offline bulk-editing workflow that is critical for planning sessions with many appointments.

**Independent Test**: Filter the list to a subset, trigger export, verify the generated `.xlsx` file contains all required columns (including `groupalarm_id` and `ga_importer_token`), open the file in a spreadsheet application, re-import it using the existing `Runner` and verify no duplicate appointments are created.

**Acceptance Scenarios**:

1. **Given** the appointment list is filtered, **When** the user triggers the export action, **Then** the tool prompts for a file path (with a sensible default).
2. **Given** a file path is provided, **When** the export runs, **Then** an `.xlsx` file is created containing one row per visible appointment with columns: name, description, startDate, endDate, organizationID, labelIDs, reminder, notificationDate, feedbackDeadline, isPublic, groupalarm_id, ga_importer_token.
3. **Given** the exported file exists, **When** a user passes it to the existing `Runner` with an appropriate mapping, **Then** appointments are updated (not duplicated) because `groupalarm_id` and `ga_importer_token` columns are present.
4. **Given** no appointments match the current filter, **When** the user triggers export, **Then** the tool shows a message "No appointments to export" and does not create a file.

---

### User Story 4 — Create a New Appointment (Priority: P4)

As an administrator, I want to create a brand-new appointment from within the CLI by filling in the required fields, reviewing the payload, and confirming before it is sent to the server.

**Why this priority**: Creation is valuable but less frequent than browsing or editing existing appointments. It builds on the same editing UI from P2.

**Independent Test**: Trigger "new appointment", fill in name, description, start/end dates, organization, confirm, verify the appointment appears on the server and in the list.

**Acceptance Scenarios**:

1. **Given** the CLI is running, **When** the user triggers "create new appointment", **Then** the detail panel opens with empty fields and sensible defaults (start = now rounded to next full hour, end = start + configured default duration [default: 4 hours], organization = user's configured default).
2. **Given** the user has filled in all required fields, **When** the user triggers "save", **Then** a confirmation dialog shows the full payload for review.
3. **Given** the user confirms, **Then** the appointment is created on the server, the returned `id` and an importer token are captured, and the new appointment appears in the list.
4. **Given** required fields are missing (e.g., no name or no dates), **When** the user triggers "save", **Then** a validation error is displayed indicating which fields are missing.

---

### User Story 5 — Delete an Appointment (Priority: P5)

As an administrator, I want to delete an appointment from the CLI with a clear confirmation step to prevent accidental removal.

**Why this priority**: Deletion is the least frequent action and the riskiest; it is valuable but can be deferred after all other capabilities are in place.

**Independent Test**: Select an appointment, trigger delete, verify confirmation dialog shows the appointment name and dates, confirm, verify the appointment is removed from the server and disappears from the list.

**Acceptance Scenarios**:

1. **Given** an appointment is selected, **When** the user triggers "delete", **Then** a confirmation dialog appears with the appointment name, date range, and a warning that this action cannot be undone. For recurring appointments, the dialog additionally asks which occurrences to delete (single, upcoming, or all).
2. **Given** the confirmation dialog is displayed, **When** the user confirms, **Then** the appointment is deleted from the server and removed from the list with a success message.
3. **Given** the confirmation dialog is displayed, **When** the user cancels, **Then** no server request is made and the appointment remains.

---

### Edge Cases

- What happens when the API returns a network error during an operation? → The tool displays the error message, preserves any unsaved local changes, and allows the user to retry.
- What happens when another user modifies or deletes an appointment between the time it was loaded and the time the user saves? → The tool displays the server error (409 conflict or 404 not found) and prompts the user to refresh the list.
- What happens when the appointment list is empty (no appointments exist for the organization)? → The tool displays an empty-state message with a hint to create a new appointment.
- What happens when the user resizes the terminal to a very small size? → The layout gracefully degrades (e.g., stacks panels vertically or hides the detail panel with a hint to enlarge).
- What happens when filtering yields zero results? → The list shows a "No matching appointments" message and the filters remain visible for adjustment.
- What happens when the user edits the start date to be after the end date? → Inline validation prevents saving and highlights the invalid field.
- What happens when the user tries to create a recurring appointment? → The recurrence fields are not shown in the create form (V1 limitation). A hint indicates that recurring appointments can only be created via the GroupAlarm web UI.
- What happens when `default_label_ids` in the config reference labels that no longer exist in the API? → The invalid IDs are silently ignored; only valid labels are pre-selected. A warning is logged.
- What happens when the config file (`.groupalarm.toml`) is corrupted or contains invalid TOML? → A clear error message is displayed with the parse error details and the file path, and the tool exits with instructions to fix or delete the file.
- What happens when the label API call fails at startup? → The label filter is disabled with a warning message. Appointments are still loaded and displayed. The user can retry via the refresh action.
- What happens when an API call returns a rate-limiting response (429)? → No API rate limiting is expected from GroupAlarm's API. Standard HTTP error handling applies.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI MUST read the API key exclusively from the `GROUPALARM_API_KEY` environment variable. If unset, the tool MUST exit with a descriptive error and setup instructions.
- **FR-002**: The CLI MUST display a scrollable, filterable list of appointments retrieved from the GroupAlarm API.
- **FR-003**: Users MUST be able to filter the appointment list by one or more labels. The label filter MUST present labels as a toggle list showing label name and color indicator, navigable with arrow keys and selectable with spacebar. A typeahead search MUST be available to quickly find labels when many exist.
- **FR-004**: Users MUST be able to filter the appointment list by a start-date and/or end-date range.
- **FR-005**: The CLI MUST provide a split-view layout with the appointment list on one side and a detail/edit panel on the other.
- **FR-006**: Users MUST be able to select an appointment and view all its fields in the detail panel.
- **FR-007**: Users MUST be able to edit any appointment field in the detail panel (name, description, start/end dates, labels, reminder, notification date, feedback deadline, visibility). Labels MUST be displayed by name and color (never as raw IDs) and edited via a selectable picker with typeahead search. Participants are displayed read-only (showing names, not IDs) since labels are the primary assignment mechanism.
- **FR-008**: Every server-side mutation (create, update, delete) MUST require explicit user confirmation via a dialog that shows a human-readable summary of the pending changes.
- **FR-009**: For updates, the confirmation dialog MUST show a field-by-field diff in a side-by-side table format (old value → new value) with changed fields highlighted. For creates, the dialog MUST show a structured summary of the new appointment payload. For deletes, the dialog MUST show the appointment name, date range, and a clear irreversibility warning.
- **FR-010**: Users MUST be able to cancel any confirmation dialog without triggering a server request.
- **FR-011**: Users MUST be able to export the currently filtered appointments to an `.xlsx` file. The default filename MUST be `appointments_YYYY-MM-DD.xlsx` in the current working directory. If the file already exists, the tool MUST prompt the user to confirm overwriting or auto-generate a unique filename by appending a counter (e.g., `appointments_2026-03-22_1.xlsx`).
- **FR-012**: The exported file MUST include `groupalarm_id` and `ga_importer_token` columns so it can be re-imported by the existing framework `Runner` without creating duplicates.
- **FR-013**: Users MUST be able to create a new appointment from within the CLI.
- **FR-014**: Users MUST be able to delete an appointment from within the CLI, with a confirmation step that warns the action is irreversible.
- **FR-015**: The CLI MUST validate appointment fields locally before attempting server requests (e.g., end date after start date, required fields present).
- **FR-016**: The API key MUST NOT appear in any form of logging or error reporting, including: Python's logging module output, Textual's debug logs, crash dumps, stack traces from `requests` exceptions, exported files, or any user-visible output. API key values MUST be sanitized from exception messages before logging or display.
- **FR-017**: The CLI MUST support keyboard navigation (arrow keys + shortcuts) and mouse interaction (click, scroll). A persistent footer bar MUST display contextual key hints for available actions. Pressing `?` MUST open a help overlay listing all key bindings. Vim-style bindings are explicitly excluded.
- **FR-018**: The CLI MUST support a `--dry-run` flag that prevents all server-side mutations and logs the payloads that would be sent. In dry-run mode, the TUI MUST display a persistent banner at the top of the screen (e.g., "Dry Run Mode: No changes will be sent to the server") and planned mutation payloads MUST be visually distinguished (e.g., yellow text).
- **FR-019**: All datetime values MUST be displayed in the user's configured timezone (default: `Europe/Berlin`) and sent to the API in UTC/ISO 8601 format.
- **FR-020**: The TUI MUST be built with the Textual framework (CSS-based layouts, built-in widget library, async event loop, native mouse and keyboard support).
- **FR-021**: The CLI MUST persist the organization ID in a local config file (e.g., `.groupalarm.toml`). If the config file does not exist or the org ID is missing, the CLI MUST prompt the user to set it on first launch. The org ID can also be overridden via a `--org-id` CLI argument.
- **FR-022**: The config file MUST support configurable defaults for: date range window (default: 1 month from today), default filter labels (list of label IDs to pre-select on startup), and default appointment duration in hours (default: 4). These defaults are applied on every launch but can be changed interactively during the session. Default label IDs from the config MUST be validated against labels fetched from the API at startup; invalid IDs are silently ignored with a logged warning.
- **FR-023**: The label filter MUST fetch available labels from the GroupAlarm API and present them as a selectable list (with name and color). Users pick from real labels rather than typing IDs manually.
- **FR-024**: The CLI MUST support deleting appointments via a new `delete_appointment` method on `GroupAlarmClient` (using `DELETE /appointment/{id}`). For recurring appointments, the delete confirmation MUST let the user choose the recurrence strategy: delete this occurrence only (single), this and all upcoming (upcoming), or all occurrences (all).
- **FR-025**: Recurring appointments MUST display their recurrence pattern (frequency, interval, days, count/until) as read-only information in human-readable form (e.g., "Every 2 weeks on Mon, Wed") in the detail panel. Update and delete operations on recurring appointments MUST present the strategy selector (single/upcoming/all). Creating new recurring appointments is explicitly out of scope for V1.
- **FR-026**: The appointment list MUST be sorted by start date ascending by default. Users SHOULD be able to toggle sort order (ascending/descending) and sort by other fields (name). A search function MUST be available to filter the list by text matching on appointment name or description.
- **FR-027**: After any successful server mutation (create, update, delete), the appointment list MUST be refreshed by re-fetching from the API to reflect the current server state.
- **FR-028**: When no appointment is selected, the detail panel SHOULD display a help/how-to overview of available actions and key bindings (if implementable without significant extra effort). The user MUST be able to re-display this help via `?`.
- **FR-029**: If the user attempts to navigate away from an appointment with unsaved changes (selecting another appointment, quitting, or pressing Escape), the CLI MUST prompt with a confirmation dialog offering to save, discard, or cancel the navigation.
- **FR-030**: While an API call is in-flight, UI interactions that would trigger additional API calls MUST be disabled and a loading indicator MUST be shown. If the user attempts a new action during an in-flight call, the action is queued or blocked with a visual indicator.
- **FR-031**: All significant events (API calls, mutations, errors, startup/shutdown) MUST be logged to a file using Python's logging module. Log levels: INFO for successful operations, WARNING for recoverable issues (e.g., invalid config label IDs), ERROR for failures. A `--verbose` flag SHOULD enable DEBUG-level logging for troubleshooting. Logs MUST NOT contain the API key (see FR-016).
- **FR-032**: On Ctrl+C or quit (`q`), the CLI MUST attempt graceful shutdown: cancel any in-flight API calls, prompt for unsaved changes (per FR-029), and return to a stable state. If Ctrl+C is pressed during an API call, the operation is cancelled and the TUI returns to a usable state without crashing.
- **FR-033**: The `.groupalarm.toml` config file MUST be created with restrictive file permissions (600 on Unix) to prevent unauthorized read access. The config file MUST NOT contain any sensitive data (API key); only non-sensitive settings (org ID, display preferences, defaults).
- **FR-034**: Long appointment names or descriptions in the list view MUST be truncated with ellipses. The full text MUST be visible in the detail panel when the appointment is selected.
- **FR-035**: Unsaved changes in the detail panel MUST be visually indicated by a distinct background color on modified fields and a modification indicator (e.g., asterisk) next to the field label. The footer bar MUST show a hint that unsaved changes exist.

### Key Entities

- **Appointment**: A scheduled event in GroupAlarm. Key attributes: id, name, description, start date, end date, organization ID, label IDs, visibility (public/private), reminder (minutes), notification date, feedback deadline, participants, importer token, recurrence (read-only in V1: frequency, interval, days, count/until). An appointment belongs to one organization and can have multiple labels.
- **Label**: A tag used to categorize appointments and link participant groups. Key attributes: id, name, color. Labels are managed externally in GroupAlarm configuration; the CLI uses them for filtering and assignment.
- **Organization**: The GroupAlarm tenant to which appointments belong. Key attribute: id. Typically fixed for a given user/deployment.
- **Export File**: An Excel workbook containing appointment data in a format compatible with the existing import pipeline. Must include `groupalarm_id` and `ga_importer_token` columns for round-trip support.

## Assumptions

- The user has a single organization context at a time. The `organizationID` is stored in a local config file (e.g., `.groupalarm.toml`) and can be overridden via `--org-id`.
- Labels are fetched from the API and cached for the session; they do not change frequently during a single CLI session. Available labels are displayed in the filter UI for selection.
- The GroupAlarm API supports listing, creating, updating, and deleting appointments via the documented REST endpoints.
- The existing `framework/` library (`GroupAlarmClient`, `Appointment`, `Mapper`, importers, `ImporterToken`) is stable and will be extended, not replaced.
- The user's terminal supports 256 colors and Unicode (standard for modern terminals on Windows, macOS, and Linux).
- The TUI is built with the Textual framework, which provides the split-view layout, scrollable widgets, footer bar, and async event handling required by this spec.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can find a specific appointment by label and date range within 30 seconds of launching the CLI.
- **SC-002**: Users can edit and save a single appointment field in under 1 minute (including confirmation).
- **SC-003**: Users can export 100 filtered appointments to Excel in under 10 seconds.
- **SC-004**: The exported Excel file can be re-imported by the existing `Runner` with zero manual modifications, producing zero duplicate appointments.
- **SC-005**: 100% of server-side mutations display a confirmation dialog before execution; no mutation bypasses confirmation.
- **SC-006**: The tool starts and displays the appointment list within 5 seconds on a standard internet connection.
- **SC-007**: Users can discover all available actions (filter, edit, save, export, create, delete) without consulting documentation, via a persistent footer bar showing contextual key hints and a `?` help overlay.

## Clarifications

### Session 2026-03-22

- Q: Input model (keyboard-only, mouse, vim bindings)? → A: Keyboard (arrow keys + shortcuts) + mouse (click, scroll). Footer bar with contextual key hints. `?` opens help overlay. No vim-style bindings.
- Q: TUI framework choice? → A: Textual (modern async Python TUI framework with CSS-based layouts, built-in widgets, native mouse/keyboard support).
- Q: How should the CLI determine which organization to use? → A: Store org ID in a local config file (e.g., `.groupalarm.toml`). Persists across sessions.
- Q: Default date range on startup? → A: Today + 1 month. Configurable in the config file alongside default filter labels. The label filter MUST show available labels fetched from the API.
- Q: Delete API endpoint availability? → A: `DELETE /appointment/{id}` exists in the OpenAPI spec with `strategy` (single/upcoming/all) and `time` query params for recurring appointments. Add `delete_appointment` to `GroupAlarmClient`.
- Q: Recurring appointments scope? → A: V1 displays recurrence info read-only, supports update/delete with strategy selector (single/upcoming/all), but creating new recurring appointments is deferred to V2.

### Quality Review Session 2026-03-22

- Q: Label filter interaction mechanics? → A: Toggle list with label names + color indicators. Arrow keys to navigate, spacebar to select/deselect. Typeahead search for quick filtering when many labels exist.
- Q: Default appointment duration for create? → A: 4 hours (configurable in `.groupalarm.toml` under `[defaults] appointment_duration_hours`).
- Q: Dry-run visual indicator? → A: Persistent banner at top ("Dry Run Mode: No changes will be sent to the server") and planned changes displayed in yellow.
- Q: Sort order for appointment list? → A: Start date ascending by default. Toggleable sort direction. Search function for text matching on name/description.
- Q: Unsaved changes protection? → A: Prompt with save/discard/cancel when navigating away from unsaved edits, switching appointments, or quitting.
- Q: Concurrent API call handling? → A: Disable triggering UI actions while API call in-flight, show loading indicator.
- Q: Logging requirements? → A: INFO for successes, ERROR for failures, WARNING for recoverable issues. File-based logging via Python logging module. `--verbose` for DEBUG. No API key in any log output.
- Q: Graceful shutdown? → A: Ctrl+C cancels in-flight API call, returns to stable state. Quit with unsaved changes triggers confirmation prompt.
- Q: Config file security? → A: File permissions 600 on Unix. No sensitive data (API key) in config file.
- Q: API key in stack traces? → A: Sanitize API key from all exception messages, stack traces, and log output before display or logging.
- Q: After single-occurrence recurring delete, refresh behavior? → A: Full list refresh from API.
- Q: Label refresh during session? → A: Labels are fetched once on startup and cached. No mid-session refresh needed (labels change rarely).
