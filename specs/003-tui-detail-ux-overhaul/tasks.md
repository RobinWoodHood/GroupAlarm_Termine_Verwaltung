# Tasks: TUI Detail Panel UX Overhaul

**Input**: Design documents from `/specs/003-tui-detail-ux-overhaul/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Test files listed in plan.md (`test_client.py`, `test_user_service.py`, `test_detail_panel.py`, `test_app.py`) should be added as a follow-up.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project initialization needed — existing project structure is in place.

*(No tasks — project already initialized with all required dependencies.)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user stories involving participants, name resolution, or field label styling can be implemented.

**⚠️ CRITICAL**: US5, US6, and US8 depend on UserService. US3 depends on the CSS rule.

- [X] T001 [P] Add `list_users(organization_id: int) -> List[Dict[str, Any]]` method to `framework/client.py` — API: `GET /users?organization={id}`, auth: `Personal-Access-Token` header, dry_run mode returns empty list, per contracts/client-extensions.md
- [X] T002 [P] Add `.field-label { color: $accent; }` CSS rule to `cli/styles/app.tcss` for yellow-highlighted field labels matching the detail panel border color
- [X] T003 Create `cli/services/user_service.py` — implement `UserService` class with `__init__(client, org_id)`, `load()`, `get_display_name(user_id)`, `get_user_id_by_display_name(display_name)`, `get_all_display_names()`, `get_directory()`, per contracts/user-service.md (depends on T001)
- [X] T004 [P] Export `UserService` in `cli/services/__init__.py`
- [X] T005 Initialize `UserService` in `cli/app.py` `on_mount` — call `user_service.load()` after label service, store reference for widget access (depends on T003)

**Checkpoint**: Foundation ready — `list_users()` callable, `UserService` cached, `.field-label` CSS available. User story implementation can now begin.

---

## Phase 3: User Story 1 — Live Detail Preview on List Navigation (Priority: P1) 🎯 MVP

**Goal**: Detail panel updates instantly when the user moves the cursor in the appointment list with Up/Down arrows.

**Independent Test**: Open TUI with multiple appointments, press Up/Down in the list, verify detail panel updates on each cursor movement without pressing Enter.

### Implementation for User Story 1

- [X] T006 [US1] Add `on_data_table_row_highlighted` handler to `cli/widgets/appointment_list.py` — post an `AppointmentHighlighted` message containing the appointment data for the newly highlighted row
- [X] T007 [US1] Handle `AppointmentHighlighted` message in `cli/screens/main_screen.py` — call `detail_panel.show_appointment()` to update the detail panel content on each cursor movement (depends on T006)

**Checkpoint**: Live preview works — moving the cursor in the list updates the detail panel instantly.

---

## Phase 4: User Story 2 — Keyboard-Driven Focus Switching (Priority: P1)

**Goal**: Users can navigate between list and detail panel using Enter/Right/Left/E/Escape without a mouse. Left/Right are reserved for text cursor in edit mode.

**Independent Test**: Press Right/Enter → detail panel gets focus. Press Left → return to list. Press E → edit mode. In edit mode, Left/Right move text cursor (not panels). Escape → read-only. Left with unsaved changes → warning dialog.

### Implementation for User Story 2

- [X] T008 [P] [US2] Add Enter key binding in `cli/screens/main_screen.py` to move focus to the detail panel (same action as Right arrow) — handle `on_data_table_row_selected` or add explicit binding
- [X] T009 [P] [US2] Add visible focus indicator styling for detail panel in read-only mode in `cli/styles/app.tcss` — ensure `$accent` border or equivalent shows active focus state
- [X] T010 [US2] Implement unsaved-changes guard in `cli/screens/main_screen.py` `action_focus_list_panel()` — when detail panel has dirty state in read-only mode, show `UnsavedChangesDialog` (Save/Discard/Cancel) instead of switching focus
- [X] T011 [US2] Ensure Left/Right arrow keys in edit mode are consumed by `EditInput` and `TextArea` widgets, NOT propagated to `MainScreen` panel-switching bindings — verify in `cli/widgets/detail_panel.py` and `cli/screens/main_screen.py`

**Checkpoint**: Full keyboard navigation works: Enter/Right → detail, Left → list (with unsaved-changes guard), E → edit, Escape → read-only. Left/Right stay within text fields in edit mode.

---

## Phase 5: User Story 3 — Highlighted Field Labels (Priority: P1)

**Goal**: All field labels in the detail panel (both read-only and edit modes) use the yellow `$accent` color matching the vertical separator line.

**Independent Test**: Open an appointment, verify all labels (Name:, Beschreibung:, Start:, etc.) are yellow in both read-only and edit modes.

### Implementation for User Story 3

- [X] T012 [P] [US3] Apply `.field-label` CSS class to all field label `Static` widgets in the read-only detail rendering in `cli/widgets/detail_panel.py` — covers Name, Beschreibung, Start, Ende, Labels, Öffentlich, Erinnerung, Benachrichtigung, Teilnehmer, Feedback section headers
- [X] T013 [P] [US3] Apply `.field-label` CSS class to all field label `Static` widgets preceding each input field in the edit mode form builder in `cli/widgets/detail_panel.py`

**Checkpoint**: Every field label in the detail panel is rendered in `$accent` (yellow) in both modes.

---

## Phase 6: User Story 9 — Tab Accepts All Type-Ahead Suggestions (Priority: P1)

**Goal**: Pressing Tab on any suggestion-enabled field accepts the current suggestion and positions the cursor at the end of the accepted text. Consistent across all suggestion fields.

**Independent Test**: In label field, type partial match, press Tab → suggestion accepted, cursor at end. Same for user participant field (after US8). No suggestion → Tab moves to next field.

### Implementation for User Story 9

- [X] T014 [US9] Verify and fix `EditInput.action_accept_or_next` in `cli/widgets/detail_panel.py` — ensure that after accepting a suggestion via Tab, `cursor_position` is set to `len(self.value)` (end of accepted text)
- [X] T015 [US9] Ensure comma-separated token suggestion fields (LabelSuggester, and later UserSuggester) apply suggestions only to the current token after the last comma in `cli/widgets/detail_panel.py` (FR-025)

**Checkpoint**: Tab-accept works correctly on all existing suggestion fields with cursor positioned at text end.

---

## Phase 7: User Story 4 — Arrow Key Navigation in Edit Mode (Priority: P2)

**Goal**: Up/Down arrows move between single-line EditInput fields. In the multi-line Beschreibung TextArea, Up/Down navigate lines internally and only move to adjacent fields at boundary lines.

**Independent Test**: Enter edit mode, use Up/Down to move between fields. In Beschreibung, type multiple lines, verify Up/Down navigate lines; Down on last line → next field; Up on first line → previous field.

### Implementation for User Story 4

- [X] T016 [P] [US4] Add Up/Down key bindings to `EditInput` class in `cli/widgets/detail_panel.py` — Up calls `screen.focus_previous()`, Down calls `screen.focus_next()`
- [X] T017 [P] [US4] Implement TextArea boundary navigation in `cli/widgets/detail_panel.py` — subclass `TextArea` or add key event handler: when `cursor_location[0] == 0` and Up pressed → `screen.focus_previous()`, when `cursor_location[0] == document.line_count - 1` and Down pressed → `screen.focus_next()`
- [X] T018 [US4] Implement no-wrap guards in `cli/widgets/detail_panel.py` — Up on the first form field and Down on the last form field must be no-ops (do not wrap around) (depends on T016, T017)

**Checkpoint**: Full arrow-key field navigation works for both single-line and multi-line fields with correct boundary behavior.

---

## Phase 8: User Story 5 — Direct Participant Display (Priority: P2)

**Goal**: A "Direkte Teilnehmer" section shows participants added directly (labelID = 0 or null), with names resolved via UserService. Hidden when none exist.

**Independent Test**: View an appointment with direct participants → "Direkte Teilnehmer" section appears with resolved names. View one without → section hidden.

### Implementation for User Story 5

- [X] T019 [US5] Add participant filtering logic to `cli/widgets/detail_panel.py` — extract participants where `labelID` is 0 or None from the appointment data
- [X] T020 [US5] Render "Direkte Teilnehmer" section in the detail panel read-only view in `cli/widgets/detail_panel.py` — resolve names via `UserService.get_display_name(userID)`, hide entire section if no direct participants (depends on T019)

**Checkpoint**: Direct participants are correctly identified and displayed by name. Section hidden when empty.

---

## Phase 9: User Story 6 — Participant Feedback Lists (Priority: P2)

**Goal**: Three feedback sub-lists (Zugesagt/Abgesagt/Keine Rückmeldung) show participants grouped by feedback status, with feedbackMessage displayed below names. Names resolved via UserService.

**Independent Test**: View an appointment with mixed feedback statuses → three lists with counts, names, and messages. Empty groups hidden.

### Implementation for User Story 6

- [X] T021 [US6] Add feedback grouping logic to `cli/widgets/detail_panel.py` — group participants by feedback status: 1=Zugesagt, 2=Abgesagt, 0=Keine Rückmeldung; use named constants for enum values per research R-006
- [X] T022 [US6] Render three feedback sub-lists in the detail panel read-only view in `cli/widgets/detail_panel.py` — each list shows header with count (e.g., "[Zugesagt] (3)"), participant names resolved via UserService, `feedbackMessage` in dim/secondary style below name; hide empty groups (depends on T021)
- [X] T023 [US6] Implement Users API fallback display in `cli/widgets/detail_panel.py` — when UserService cache is empty (API unreachable), show `User #12345` format with a visible warning notification (FR-016)

