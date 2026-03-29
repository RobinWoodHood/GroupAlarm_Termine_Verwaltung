# Feature Specification: TUI Excel Import with Preview and Upload

**Feature Branch**: `004-tui-excel-import`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: User description: "I need an Import function similar to the import function of the previous framework. So that I can use different excels for the import and define via the config file the matching. The excel this TUI can export at least must be usable for the import. After the excel is imported I need a preview before the appointments are updated or created if not existing. This preview must be with different colors but the same UI as the existing one. So all text must be red and at the top it must be clearly written that this is a preview of the import. Then I must be able to go up and down with the arrow keys and see on the right the details of each appointment. I don't need the edit mode here. But I need the filter for time and label and search. After finishing the preview I need a shortcut to upload the list. Then I need a summary which changes were made successfully or not. In this summary I need a list of appointments which were not updated successfully."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Import Excel and Preview Appointments (Priority: P1)

As a user, I want to import an Excel file into the TUI and immediately see a read-only preview of all parsed appointments in the same list+detail layout I already know, but styled in red with a clear banner so I can verify the data before anything is sent to GroupAlarm.

**Why this priority**: Without the ability to load and preview an Excel file, no other import workflow step (upload, summary) is possible. This is the foundational slice that delivers immediate value — the user can already verify data visually.

**Independent Test**: Can be fully tested by importing an Excel file and visually confirming that the preview screen shows all appointments with red styling, the "IMPORT PREVIEW" banner is visible, arrow-key navigation works, and the detail panel shows each appointment's fields. No server interaction is required.

**Acceptance Scenarios**:

1. **Given** the TUI is running and the user triggers the import action, **When** the user selects a valid Excel file, **Then** the TUI switches to a preview screen that shows all parsed appointments in a list with red-coloured text and a prominent "IMPORT PREVIEW" banner at the top.
2. **Given** the preview screen is displayed, **When** the user presses Up/Down arrow keys, **Then** the appointment list cursor moves and the detail panel on the right updates to show the highlighted appointment's full details (name, description, start, end, labels, etc.).
3. **Given** the preview screen is displayed, **When** the user uses the filter controls (date range, label toggles, search text), **Then** the appointment list updates to show only matching appointments from the imported data.
4. **Given** the user selects an Excel file that was previously exported by the TUI, **Then** the import parses all columns correctly and displays the appointments in the preview without errors.
5. **Given** the user selects an Excel file with missing or malformed rows, **Then** the preview shows only the successfully parsed rows and displays a notification about skipped rows (count and reason).

---

### User Story 2 — Python Mapping Module for Custom Imports (Priority: P1)

As a user, I want to point the config at an existing Python mapping file (like `Bereichsausbildungen_productive.py`) so I can import Excel/CSV files with arbitrary layouts using the full power of `Mapper` — lambdas, multi-column templates, label-token mapping, custom date formats, and relative dates — without any code changes to the TUI.

**Why this priority**: Real-world imports require complex transformations that cannot be expressed in TOML. Users already have working Python mapping files for the framework's `Runner`; reusing them in the TUI is the fastest path to value and satisfies Constitution Principle IV (Framework Reuse).

**Independent Test**: Can be fully tested by setting `mapping_file` in `.groupalarm.toml`, importing a non-standard Excel/CSV file, and verifying that the preview correctly shows appointments transformed by the Python mapping module.

**Acceptance Scenarios**:

1. **Given** no `[import]` section exists in the config file, **When** the user imports an Excel with the TUI's own export column layout, **Then** the import works with the built-in default mapping (Tier 1 — zero-config round-trip).
2. **Given** the user has set `mapping_file = "mappings/bereichsausbildungen.py"` in the `[import]` section, **When** the user imports a file, **Then** the system loads `mapping` and `defaults` dicts from that Python module and uses them with `Mapper` to transform rows into appointments.
3. **Given** the Python mapping module uses lambdas (e.g. `"name": lambda r, helpers: f"{r['Nr']} {r['Lehrgang']}"`), **Then** the import correctly evaluates them for each row.
4. **Given** the Python mapping module uses `map_labels_from_participants()` for label resolution, **Then** label IDs are correctly resolved from participant tokens.
5. **Given** the Python mapping module uses `helpers["parse_date"]()` with a custom format string, **Then** dates are parsed correctly using that format.
6. **Given** the Python mapping module uses `{"days_before": 5}` for `notificationDate`, **Then** the notification date is computed relative to `startDate`.
7. **Given** the mapping file path in the config does not exist or has syntax errors, **Then** the system reports a clear error identifying the problem.

---

### User Story 5 — Interactive Column Mapper Wizard (Priority: P3, Future)

As a user, I want a step-by-step wizard in the TUI that guides me through mapping Excel columns to appointment fields so I can create a mapping for a new file format without writing Python code.

