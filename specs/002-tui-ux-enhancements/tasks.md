# Tasks: TUI UX Enhancements

**Input**: Design documents from `/specs/002-tui-ux-enhancements/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Task can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1, US2, US3)
- Include exact file paths in every description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Finalize feature documentation and shared fixtures required by all subsequent phases.

- [X] T001 [Shared] Capture the keyboard-navigation + edit confirmation quickstart walkthrough in specs/002-tui-ux-enhancements/quickstart.md.
- [X] T002 [P] [Shared] Generate representative appointment and label fixtures for automated tests in tests/data/tui_sample.json.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core helpers and shared state that every user story depends on.

- [X] T003 [Shared] Implement `format_de_datetime`/`parse_de_datetime` helpers plus UTC→`Europe/Berlin` conversion utilities in framework/utils.py so every timestamp renders with the correct timezone.
- [X] T004 [P] [Shared] Introduce `NavigationState` and `FilterControls` dataclasses per the data model in cli/widgets/state.py.
- [X] T005 [P] [Shared] Extend cli/services/label_service.py with a `get_directory()` helper that returns the complete LabelDirectory for filters and autocomplete.
- [X] T006 [Shared] Define reminder conversion constants and the static 0–10 080 minute validation (with docstring explaining the fixed API limit) in framework/appointment.py.
- [X] T007 [P] [Shared] Add a reusable Textual Pilot fixture and focus helper in tests/conftest.py for keyboard-driven suites.
- [X] T039 [P] [Shared] Write NavigationState and FilterControls unit tests in tests/test_app.py (or a new tests/test_navigation.py) so pane focus transitions, preview-collapse flags, and shortcut-driven expansion are validated before wiring CLI widgets.
- [X] T040 [P] [Shared] Cover the reminder conversion constants and 0–10 080 minute guardrail introduced in framework/appointment.py with dedicated tests in tests/test_utils.py, ensuring invalid entries raise friendly errors before UI work begins.
- [X] T035 [P] [Shared] Add unit tests in tests/test_utils.py (plus a lightweight Textual Pilot regression in tests/test_app.py) that assert UTC payloads convert to `Europe/Berlin`, exercise DST transitions, and verify the helpers surface the raw ISO string + warning flag that drives the timezone toast when conversion fails.

**Checkpoint**: Navigation/data helpers and validation utilities are available for all stories.

---

## Phase 3: User Story 1 - Keyboard Navigation Between List and Detail (Priority: P1) 🎯 MVP

**Goal**: Operators can move focus between list, detail, and filter panes via arrows or shortcuts without losing selection or filters.

**Independent Test**: Launch the CLI, navigate solely with arrow buttons and shortcuts (`Ctrl + /`, `Ctrl + F`), and confirm list, detail, and filter controls remain reachable even when no appointments match.

### Tests for User Story 1 (Mandatory per Principle VI)

Write these tests before implementation so they fail first and guard regressions.

- [X] T008 [P] [US1] Add Textual Pilot coverage for list/detail arrow focus switching in tests/test_app.py.
- [X] T009 [P] [US1] Add filter-bar focus traversal tests in tests/test_filter_bar.py that cover zero-match indicators (muted `0` badge + "Keine Treffer" chip), the five-toggle preview with `+N weitere` hint while unfocused, and automatic full expansion when shortcuts or Tab move focus inside the bar.

### Implementation for User Story 1

- [X] T010 [US1] Register keyboard bindings for `Ctrl + /`, `Ctrl + Shift + /`, and `Ctrl + F` in cli/app.py.
- [X] T011 [US1] Manage NavigationState transitions and arrow affordances for pane switching in cli/screens/main_screen.py.
- [X] T012 [US1] Render list-pane arrow indicators and keep row selection highlighted in cli/widgets/appointment_list.py.
- [X] T013 [US1] Reflect active-panel status and focus restoration logic in cli/widgets/detail_panel.py view mode.
- [X] T014 [US1] Keep time/search/label controls visible, arrow/tab focusable, show only five label toggles plus the `+N weitere` helper when the bar is unfocused, auto-expand the full directory the moment focus enters (via shortcuts or traversal), and render the muted `0` badge plus "Keine Treffer" helper chip for zero-match labels in cli/widgets/filter_bar.py using FilterControls.
- [X] T015 [US1] Merge cached LabelDirectory data with active results (including zero-count metadata and the preview/expanded state) when populating filter toggles in cli/screens/main_screen.py so the `+N weitere` helper and five-toggle preview behave consistently.
- [X] T038 [US1] Ensure `MainScreen` listens for `FilterBar` focus events triggered by shortcuts and expands the preview row into the full list before focus changes, matching the "focused shows all / unfocused shows five" rule from Acceptance Scenario 2.

**Checkpoint**: Keyboard-only navigation across panes works end-to-end and is testable independently.

---

## Phase 4: User Story 2 - Confident Appointment Editing With Preview (Priority: P1)

**Goal**: Editing an appointment provides structured date/time fields, reminder units, label autocomplete, and a diff preview that requires confirmation before saving.

**Independent Test**: Enter edit mode, adjust multiple fields, verify reminder validation and label warnings, preview the diff, confirm, and observe both panes refresh.

### Tests for User Story 2 (Mandatory per Principle VI)

Author these tests before modifying widgets to satisfy the constitution's test-discipline requirement.

- [X] T016 [P] [US2] Add reminder conversion tests, start/end/notification ordering validation, and German-format conversion coverage in tests/test_detail_panel.py.
- [X] T017 [P] [US2] Add diff preview and label warning coverage in tests/test_confirmation.py.
- [X] T037 [P] [US2] Add a regression test proving `ConfirmationDialog` still blocks API calls until the user confirms in tests/test_confirmation.py.

### Implementation for User Story 2

- [X] T018 [US2] Implement `EditFormState` with split date/time inputs, dirty tracking, German formatting, and start/end/notification ordering validation that raises inline warnings before save in cli/widgets/detail_panel.py.
- [X] T019 [US2] Wire the reminder unit selector and inline warnings to the validator in cli/widgets/detail_panel.py.
- [X] T020 [US2] Implement label autocomplete tokens and unknown-label warnings using LabelService in cli/widgets/detail_panel.py.
- [X] T021 [US2] Build grouped diff preview sections and hook them into the confirmation flow in cli/widgets/confirmation_dialog.py.
- [X] T022 [US2] Refresh appointments after save by updating cli/services/appointment_service.py and cli/screens/main_screen.py to re-fetch and reselect the active row.

**Checkpoint**: Editing workflow is reliable, validated locally, and shows a confirmation diff prior to persistence.

---

## Phase 5: User Story 3 - Readable Detail Presentation (Priority: P2)

**Goal**: Detail and list views use consistent German timestamp formatting, improved spacing, and subtle color cues so operators can scan key info quickly.

**Independent Test**: View any appointment (with and without optional fields) and confirm timestamps follow `dd.mm.yyyy HH:MM`, sections have breathing room, and zero-state labels remain visible but muted.

### Tests for User Story 3 (Mandatory per Principle VI)

Create these tests ahead of implementation so visual polish remains verifiable.

- [X] T023 [P] [US3] Add list-view timestamp snapshot/assertions for the shared formatter in tests/test_appointment_list.py, including a forced conversion failure case that verifies the raw ISO fallback and warning-toast dispatch.
- [X] T024 [P] [US3] Add detail-panel spacing and optional-field rendering tests in tests/test_detail_panel.py, covering both normal formatting and the conversion-failure fallback that surfaces the toast + raw ISO string.

### Implementation for User Story 3

- [X] T025 [US3] Apply the shared formatter and zero-state messaging to rows in cli/widgets/appointment_list.py, and if timezone conversion fails, fall back to the raw ISO timestamp and dispatch a warning toast via `MainScreen`.
- [X] T026 [US3] Polish detail-panel layout spacing, section headings, and optional field fallbacks in cli/widgets/detail_panel.py, including the same timezone-conversion fallback and warning toast logic.
- [X] T027 [US3] Introduce new accent colors and spacing tokens supporting the refreshed layout in cli/styles/app.tcss.

**Checkpoint**: Visual presentation is scannable, with shared formatting applied everywhere.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Validation, documentation, and final verification across stories.

- [X] T028 [Shared] Document the new shortcuts, reminder limits, and diff preview flow in docs/API_REFERENCE.md.
- [X] T029 [P] [Shared] Run the focused pytest suite for updated widgets (tests/test_app.py, tests/test_filter_bar.py, tests/test_detail_panel.py, tests/test_appointment_list.py).
- [X] T030 [P] [Shared] Execute the quickstart scenario from specs/002-tui-ux-enhancements/quickstart.md as a manual acceptance checklist.
- [X] T031 [Shared] Design the SC-004 operator survey (questions + distribution plan) in docs/tui-survey.md, including the ≥90% satisfaction target and response window.
- [X] T032 [P] [Shared] Collect and summarize survey responses one week post-release, document whether the ≥90% goal was met, and add findings to docs/API_REFERENCE.md.
- [X] T033 [US1] Capture SC-001 focus transition timings (<1s) using a Textual Pilot benchmark in tests/test_app.py and record the results in docs/tui-focus-metrics.md.
- [X] T034 [US2] Log SC-003 first-attempt save success across at least 20 QA runs, summarize the percentage in docs/tui-save-metrics.md, and link the evidence from the confirmation flow.
- [X] T036 [US1] Record five consecutive keyboard-only quickstart runs (SC-005), note any focus issues, and append the run log to docs/tui-focus-metrics.md alongside the SC-001 metrics.

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** → Enables fixture/docs work for all phases.
- **Phase 2 (Foundational)** → Blocks all user stories until shared helpers and validators exist.
- **User Story Sequence**: US1 (P1) must complete before US2 so the navigation + filter state exists; US2 (P1) must complete before US3 to avoid reworking layout while editing is unstable; US3 (P2) depends on formatting helpers from prior stories but can begin after US2’s diff preview lands.
- **Polish** starts after desired user stories are complete.

Within each story:
1. Finish tests (T008–T009, T016–T017, T023–T024) so they fail first.
2. Implement functionality following the numbered tasks.
3. Use checkpoints to confirm the story is independently testable before moving on.

---

## Parallel Execution Examples

- **User Story 1**: Run T008 and T009 in parallel while implementation tasks T012–T014 proceed independently once T011 lands. T010 can happen concurrently with T011 because they touch different modules (cli/app.py vs cli/screens/main_screen.py).
- **User Story 2**: T016 and T017 run concurrently. After T018, tasks T019 and T020 can progress in parallel (both touch cli/widgets/detail_panel.py but separate sections) once scaffolding exists; coordinate merges accordingly. T021 can run while T022 wiring is underway.
- **User Story 3**: T023 and T024 kick off simultaneously, while T025 (list view) and T026 (detail panel) can progress in parallel as long as shared formatter code from T003 is complete. T027 is independent and can run alongside the tests.

---

## Implementation Strategy

1. **MVP (US1)**: Complete Phases 1–2, then deliver User Story 1 to restore reliable keyboard navigation — this satisfies the minimum viable UX improvement.
2. **Increment 2 (US2)**: Layer in the edit form, reminder validation, label autocomplete, and diff preview once navigation is stable, reusing the helpers created earlier.
3. **Increment 3 (US3)**: Polish readability and styling after the editing experience is locked, ensuring formatting helpers are already shared.
4. **Final Polish**: Update docs, run tests, and execute the quickstart scenario before handing off.

Each increment is independently testable using the checkpoints and manual quickstart, enabling staggered demos or releases if needed.