**Checkpoint**: Feedback lists render correctly with grouped participants, resolved names, messages, and graceful fallback.

---

## Phase 10: User Story 7 — Creation Defaults and New Fields (Priority: P2)

**Goal**: New appointment creation exposes `keepLabelParticipantsInSync` (default: Ja) and changes `isPublic` default to Nein.

**Independent Test**: Open create form → verify keepLabelParticipantsInSync shows "Ja", isPublic shows "Nein". Change values and save → verify payload reflects changes.

### Implementation for User Story 7

- [X] T024 [P] [US7] Add `keepLabelParticipantsInSync` field to `EDIT_FIELD_DEFS` in `cli/widgets/detail_panel.py` — Ja/Nein EditInput, default value "Ja" in create mode, field ID `keepLabelParticipantsInSync`, label "Label-Sync:"
- [X] T025 [P] [US7] Change `isPublic` default value from "Ja" to "Nein" in create-mode field initialization in `cli/widgets/detail_panel.py`
- [X] T026 [US7] Update create/edit confirmation summary in `cli/widgets/confirmation_dialog.py` to include `keepLabelParticipantsInSync` and display both new field values

**Checkpoint**: Create form shows correct defaults. Both fields appear in confirmation dialog and are included in the API payload.

---

## Phase 11: User Story 8 — Direct User Addition in Appointment Creation (Priority: P2)

