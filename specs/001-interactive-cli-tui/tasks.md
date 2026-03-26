# Tasks: Interactive CLI TUI for GroupAlarm Appointment Management

**Input**: Design documents from `/specs/001-interactive-cli-tui/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Tests ARE included — Constitution Principle VI (Test Discipline) mandates unit tests for all new modules, and the spec explicitly requires pytest with monkeypatch + Textual pilot tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and directory scaffolding

- [X] T001 Update requirements.txt with new dependencies: textual, tomli-w, openpyxl (requests and pandas already present)
- [X] T002 Create project directory structure: cli/, cli/screens/, cli/widgets/, cli/services/, cli/styles/ with __init__.py files
- [X] T003 [P] Create CLI entry point script in groupalarm_cli.py with argparse (--org-id, --dry-run, --verbose) and GROUPALARM_API_KEY env var check per contracts/cli-application.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core framework extensions and infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Extend Appointment dataclass with optional `recurrence: Optional[Dict]` field in framework/appointment.py (read-only, not included in to_api_payload for creates) per data-model.md
- [X] T005 [P] Add `list_labels(organization_id, label_type)` method to GroupAlarmClient in framework/client.py per contracts/client-extensions.md (GET /labels?organization={id}&all=true)
- [X] T006 [P] Add `delete_appointment(id_, strategy, time)` method to GroupAlarmClient in framework/client.py per contracts/client-extensions.md (DELETE /appointment/{id})
- [X] T007 [P] Add `strategy` parameter to existing `update_appointment` method in framework/client.py per contracts/client-extensions.md (adds ?strategy= query param to PUT URL)
- [X] T008 [P] Create AppConfig dataclass and load_config/save_config functions in framework/config.py per contracts/config-module.md (.groupalarm.toml read/write with tomllib + tomli-w, file permissions 600 on Unix)
- [X] T009 [P] Create export_appointments function in framework/exporter.py per contracts/exporter-module.md (openpyxl, 13 columns including groupalarm_id and ga_importer_token, round-trip compatible)
- [X] T010 [P] Implement API key sanitizer logging filter in framework/log_sanitizer.py — ApiKeySanitizer + install_api_key_sanitizer per research.md R-011 (FR-016, FR-031)
- [X] T011 [P] Write tests for list_labels in tests/test_client.py (monkeypatch HTTP, no network)
- [X] T012 [P] Write tests for delete_appointment in tests/test_client.py (monkeypatch HTTP, strategy params, dry-run, 404 → AppointmentNotFound)
- [X] T013 [P] Write tests for update_appointment strategy parameter in tests/test_client.py (verify ?strategy= query param on PUT)
- [X] T014 [P] Write tests for config module in tests/test_config.py (load missing file → defaults, load valid TOML, load invalid TOML → ValueError, save and re-load round-trip, organization_id=None when missing)
- [X] T015 [P] Write tests for exporter module in tests/test_exporter.py (export to xlsx, verify 13 columns, verify groupalarm_id + ga_importer_token present, empty list → ValueError, round-trip compatibility with ImporterToken)
- [X] T016 [P] Write test for recurrence field on Appointment dataclass in tests/test_appointment.py (recurrence not in to_api_payload, recurrence populated from dict)

**Checkpoint**: Foundation ready — framework/ extended with config, exporter, label listing, delete, strategy-aware update, API key sanitizer. All tests green.

---

## Phase 3: User Story 1 — Browse & Filter Appointments (Priority: P1) 🎯 MVP

**Goal**: Launch the CLI and see a scrollable, filterable list of appointments. Filter by labels (toggle list with typeahead) and date range. Sort by start date or name. Search by text.

**Independent Test**: Launch the CLI, verify the appointment list loads from the API, apply a label filter → only matching appointments shown, apply a date range filter → list narrows, search by text → matches highlighted.

### Tests for User Story 1

- [X] T017 [P] [US1] Write Textual pilot test for app startup and appointment list loading in tests/test_app.py (monkeypatch GroupAlarmClient.list_appointments and list_labels, verify DataTable populated)
- [X] T018 [P] [US1] Write Textual pilot test for search filter in tests/test_app.py (type search term → list narrows, no match → empty list)
- [X] T019 [P] [US1] Write Textual pilot test for dry-run banner visibility in tests/test_app.py (banner shown when --dry-run, hidden otherwise)

### Implementation for User Story 1

- [X] T020 [US1] Create LabelService in cli/services/label_service.py — fetch labels via GroupAlarmClient.list_labels, cache for session, provide label-name/color lookup by ID
- [X] T021 [US1] Create AppointmentService in cli/services/appointment_service.py — bridge to GroupAlarmClient (list_appointments with date range params), hold in-memory appointment list, expose filter/sort/search methods
- [X] T022 [US1] Create FilterBar widget in cli/widgets/filter_bar.py — date range Inputs with restrict regex, search Input (Ctrl+F), filter events
- [X] T023 [US1] Create AppointmentList widget in cli/widgets/appointment_list.py — DataTable with columns (name [truncated with ellipsis per FR-034], start date, end date, labels [by name+color]), row selection events
- [X] T024 [US1] Create DetailPanel widget in cli/widgets/detail_panel.py — read-only view with help text when empty, appointment details with recurrence display (FR-025, FR-028)
- [X] T025 [US1] Create MainScreen in cli/screens/main_screen.py — Horizontal split layout (left: FilterBar + AppointmentList, right: DetailPanel showing help/how-to per FR-028), wire FilterBar events to AppointmentService filtering, wire list selection events
- [X] T026 [US1] Create GroupAlarmApp (Textual App subclass) in cli/app.py — push MainScreen, load labels+appointments, validate API key, handle --dry-run banner (FR-018), handle --org-id override, first-run org-id check (FR-021), key bindings (BINDINGS list per contracts/cli-application.md)
- [X] T027 [US1] Create Textual CSS stylesheet in cli/styles/app.tcss — Horizontal split ratios (1fr / 2fr), filter bar layout, list styling, dry-run banner styling (yellow), color theme
- [X] T028 [US1] Wire groupalarm_cli.py entry point to cli/app.py GroupAlarmApp — parse args, configure logging (with ApiKeySanitizer), load config, instantiate client, run app

**Checkpoint**: User Story 1 complete — user can launch CLI, see appointment list, filter by labels and date range, sort, search. MVP is functional.

---

## Phase 4: User Story 2 — View & Edit a Single Appointment (Priority: P2)

**Goal**: Select an appointment to see all fields in a detail panel. Edit fields inline, see unsaved changes highlighted, confirm before saving.

**Independent Test**: Select appointment → all fields displayed in detail panel → edit name → confirmation dialog shows diff (old → new) → confirm → change sent to API → list refreshes.

### Tests for User Story 2

- [X] T029 [P] [US2] Write Textual pilot test for detail panel population on selection in tests/test_app.py (select appointment in list → detail panel shows all fields)
- [X] T030 [P] [US2] Write Textual pilot test for edit mode and unsaved changes indicator in tests/test_app.py (enter edit mode → modify field → asterisk + color change on modified field, footer shows unsaved hint per FR-035)
- [X] T031 [P] [US2] Write Textual pilot test for confirmation dialog (diff view) in tests/test_confirmation.py (trigger save → ModalScreen shows field-by-field old→new diff, confirm → API called, cancel → no API call)
- [X] T032 [P] [US2] Write Textual pilot test for unsaved changes guard in tests/test_confirmation.py (navigate away with dirty=True → Save/Discard/Cancel dialog per FR-029)

### Implementation for User Story 2

- [X] T033 [US2] Create DetailPanel widget in cli/widgets/detail_panel.py — display all Appointment fields (name, description, start/end dates, labels [by name+color via LabelService], reminder, notification date, feedback deadline, visibility, participants [read-only], recurrence [read-only human-readable per FR-025]). Edit mode: Input widgets with validators (DateTimeValidator for dates, restrict regex). Track dirty flag via Input.Changed (FR-035). Modified fields: distinct background color + asterisk per FR-035
- [X] T034 [US2] Create ConfirmationDialog (ModalScreen[bool]) in cli/widgets/confirmation_dialog.py — side-by-side diff table for updates (old→new per field, changed fields highlighted per FR-009), structured payload summary for creates, irreversibility warning for deletes. Confirm/Cancel buttons
- [X] T035 [US2] Create UnsavedChangesDialog (ModalScreen[str]) in cli/widgets/confirmation_dialog.py — three options: Save, Discard, Cancel. Pushed on list-selection change, Escape, or quit when dirty=True (FR-029)
- [X] T036 [US2] Wire save flow in MainScreen: [s] key → validate fields locally (FR-015: end > start, required fields) → push ConfirmationDialog with diff → on confirm: call AppointmentService.update (with strategy selector for recurring) → lock UI + show loading indicator (FR-030) → refresh list (FR-027) → success indicator
- [X] T037 [US2] Wire unsaved changes guard in MainScreen: on list selection change, Escape, or action_quit → check dirty → push UnsavedChangesDialog → handle Save/Discard/Cancel (FR-029)
- [X] T038 [US2] Wire discard action: [Escape] in edit mode reverts all fields to server-side values
- [X] T039 [US2] Add loading indicator and UI lock during in-flight API calls in cli/app.py — disable mutation-triggering UI interactions, show spinner (FR-030)

**Checkpoint**: User Stories 1 + 2 complete — user can browse, filter, select, view detail, edit fields, confirm changes, unsaved changes are protected.

---

## Phase 5: User Story 3 — Export Appointments to Excel (Priority: P3)

**Goal**: Export currently filtered appointments to a round-trip-compatible .xlsx file.

**Independent Test**: Filter list to subset → press x → enter file path → .xlsx created with 13 columns → re-import with Runner → no duplicates.

### Tests for User Story 3

- [X] T040 [P] [US3] Write Textual pilot test for export action in tests/test_app.py (press x → file path prompt with default name appointments_YYYY-MM-DD.xlsx → export succeeds → success message)
- [X] T041 [P] [US3] Write Textual pilot test for export with no matching appointments in tests/test_app.py (empty filtered list → "No appointments to export" message, no file created per spec US3 scenario 4)
- [X] T042 [P] [US3] Write Textual pilot test for export overwrite prompt in tests/test_app.py (file exists → prompt to overwrite or auto-generate unique name per FR-011)

### Implementation for User Story 3

- [X] T043 [US3] Create export flow in MainScreen: [x] key → if empty list show message → else prompt for file path (Input with default appointments_YYYY-MM-DD.xlsx) → if file exists: overwrite confirmation or auto-generate counter suffix (FR-011) → call framework/exporter.py export_appointments with filtered list → show success/failure message
- [X] T044 [US3] Update footer.py to show export key hint (x) when appointments are loaded

**Checkpoint**: User Stories 1–3 complete — browse, filter, edit, and export all functional. Round-trip Excel workflow operational.

---

## Phase 6: User Story 4 — Create a New Appointment (Priority: P4)

**Goal**: Create a new appointment from within the CLI with pre-filled defaults, validation, and confirmation.

**Independent Test**: Press n → detail panel opens with defaults (start=now rounded to next hour, end=start+4h, org from config) → fill required fields → save → confirmation shows full payload → confirm → appointment created on server → appears in list.

### Tests for User Story 4

- [X] T045 [P] [US4] Write Textual pilot test for new appointment creation in tests/test_app.py (press n → detail panel with empty/default fields, fill name + dates → save → confirmation payload → confirm → API create called → list refreshed)
- [X] T046 [P] [US4] Write Textual pilot test for validation errors on create in tests/test_app.py (missing name → validation error shown, end before start → validation error per FR-015)

### Implementation for User Story 4

- [X] T047 [US4] Add create-new-appointment flow in MainScreen: [n] key → DetailPanel in create mode (empty fields with defaults from AppConfig: start=now rounded to next hour, end=start + default_appointment_duration_hours, organizationID from config per FR-013) → validate → ConfirmationDialog (full payload summary per FR-009) → call AppointmentService.create → refresh list (FR-027)
- [X] T048 [US4] Add validation error display in DetailPanel for missing required fields (name, dates) and invalid date ranges (FR-015)

**Checkpoint**: User Stories 1–4 complete — browse, filter, edit, export, and create all functional.

---

## Phase 7: User Story 5 — Delete an Appointment (Priority: P5)

**Goal**: Delete an appointment with clear confirmation including irreversibility warning. Recurring appointments show strategy selector.

**Independent Test**: Select appointment → press d → confirmation shows name + date range + warning → confirm → API delete called → appointment removed from list.

### Tests for User Story 5

- [X] T049 [P] [US5] Write Textual pilot test for delete flow in tests/test_app.py (select appointment → press d → confirmation dialog with name + warning → confirm → API delete called → list refreshed)
- [X] T050 [P] [US5] Write Textual pilot test for recurring appointment delete with strategy selector in tests/test_app.py (recurring appointment → strategy selector [single/upcoming/all] before confirmation → correct strategy passed to API)
- [X] T051 [P] [US5] Write Textual pilot test for delete cancellation in tests/test_app.py (cancel confirmation → no API call, appointment remains)

### Implementation for User Story 5

- [X] T052 [US5] Add delete flow in MainScreen: [d] key → if no appointment selected show hint → if recurring: push strategy selector OptionList (single/upcoming/all per FR-024) → push ConfirmationDialog (appointment name, date range, irreversibility warning per FR-014, FR-009) → on confirm: call AppointmentService.delete(id, strategy, time) → refresh list (FR-027)
- [X] T053 [US5] Create RecurrenceStrategyDialog (ModalScreen[str]) in cli/widgets/confirmation_dialog.py — presents "This occurrence only", "This and upcoming", "All occurrences" options for recurring appointment mutations

**Checkpoint**: All 5 user stories complete — browse, filter, edit, export, create, and delete all functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Graceful shutdown, help overlay, error handling, performance, and final validation

- [X] T054 [P] Create HelpScreen (ModalScreen) in cli/screens/help_screen.py — [?] key opens modal overlay listing all key bindings from contracts/cli-application.md (FR-017, FR-028)
- [X] T055 [P] Implement graceful shutdown in cli/app.py — override action_quit: check dirty flag → UnsavedChangesDialog, cancel in-flight @work workers, Ctrl+C binding routes through same quit flow (FR-032, research.md R-014)
- [X] T056 [P] Add timezone-aware display throughout cli/ — all datetime values displayed in configured timezone (default Europe/Berlin), sent to API as UTC/ISO 8601 (FR-019)
- [X] T057 [P] Add --verbose CLI flag handling: set logging to DEBUG level in groupalarm_cli.py (FR-031)
- [X] T058 [P] Add dry-run banner widget in cli/app.py — persistent banner at top when --dry-run active, planned mutation payloads in yellow (FR-018)
- [X] T059 [P] Handle config file permissions: set 600 on Unix in framework/config.py save_config (FR-033)
- [X] T060 [P] Handle invalid default_label_ids in config: validate against fetched labels on startup, silently ignore invalid IDs with logged warning (FR-022)
- [X] T061 [P] Handle network errors gracefully in cli/services/ — display error message, preserve unsaved local changes, allow retry (spec edge cases)
- [X] T062 [P] Handle empty appointment list state — display hint to create new appointment in list area (spec edge case)
- [X] T063 Run quickstart.md validation — verify installation steps, config file creation, all key bindings, dry-run mode, export workflow end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (requirements installed) — **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Phase 2 — MVP target
- **User Story 2 (Phase 4)**: Depends on Phase 2, lightly depends on Phase 3 (MainScreen, AppointmentList exist)
- **User Story 3 (Phase 5)**: Depends on Phase 2, lightly depends on Phase 3 (filtered list exists)
- **User Story 4 (Phase 6)**: Depends on Phase 2, lightly depends on Phase 4 (DetailPanel and ConfirmationDialog exist)
- **User Story 5 (Phase 7)**: Depends on Phase 2, lightly depends on Phase 4 (ConfirmationDialog exists)
- **Polish (Phase 8)**: Depends on Phases 3–7

### User Story Dependencies

- **US1 (P1)**: Foundation only — fully independent, MVP
- **US2 (P2)**: Needs US1 MainScreen + AppointmentList as host for DetailPanel
- **US3 (P3)**: Needs US1 filtered list to know what to export
- **US4 (P4)**: Needs US2 DetailPanel + ConfirmationDialog (reuses edit form in create mode)
- **US5 (P5)**: Needs US2 ConfirmationDialog (reuses for delete confirmation)

### Within Each User Story

1. Tests written first (MUST fail before implementation)
2. Services before widgets
3. Widgets before screen wiring
4. Core implementation before integration
5. Story complete → checkpoint validation

### Parallel Opportunities

**Phase 2 (Foundational)** — Maximum parallelism:
- T005, T006, T007 (client extensions) — different methods, same file but independent
- T008, T009, T010 (config, exporter, logging) — different files
- T011–T016 (all tests) — different test files/sections

**Phase 3 (US1)** — Tests in parallel, then services, then widgets:
- T017, T018, T019 (tests) — parallel
- T020, T021 (services) — parallel (different files)
- T022, T023, T024 (widgets) — parallel (different files)

**Phase 4 (US2)** — Tests in parallel, then sequential implementation:
- T029, T030, T031, T032 (tests) — parallel

**Phase 8 (Polish)** — All tasks independent:
- T054–T062 — all parallel (different files/concerns)

---

## Parallel Example: User Story 1

```bash
# Tests first (parallel):
T017: "Textual pilot test for app startup in tests/test_app.py"
T018: "Textual pilot test for label filter in tests/test_app.py"
T019: "Textual pilot test for date range filter in tests/test_app.py"

