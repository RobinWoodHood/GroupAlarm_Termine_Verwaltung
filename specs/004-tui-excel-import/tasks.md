# Tasks: TUI Excel Import with Preview and Upload

**Input**: Design documents from `/specs/004-tui-excel-import/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Test tasks are included per plan.md which specifies 4 new test files (test_import_service.py, test_import_preview_screen.py, test_import_config.py, test_import_summary.py).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. User Story 5 (Tier 3 wizard, P3/future) is explicitly deferred per spec and research R11 and is not included.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create new module files and establish base data structures

- [x] T001 Create cli/services/import_service.py with data model dataclasses (ImportSession, SkippedRow, UploadResult, ImportSummary) per data-model.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Config extension and default mapping — MUST complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Add ImportConfig frozen dataclass (mapping_file: str | None, sheet_name: str | None) and extend AppConfig with import_config field, update load_config()/save_config() to handle [import] TOML section per contracts/config-import-section.md in framework/config.py
- [x] T003 [P] Define DEFAULT_IMPORT_COLUMNS mapping dict (13 columns matching exporter.COLUMNS with parse logic per contracts/import-service.md Default Column Mapping table) in cli/services/import_service.py
- [x] T004 Create tests/test_import_config.py with unit tests for ImportConfig loading (missing [import] section → None, mapping_file set, sheet_name set) and saving (round-trip, omit when None)

**Checkpoint**: Config infrastructure ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Import Excel and Preview Appointments (Priority: P1) 🎯 MVP

**Goal**: User presses Ctrl+O, enters a file path, and sees a red-styled read-only preview of all parsed appointments with navigation and filtering — using the built-in Tier 1 default mapping for TUI-exported Excel files.

**Independent Test**: Import a TUI-exported Excel file → verify red banner, red text, arrow-key navigation, detail panel updates, filter controls work, Escape cancels without server contact.

### Implementation for User Story 1

- [x] T005 [US1] Implement parse_excel(file_path, import_config, organization_id, timezone) with Tier 1 default mapping: open file via ExcelImporter (sheet_name from import_config if present), iterate rows using DEFAULT_IMPORT_COLUMNS, extract groupalarm_id → Appointment.id and ga_importer_token → description append, record SkippedRow on parse error, return ImportSession per contracts/import-service.md in cli/services/import_service.py
- [x] T006 [P] [US1] Create ImportFileDialog(ModalScreen[str | None]) with Input widget (placeholder "Path to Excel file (.xlsx)"), file-exists validation, Enter/Import button → dismiss(path), Escape/Cancel → dismiss(None) per contracts/import-preview-screen.md in cli/screens/import_preview_screen.py
- [x] T007 [US1] Create ImportPreviewScreen(Screen) with compose() layout: banner Static (#import-banner), FilterBar, Horizontal split of AppointmentList + DetailPanel; screen-level DEFAULT_CSS for red styling (DataTable color: red, DetailPanel fields red, darkred cursor, darkred banner per contracts/import-preview-screen.md CSS); key bindings (escape→action_cancel, left/right→focus panels, ctrl+f→search, ctrl+t→date filter); action_cancel() pops screen in cli/screens/import_preview_screen.py
- [x] T008 [US1] Implement on_mount() in ImportPreviewScreen: display banner text "⚠ IMPORT PREVIEW — {filename} ({N} appointments) [Tier {1|2}]", show skipped-rows notification if any, populate AppointmentList with import_session.appointments, resolve labels via label_service, populate FilterBar, focus appointment list; implement on_appointment_highlighted() → detail_panel.show_appointment() read-only in cli/screens/import_preview_screen.py
- [x] T009 [US1] Implement in-memory filtering in ImportPreviewScreen: reuse FilterControls state object, apply date range filter, label toggles, and text search locally against import_session.appointments, re-populate AppointmentList after each filter change in cli/screens/import_preview_screen.py
- [x] T010 [US1] Add Ctrl+O binding to BINDINGS list in cli/app.py with action_import() that delegates to the active screen
- [x] T011 [US1] Implement action_import() in cli/screens/main_screen.py: push ImportFileDialog, on result (non-None) call ImportService.parse_excel() with file path and AppConfig settings, push ImportPreviewScreen with parsed ImportSession + client + label_service + config + dry_run
- [x] T012 [P] [US1] Add unit tests for parse_excel() Tier 1 default mapping (valid TUI export round-trip, skipped rows with missing name/startDate, empty file raises ValueError, missing columns handled) in tests/test_import_service.py
- [x] T013 [P] [US1] Create tests/test_import_preview_screen.py with unit tests for ImportPreviewScreen (mount shows banner + appointments, arrow navigation updates detail panel, filtering reduces visible list, escape cancels without modification)

**Checkpoint**: User Story 1 fully functional — TUI-exported Excel files can be imported and previewed with red styling, navigation, and filters

---

## Phase 4: User Story 2 — Python Mapping Module for Custom Imports (Priority: P1)

**Goal**: User sets `mapping_file` in `[import]` config section, and the import uses the referenced Python module's `mapping`/`defaults` dicts with the full power of Mapper — lambdas, multi-column templates, label-token mapping, custom date formats, relative dates.

**Independent Test**: Set `mapping_file = "Bereichsausbildungen_productive.py"` in config, import a non-standard Excel file → verify preview shows correctly transformed appointments using the mapping module.

### Implementation for User Story 2

- [x] T014 [US2] Implement load_mapping_module(mapping_file) in cli/services/import_service.py: resolve path (relative to project root if not absolute), validate .py extension and file existence, load via importlib.util.spec_from_file_location() + module_from_spec() + loader.exec_module(), extract module.mapping (required dict) and module.defaults (optional dict, default {}), raise FileNotFoundError/ValueError with descriptive messages per contracts/import-service.md error handling
- [x] T015 [US2] Add Tier 2 selection logic to parse_excel() in cli/services/import_service.py: if import_config is not None and import_config.mapping_file is set → call load_mapping_module(), merge defaults with function params (timezone, organization_id as fallbacks), create Mapper(mapping, defaults), use Mapper.map_row() per row, record column_mapping_used as "tier2-module:{path}"
- [x] T016 [P] [US2] Add unit tests for load_mapping_module() (valid module with mapping+defaults, missing file, syntax error, missing mapping attribute, non-.py file) and Tier 2 parse_excel() (custom mapping transforms rows correctly, defaults merge, lambda evaluation) in tests/test_import_service.py

**Checkpoint**: User Story 2 complete — existing Python mapping files (e.g. Bereichsausbildungen_productive.py) work as Tier 2 import modules without modification

---

## Phase 5: User Story 3 — Upload Imported Appointments (Priority: P3)

**Goal**: User presses Ctrl+U on the preview screen to upload all visible appointments to GroupAlarm with create/update logic, confirmation dialog, and dry-run support.

**Independent Test**: Import an Excel, press Ctrl+U → confirmation dialog shows create/update counts → in dry-run mode, verify payloads logged without API calls.

### Implementation for User Story 3

- [x] T017 [US3] Implement upload(appointments, client, dry_run) in cli/services/import_service.py: for each appointment — if id set → client.update_appointment() (on AppointmentNotFound 404 → fall back to create), if id None → ImporterToken.ensure_token() then client.create_appointment(), wrap each in try/except recording UploadResult(action=created|updated|failed, error=str), return ImportSummary with aggregated counts per contracts/import-service.md
- [x] T018 [US3] Add Ctrl+U binding and action_upload() to ImportPreviewScreen in cli/screens/import_preview_screen.py: collect currently filtered appointments, count create vs update (based on appointment.id None vs set), push ConfirmationDialog with "Upload {N} appointments? ({X} new, {Y} updates)", on confirm call ImportService.upload() with appointments + client + dry_run per contracts/import-preview-screen.md and research R7
- [x] T019 [P] [US3] Add unit tests for upload() (successful create, successful update, 404 fallback to create, exception → failed result, dry-run mode, ImportSummary counts) in tests/test_import_service.py

**Checkpoint**: User Story 3 complete — full upload flow with confirmation and dry-run support

---

## Phase 6: User Story 4 — Upload Summary with Error Details (Priority: P4)

**Goal**: After upload, a summary modal shows total/created/updated/failed counts and lists each failed appointment with error reason. Dismiss returns to main screen with refreshed data.

**Independent Test**: Trigger upload with mix of successful and failing appointments → verify summary shows correct counts and failure list → dismiss returns to main screen.

### Implementation for User Story 4

- [x] T020 [US4] Create ImportSummaryScreen(ModalScreen[None]) in cli/screens/import_summary_screen.py: title "Import Summary" (or "Import Summary (DRY-RUN)" when dry_run), stats line "Total: N | Created: X | Updated: Y | Failed: Z", scrollable failure list showing each failed appointment name + error reason, escape/enter bindings to dismiss per contracts/import-preview-screen.md and research R8
- [x] T021 [US4] Wire ImportSummaryScreen into upload flow in cli/screens/import_preview_screen.py: after ImportService.upload() completes push ImportSummaryScreen with results, on summary dismiss pop both screens (summary + preview) and trigger MainScreen._load_appointments() to refresh server data
- [x] T022 [P] [US4] Create tests/test_import_summary.py with unit tests for ImportSummaryScreen (all success display, mixed success + failures display, empty failures list, dry-run title indicator, escape/enter dismiss)

**Checkpoint**: Full import-preview-upload-summary workflow complete end-to-end

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Integration cleanup, documentation, and final validation

- [x] T023 [P] Update module exports in cli/screens/__init__.py (ImportPreviewScreen, ImportFileDialog, ImportSummaryScreen) and cli/services/__init__.py (ImportService) for public API surface
- [x] T024 [P] Add Ctrl+O import shortcut to help screen key bindings table in cli/screens/help_screen.py
- [ ] T025 Run quickstart.md verification steps to validate full import-preview-upload-summary workflow end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — delivers MVP (Tier 1 import + preview)
- **US2 (Phase 4)**: Depends on Phase 3 T005 (parse_excel infrastructure) — adds Tier 2 mapping
- **US3 (Phase 5)**: Depends on Phase 3 T007-T009 (preview screen) — adds upload capability
- **US4 (Phase 6)**: Depends on Phase 5 T017-T018 (upload flow) — adds summary screen
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Phase 1 (Setup)
  └─▶ Phase 2 (Foundational: config + default mapping)
       └─▶ US1 (P1): Import + Preview [Tier 1]
            ├─▶ US2 (P1): Python Mapping Module [Tier 2]  (extends parse_excel)
            └─▶ US3 (P3): Upload                          (extends preview screen)
                 └─▶ US4 (P4): Summary                    (extends upload flow)
```