**Goal**: A "Teilnehmer" field with type-ahead suggestions from all org users allows adding direct participants by name, comma-separated.

**Independent Test**: In create form, type partial user name → suggestion appears. Tab → accepted. Type comma, another name → new suggestion. Save → participant user IDs in payload.

### Implementation for User Story 8

- [X] T027 [US8] Create `UserSuggester` class in `cli/widgets/detail_panel.py` — analogous to `LabelSuggester`, suggests from `UserService.get_all_display_names()`, handles comma-separated tokens (suggest only for the current token after last comma)
- [X] T028 [US8] Add "Teilnehmer" `EditInput` field with `UserSuggester` to `EDIT_FIELD_DEFS` in `cli/widgets/detail_panel.py` — field ID `participants`, label "Teilnehmer:", default "" (depends on T027)
- [X] T029 [US8] Implement user ID resolution from display names when building the API payload in `cli/widgets/detail_panel.py` — parse comma-separated names, call `UserService.get_user_id_by_display_name()` for each, build participant list with `labelID=0` (depends on T028)

**Checkpoint**: Users can add direct participants by name with type-ahead. Correct user IDs appear in the saved appointment payload.

---

## Phase 12: User Story 10 — README Modernization (Priority: P3)

**Goal**: README focuses on TUI workflows. All old framework references (Mapper, Runner, Importer, CSV/Excel, Token/UUID) removed.

**Independent Test**: Read README — zero mentions of Mapper, Runner, Importer, CSV, Excel, Token/UUID, `example_usage.py`. Contains: TUI startup, configuration, keyboard shortcuts.

### Implementation for User Story 10

- [X] T030 [US10] Rewrite `README.md` — document TUI startup (`python groupalarm_cli.py`), `.groupalarm.toml` configuration, keyboard shortcuts (list/detail navigation, edit mode, filtering, creation), dry-run mode, installation instructions; remove all references to Mapper, Runner, CSVImporter, ExcelImporter, Token/UUID persistence, `example_usage.py`

**Checkpoint**: README is TUI-focused with zero legacy framework references.

---

## Phase 13: User Story 11 — Example Configuration File (Priority: P3)

**Goal**: A `.groupalarm.example.toml` documents all configuration keys with sensible defaults and comments.

**Independent Test**: Parse file with TOML parser — valid TOML. Contains all AppConfig keys from data-model.md.

### Implementation for User Story 11

- [X] T031 [US11] Create `.groupalarm.example.toml` in repository root — include all AppConfig keys per data-model.md: `[general]` section with `organization_id`, `timezone`; `[defaults]` section with `date_range_days`, `label_ids`, `appointment_duration_hours`; add TOML comments explaining each key

**Checkpoint**: Example config is valid TOML covering all application settings.

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and consistency checks