**Why this priority**: This is a convenience enhancement for users who are not comfortable writing Python mapping files. The core import functionality (Tier 1 + Tier 2) must be complete first.

**Independent Test**: Can be tested by triggering the wizard from the import dialog when no mapping is configured for a non-standard file, completing the wizard steps, and verifying the generated mapping produces correct appointments in preview.

**Acceptance Scenarios**:

1. **Given** the user imports a non-standard Excel file with no `mapping_file` configured and the columns don't match the default mapping, **When** the import detects unrecognized columns, **Then** the system offers to launch the column mapper wizard.
2. **Given** the wizard is launched, **Then** it presents each required appointment field and lets the user select which Excel column maps to it (or set a literal value).
3. **Given** the wizard is completed, **Then** a Python mapping file is generated and saved, and the config is updated to reference it for future imports.
4. **Given** the user cancels the wizard, **Then** the import is cancelled and no files are modified.

---

### User Story 3 — Upload Imported Appointments (Priority: P3)

As a user, after verifying the preview I want to press a keyboard shortcut to upload all imported appointments to GroupAlarm, where existing appointments are updated and new ones are created.

**Why this priority**: The preview alone is read-only; the upload step completes the write-path and delivers the core value of bulk-managing appointments.

**Independent Test**: Can be fully tested (in dry-run mode) by importing an Excel, confirming the preview, pressing the upload shortcut, and verifying that the correct create/update API calls are logged.

**Acceptance Scenarios**:

1. **Given** the user is on the import preview screen, **When** the user presses the upload shortcut (Ctrl+U), **Then** the system begins uploading appointments to GroupAlarm — updating those with an existing `groupalarm_id` and creating new ones without an id.
2. **Given** an appointment in the import has a `groupalarm_id` that matches a server appointment, **When** the upload runs, **Then** that appointment is updated via the API.
3. **Given** an appointment in the import has no `groupalarm_id`, **When** the upload runs, **Then** that appointment is created via the API and an importer token is appended to its description.
4. **Given** the TUI is in dry-run mode, **When** the user presses the upload shortcut, **Then** no actual API calls are made and the summary shows dry-run results.

---

### User Story 4 — Upload Summary with Error Details (Priority: P4)

As a user, after upload completes I want to see a summary screen showing how many appointments were created, how many were updated, and a list of any that failed — so I can take corrective action.

**Why this priority**: Without a summary the user has no feedback on what actually happened. This story closes the feedback loop.

**Independent Test**: Can be fully tested by triggering an upload that includes appointments expected to succeed and at least one expected to fail (e.g. invalid data), then verifying the summary shows correct counts and lists the failed appointment with its error.

**Acceptance Scenarios**:

1. **Given** the upload has completed, **Then** a summary screen appears showing total appointments processed, number successfully created, number successfully updated, and number failed.
2. **Given** one or more appointments failed during upload, **Then** the summary lists each failed appointment by name with the reason for failure.
3. **Given** all appointments uploaded successfully, **Then** the summary confirms full success and the failure list is empty.
4. **Given** the summary is displayed, **When** the user presses Escape or Enter, **Then** the TUI returns to the normal appointment view (reloading the latest server data).

---

### Edge Cases

