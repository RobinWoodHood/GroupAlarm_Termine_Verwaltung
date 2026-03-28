# Implementation Plan: TUI Detail Panel UX Overhaul

**Branch**: `003-tui-detail-ux-overhaul` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-tui-detail-ux-overhaul/spec.md`

## Summary

Overhaul the TUI detail panel to support live preview on list navigation (via `DataTable.RowHighlighted`), keyboard-driven focus switching (Enter/Right/Left/E), yellow-highlighted field labels (`$accent`), Up/Down arrow navigation in edit mode, direct participant display, three-column feedback lists with name resolution via a new Users API integration, creation defaults (`isPublic=false`, `keepLabelParticipantsInSync=true`), direct user addition with type-ahead suggestions, README modernization, and example config file.

## Technical Context

**Language/Version**: Python ≥ 3.11  
**Primary Dependencies**: Textual (TUI framework), requests (HTTP), tomllib/tomli_w (config)  
**Storage**: GroupAlarm REST API (remote), `.groupalarm.toml` (local config)  
**Testing**: pytest (unit tests with monkeypatched HTTP, no live API calls)  
**Target Platform**: Windows / Linux / macOS terminal  
**Project Type**: CLI / TUI application  
**Performance Goals**: Detail panel updates within 200ms of cursor movement; type-ahead within 300ms  
**Constraints**: No network access in tests; environment-variable authentication only  
**Scale/Scope**: Single-user TUI, typical org size <500 users, <100 appointments in view

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Interactive CLI-First | **PASS** | All changes enhance the TUI — split-view, keyboard navigation, visual feedback |
| II. Explicit Confirmation | **PASS** | Save/create still requires confirmation dialog; unsaved-changes warning added |
| III. Credential Security | **PASS** | Users API uses same `GROUPALARM_API_KEY` env var; no new credential paths |
| IV. Framework Reuse | **PASS** | New `list_users()` added to `GroupAlarmClient` first; `UserService` consumes it in CLI layer. `framework/` remains independently usable |
| V. Export & Round-Trip | **N/A** | No export changes in this feature |
| VI. Test Discipline | **PASS** | All new modules (UserService, client.list_users, detail panel changes) will have pytest unit tests with mocked HTTP |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/003-tui-detail-ux-overhaul/
├── plan.md              # This file
├── research.md          # Phase 0 output — all unknowns resolved
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — verification guide
├── contracts/           # Phase 1 output — interface contracts
│   ├── client-extensions.md
│   ├── user-service.md
│   └── detail-panel.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
framework/
├── appointment.py       # Existing — no structural changes
├── client.py            # Extended: add list_users() method
├── config.py            # Existing — no changes
└── ...

cli/
├── app.py               # Extended: initialize UserService on mount
├── screens/
│   └── main_screen.py   # Extended: RowHighlighted handler, Enter binding, unsaved-changes on Left
├── services/
│   ├── appointment_service.py  # Existing — no changes
│   ├── label_service.py        # Existing — no changes
│   └── user_service.py         # NEW: user cache, name resolution, display name lookup
├── widgets/
│   ├── detail_panel.py  # Major changes: field labels, feedback display, participant sections,
│   │                    #   edit form fields (keepLabelParticipantsInSync, participants),
│   │                    #   EditInput Up/Down bindings, UserSuggester
│   ├── appointment_list.py  # Extended: RowHighlighted event handling
│   ├── confirmation_dialog.py  # Extended: create summary includes new fields
│   ├── filter_bar.py    # No changes
│   └── state.py         # No changes
├── styles/
│   └── app.tcss         # Extended: .field-label color rule

tests/
├── test_client.py       # Extended: test list_users()
├── test_user_service.py # NEW: test UserService
├── test_detail_panel.py # Extended: test new sections, field labels, edit navigation
├── test_app.py          # Extended: test UserService integration
└── ...

.groupalarm.example.toml # NEW: example configuration
README.md                # Rewritten: TUI-focused, old framework references removed
```

**Structure Decision**: Single-project structure (existing). No new top-level directories. One new service module (`user_service.py`), one new config file, all other changes are extensions of existing files.

## Complexity Tracking

No constitution violations — table not needed.

## Implementation Phases (Summary)

### Phase 0: Research (completed)
All NEEDS CLARIFICATION resolved — see [research.md](research.md).

### Phase 1: Design (completed)
- [data-model.md](data-model.md): Entity definitions with relationships, state transitions, validation rules
- [contracts/client-extensions.md](contracts/client-extensions.md): `list_users()` API contract
- [contracts/user-service.md](contracts/user-service.md): UserService interface
- [contracts/detail-panel.md](contracts/detail-panel.md): Navigation, display, and edit form contracts
- [quickstart.md](quickstart.md): Verification guide

### Phase 2: Tasks (next — `/speckit.tasks`)
Task breakdown for implementation.

## Key Design Decisions

1. **Live preview via RowHighlighted**: Use Textual's built-in `DataTable.RowHighlighted` event rather than polling. This is event-driven and zero-lag.

2. **UserService as session-level cache**: Fetch all org users once on startup. Avoids N+1 lookups when resolving participant names. Memory usage is negligible for typical org sizes (<500 users).

3. **$accent for field labels**: Use the Textual theme variable `$accent` (yellow in dark theme) rather than hardcoded colors. This ensures theme consistency and future adaptability.

4. **Up/Down in EditInput only**: Arrow navigation between fields applies to `EditInput` (single-line) fields. `TextArea` (description) retains standard multi-line Up/Down for navigating lines.

5. **UserSuggester pattern**: Analogous to existing `LabelSuggester` — comma-separated token matching on the last token. Reuses the proven pattern.

6. **isPublic default change**: Only affects create mode. Existing appointments retain their saved values on edit. The `Appointment` dataclass default (`True`) is not changed — the default override happens in the create-mode initialization of `DetailPanel.enter_create_mode()`.

7. **Feedback status constants**: Defined as named constants (`FEEDBACK_NONE = 0`, `FEEDBACK_ACCEPTED = 1`, `FEEDBACK_DECLINED = 2`) to allow easy correction if API mapping differs.