- [X] T032 [P] Run quickstart.md verification guide end-to-end — verify all 7 feature areas (live preview, focus switching, field labels, edit navigation, participants, feedback, creation defaults)
- [X] T033 Code review for consistency across all modified files — verify CSS class usage, UserService integration, keyboard bindings, and state transitions match contracts/detail-panel.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No tasks — existing project
- **Foundational (Phase 2)**: No external dependencies — can start immediately. BLOCKS US5, US6, US8 (need UserService) and US3 (needs CSS rule)
- **US1 (Phase 3)**: Depends on Phase 2 CSS (T002) only if field labels are rendered during preview — otherwise can start after Phase 1
- **US2 (Phase 4)**: Can start after Phase 2. Independent of US1.
- **US3 (Phase 5)**: Depends on T002 (.field-label CSS rule)
- **US9 (Phase 6)**: Can start after Phase 2. Independent of other stories.
- **US4 (Phase 7)**: Can start after Phase 2. Independent of other stories.
- **US5 (Phase 8)**: Depends on T003/T005 (UserService for name resolution)
- **US6 (Phase 9)**: Depends on T003/T005 (UserService for name resolution)
- **US7 (Phase 10)**: Can start after Phase 2. Independent of other stories.
- **US8 (Phase 11)**: Depends on T003/T005 (UserService for suggestions)
- **US10 (Phase 12)**: No dependencies on other stories — can run anytime
- **US11 (Phase 13)**: No dependencies on other stories — can run anytime
- **Polish (Phase 14)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent — no dependencies on other stories
- **US2 (P1)**: Independent — can run in parallel with US1
- **US3 (P1)**: Independent — needs only CSS rule from Phase 2
- **US9 (P1)**: Independent — verifies existing behavior
- **US4 (P2)**: Independent — can run in parallel with other P2 stories
- **US5 (P2)**: Needs UserService (Phase 2) — otherwise independent
- **US6 (P2)**: Needs UserService (Phase 2) — otherwise independent
- **US7 (P2)**: Independent
- **US8 (P2)**: Needs UserService (Phase 2) — otherwise independent
- **US10 (P3)**: Fully independent
- **US11 (P3)**: Fully independent

### Within Each User Story

- Models/infrastructure before display logic
- Display logic before integration
- Core implementation before edge-case handling

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T001 and T002 can run in parallel (different files)
- T003 starts after T001 completes
- T004 and T005 can run in parallel after T003

**P1 Stories (after Phase 2)**:
- US1, US2, US3, US9 can all start in parallel (touch different aspects of detail_panel.py and main_screen.py — coordinate edits if running simultaneously)

**P2 Stories (after Phase 2)**:
- US4, US5, US6, US7, US8 can start in parallel
- US5 and US6 share participant display area — best done sequentially

**P3 Stories**:
- US10 and US11 are completely independent — can run anytime, even in parallel with P1/P2

---

## Parallel Example: Foundational Phase

```
# Batch 1 (parallel):
T001: Add list_users() to framework/client.py
T002: Add .field-label CSS rule to cli/styles/app.tcss

# Batch 2 (after T001):
T003: Create cli/services/user_service.py

# Batch 3 (parallel, after T003):
T004: Export UserService in cli/services/__init__.py
T005: Initialize UserService in cli/app.py
```

## Parallel Example: P1 Stories

```
# After Phase 2, all P1 stories can start in parallel:
US1: T006, T007 (appointment_list.py, main_screen.py)
US2: T008-T011 (main_screen.py, app.tcss, detail_panel.py)
US3: T012, T013 (detail_panel.py)
US9: T014, T015 (detail_panel.py)

# Note: US2 and US3 both touch detail_panel.py — coordinate if parallel
```

## Parallel Example: P2 Stories

```
# After Phase 2, P2 stories can proceed:
US4: T016-T018 (detail_panel.py — EditInput/TextArea navigation)
US7: T024-T026 (detail_panel.py + confirmation_dialog.py — standalone)
US5: T019-T020 (detail_panel.py — participant display)
US6: T021-T023 (detail_panel.py — feedback lists, after US5)
US8: T027-T029 (detail_panel.py — UserSuggester, after US5/US6)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001–T005)
2. Complete Phase 3: US1 — Live Detail Preview (T006–T007)
3. **STOP and VALIDATE**: Detail panel updates on cursor movement
4. This alone delivers the highest-impact UX improvement

### Incremental Delivery

1. **Foundation** → Phase 2 (T001–T005)
2. **MVP** → US1 Live Preview (T006–T007) → Validate
3. **P1 batch** → US2 Focus Switching + US3 Field Labels + US9 Tab-Accept (T008–T015) → Validate
4. **P2 core** → US4 Arrow Nav + US7 Defaults (T016–T018, T024–T026) → Validate
5. **P2 participants** → US5 Direct Participants + US6 Feedback Lists + US8 User Addition (T019–T023, T027–T029) → Validate
6. **P3 docs** → US10 README + US11 Example Config (T030–T031)
7. **Polish** → (T032–T033)

Each increment is independently testable and delivers visible user value.