- US2 and US3 are independent of each other — they extend different parts of US1
- US4 depends on US3 only

### Within Each User Story

- Data model / service tasks before screen tasks
- Screen skeleton before behaviour (navigation, filtering)
- Core implementation before integration (bindings, wiring)
- Tests after implementation tasks they cover

### Parallel Opportunities

**Phase 2**: T003 (DEFAULT_IMPORT_COLUMNS) can run alongside T002 (config changes) — different files

**Phase 3 (US1)**:
- T005 (parse_excel) ∥ T006 (ImportFileDialog) — different concerns, T006 in different section of file
- T012 (test_import_service) ∥ T013 (test_import_preview) — different test files

**Phase 4 (US2)**: T016 (tests) can run after T014-T015 complete

**Phase 5 (US3)**: T019 (tests) can run after T017-T018 complete

**Phase 6 (US4)**: T022 (tests) can run after T020-T021 complete

**Phase 7**: T023 ∥ T024 — independent files

---

## Parallel Execution Example: User Story 1

```
# Batch 1 — parallel (different concerns):
T005: Implement parse_excel() Tier 1 in cli/services/import_service.py
T006: Create ImportFileDialog in cli/screens/import_preview_screen.py

# Batch 2 — sequential (same file, builds on T006/T007):
T007: Create ImportPreviewScreen skeleton + CSS + bindings
T008: Add on_mount initialization + highlight handler
T009: Add in-memory filtering

# Batch 3 — parallel (different files):
T010: Add Ctrl+O binding in cli/app.py
T011: Add action_import() in cli/screens/main_screen.py

# Batch 4 — parallel (test files, independent):
T012: Tests for parse_excel() in tests/test_import_service.py
T013: Tests for preview screen in tests/test_import_preview_screen.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002-T004)
3. Complete Phase 3: User Story 1 (T005-T013)
4. **STOP and VALIDATE**: Import a TUI-exported Excel → verify red preview, navigation, filters, cancel
5. This delivers immediate value — users can already import and visually verify data

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. **US1** → Tier 1 import + preview (MVP!)
3. **US2** → Tier 2 Python mapping module support (full Mapper power)
4. **US3** → Upload with confirmation + dry-run
5. **US4** → Summary screen with failure details
6. Each story adds value without breaking previous stories

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 25 |
| **Phase 1 (Setup)** | 1 task |
| **Phase 2 (Foundational)** | 3 tasks |
| **Phase 3 (US1 — MVP)** | 9 tasks |
| **Phase 4 (US2)** | 3 tasks |
| **Phase 5 (US3)** | 3 tasks |
| **Phase 6 (US4)** | 3 tasks |
| **Phase 7 (Polish)** | 3 tasks |
| **Parallel opportunities** | 7 batches across all phases |
| **Suggested MVP scope** | Phases 1-3 (US1: Tier 1 import + preview) |
| **Deferred** | US5 (Tier 3 interactive wizard) — not included |

## Notes

- User Story 5 (Tier 3 interactive wizard, P3/future) is **not included** — explicitly deferred per spec and research R11
- [P] tasks can run in parallel (different files, no dependencies on incomplete tasks)
- [US*] labels map tasks to user stories from spec.md for traceability
- Tests use pytest with monkeypatched data — no live API calls per constitution Principle VI
- Existing mapping files (Bereichsausbildungen_productive.py, example_usage.py) serve as Tier 2 validation targets
- Screen-level DEFAULT_CSS is used for red styling per research R2 — **app.tcss is NOT modified**
- Config uses `import_config.mapping_file` (str path to Python module) per contracts/config-import-section.md and contracts/import-service.md — no TOML-embedded column definitions
- All checklist items follow strict format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