- What happens when the selected file is not a valid Excel file? → The system displays an error notification and returns to the normal view without entering the preview.
- What happens when the Excel file is empty (no data rows)? → The system displays a notification "No appointments found in file" and does not enter the preview.
- What happens when the user cancels the import preview without uploading? → The system returns to the normal appointment view; no data is modified.
- What happens when the network is unavailable during upload? → Each failed appointment is added to the failure list in the summary with the network error as the reason.
- What happens when an appointment's `groupalarm_id` references a server appointment that no longer exists? → The system falls back to creating it as a new appointment (same as the existing runner's token-based fallback behaviour).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a keyboard shortcut (Ctrl+O) on the main screen to initiate an Excel import.
- **FR-002**: System MUST prompt the user to enter or select the path to the Excel file to import.
- **FR-003**: System MUST parse the Excel file and map rows to `Appointment` objects using a three-tier mapping strategy: (1) built-in default mapping for TUI export format, (2) Python mapping module referenced from config, (3) interactive wizard (future).
- **FR-004**: When no custom `[import]` section is configured (Tier 1), the system MUST use a built-in default mapping that matches the TUI's own export column layout (name, description, startDate, endDate, organizationID, labelIDs, isPublic, reminder, notificationDate, feedbackDeadline, timezone, groupalarm_id, ga_importer_token).
- **FR-005**: System MUST allow the user to set `mapping_file` in the `[import]` section of `.groupalarm.toml` pointing to a Python module that exports a `mapping` dict (and optional `defaults` dict) compatible with the `Mapper` class (Tier 2).
- **FR-006**: When a `mapping_file` is configured, the system MUST load the Python module dynamically, extract its `mapping` and `defaults` dicts, and use the existing `Mapper` class to transform rows — supporting lambdas, template strings, `map_labels_from_participants()`, `parse_date()` with custom formats, `{"days_before": N}` relative dates, and literal constants.
- **FR-007**: After parsing, the system MUST display a dedicated import preview screen that reuses the existing list+detail split layout (AppointmentList on the left, DetailPanel on the right).
- **FR-008**: The import preview screen MUST display a prominent banner at the top reading "IMPORT PREVIEW" to distinguish it from the normal appointment view.
- **FR-009**: All text in the import preview list MUST be rendered in red to visually distinguish imported data from live server data.
- **FR-010**: The import preview MUST support Up/Down arrow key navigation to move through the appointment list, with the detail panel updating to show the currently highlighted appointment.
- **FR-011**: The import preview MUST NOT provide edit mode capabilities — the detail panel is read-only.
- **FR-012**: The import preview MUST support the same filter controls as the main screen: date range filtering, label toggles, and text search.
- **FR-013**: System MUST provide a keyboard shortcut (Ctrl+U) on the import preview screen to begin uploading all imported appointments to GroupAlarm.
- **FR-014**: During upload, the system MUST update appointments that have an existing `groupalarm_id` and create new appointments for those without one.
- **FR-015**: For newly created appointments, the system MUST append an importer token (GA-IMPORTER) to the description, consistent with the existing runner behaviour.
- **FR-016**: After upload completes, the system MUST display a summary screen showing: total processed, successfully created count, successfully updated count, and failed count.
- **FR-017**: The summary screen MUST list each failed appointment by name with a human-readable error reason.
- **FR-018**: From the summary screen, the user MUST be able to dismiss it (Escape or Enter) to return to the normal appointment view with refreshed server data.
- **FR-019**: If parsing encounters rows with missing required data, the system MUST skip those rows, count them, and display a notification about skipped rows before entering the preview.
- **FR-020**: The user MUST be able to cancel the import preview at any time (Escape) without any data being sent to the server.
- **FR-021**: When the TUI is running in dry-run mode, the upload shortcut MUST log API payloads instead of making real API calls, and the summary MUST indicate dry-run results.

### Key Entities

- **Import Session**: A transient collection of appointments parsed from an Excel file, including metadata about the source file path, parse errors (skipped rows), and the column mapping used. Exists only during the import preview workflow.
- **Column Mapping**: A three-tier strategy for resolving how Excel columns map to appointment fields. **Tier 1**: built-in default mapping matching the TUI export format. **Tier 2**: a Python mapping module (`.py` file) referenced from `[import].mapping_file` in `.groupalarm.toml`, exporting a `mapping` dict compatible with the `Mapper` class. **Tier 3** (future): an interactive TUI wizard that generates a mapping file.
- **Upload Result**: Per-appointment outcome of the upload operation — records whether each appointment was created, updated, or failed, along with the error reason for failures.
- **Import Summary**: An aggregate view of all upload results — total count, created count, updated count, failed count, and the list of failed items with their errors.

## Assumptions

- The Excel file contains one worksheet; the first sheet is used unless otherwise configured.
- Date values in Excel follow either ISO 8601 format (as used by the TUI export) or the format/logic specified in the Python mapping module.
- The `organizationID` for imported appointments defaults to the value from `[general].organization_id` in the config file when not present in the Excel or mapping module.
- Label IDs in Tier 1 are stored as a comma-separated string (matching the export format). In Tier 2, label resolution is handled by the mapping module (e.g. `map_labels_from_participants()`).
- Python mapping modules are trusted user-provided files (same trust level as the existing `Bereichsausbildungen_productive.py` scripts). The system does not sandbox their execution.
- The upload shortcut triggers processing of the full filtered list visible in the preview at the time of pressing the shortcut.
- Network errors and API errors are caught per-appointment so one failure does not abort the remaining uploads.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can import an Excel file and see a complete preview of all valid appointments within 5 seconds for files up to 500 rows.
- **SC-002**: The import preview accurately renders 100% of fields from an Excel file previously exported by the TUI.
- **SC-003**: Users can visually distinguish the import preview from the normal view immediately — the red styling and banner are visible without scrolling.
- **SC-004**: Users can navigate the full import preview (arrow keys, filters, search, detail view) without encountering any mode where editing is possible.
- **SC-005**: After upload, the summary correctly reports the outcome of every appointment — no appointment is silently lost or unaccounted for.
- **SC-006**: Users can complete the full import-preview-upload-summary workflow in under 2 minutes for a typical file of 50 appointments.
- **SC-007**: Existing Python mapping files (e.g. `Bereichsausbildungen_productive.py`) can be referenced from the config and used to import non-standard Excel/CSV files without code changes to the TUI.