# Services (parallel — different files):
T020: "LabelService in cli/services/label_service.py"
T021: "AppointmentService in cli/services/appointment_service.py"

# Widgets (parallel — different files):
T022: "FilterBar widget in cli/widgets/filter_bar.py"
T023: "AppointmentList widget in cli/widgets/appointment_list.py"
T024: "Footer widget in cli/widgets/footer.py"

# Screen + App (sequential — integration):
T025: "MainScreen in cli/screens/main_screen.py"
T026: "GroupAlarmApp in cli/app.py"
T027: "CSS stylesheet in cli/styles/app.tcss"
T028: "Wire entry point in groupalarm_cli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T016) — CRITICAL, blocks everything
3. Complete Phase 3: User Story 1 (T017–T028)
4. **STOP and VALIDATE**: Launch CLI, see appointment list, filter by labels and dates, sort, search
5. Deploy/demo if ready — single-story MVP delivers core value

### Incremental Delivery

1. Setup + Foundational → framework extended, tests green
2. Add US1 (Browse & Filter) → Test independently → **MVP!**
3. Add US2 (View & Edit) → Test independently → inline editing live
4. Add US3 (Export) → Test independently → round-trip Excel workflow
5. Add US4 (Create) → Test independently → full CRUD minus delete
6. Add US5 (Delete) → Test independently → full CRUD complete
7. Polish → graceful shutdown, help, timezone, error handling
8. Each story adds value without breaking previous stories

### Suggested MVP Scope

**User Story 1 (Browse & Filter)** is the MVP. It delivers the foundational interaction — every other story depends on being able to see and select appointments first.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable at its checkpoint
- Constitution checks: all 6 principles verified in plan.md (PASS)
- Total FR coverage: FR-001 through FR-035 mapped across phases
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
