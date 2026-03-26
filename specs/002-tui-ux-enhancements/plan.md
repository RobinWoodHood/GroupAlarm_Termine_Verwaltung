ios/ or android/
# Implementation Plan: TUI UX Enhancements

**Branch**: `002-tui-ux-enhancements` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-tui-ux-enhancements/spec.md`

## Summary

- Restore fast keyboard navigation between the appointment list, detail panel, and filter bar by adding visible left/right affordances plus focus-handling bindings (`Ctrl + /` for start-date filter, `Ctrl + Shift + /` for end-date filter, `Ctrl + F` for search) and arrow-key traversal within filters; while unfocused the label section shows a five-toggle preview (with a `+N weitere` helper), but focusing any filter expands the full directory immediately.  
- Rebuild the `DetailPanel` into a structured form with dedicated date/time inputs (German format), reminder unit selector, label autocomplete with warning on unknown labels, and a diff preview modal before saving so editing is reliable.  
- Polish the split view with consistent `dd.mm.yyyy HH:MM` timestamps, spacing, and color accents, keeping filter controls populated with all labels regardless of the active list so operators never lose context, and ensure every displayed timestamp is derived from UTC data converted via `ZoneInfo("Europe/Berlin")` before formatting, falling back to the raw ISO string plus a warning toast if conversion fails.  
- After rollout, run the SC-004 pulse survey (targeting ≥90% satisfaction) and record the findings in docs so readability improvements are evidence-backed.
- Instrument SC-001, SC-003, and SC-005 during QA by capturing Textual Pilot timing benchmarks, first-attempt save logs, and five-run keyboard-only streak evidence in docs/tui-focus-metrics.md and docs/tui-save-metrics.md.

## Technical Context

**Language/Version**: Python 3.11 (Textual 0.85.2, Rich bundled)  
**Primary Dependencies**: Textual UI toolkit, python-dateutil for parsing, zoneinfo for TZ conversion, openpyxl for exports, GroupAlarm framework modules (`framework/appointment.py`, `framework/client.py`)  
**Storage**: Remote GroupAlarm REST API (appointments + labels) with local `.groupalarm.toml` config for defaults; no new persistence  
**Testing**: pytest + Textual Pilot for widget flows, monkeypatched `GroupAlarmClient` for HTTP isolation, snapshot-friendly diff output tests, and timezone conversion unit tests that assert UTC→`Europe/Berlin` behavior  
**Target Platform**: Cross-platform terminal (Windows primary) with 256-color + UTF-8 support  
**Project Type**: Interactive CLI / TUI layered atop existing framework library  
**Performance Goals**: Focus transitions < 1s, filter updates < 300 ms for 500 appointments, diff modal renders within one frame  
**Constraints**: Keyboard-first UX, explicit confirmation before every mutation, timezone-aware display (`Europe/Berlin` conversions via `ZoneInfo`), reminder limits capped at a static 0–10 080 minutes per appointment API contract (see R-201)  
**Scale/Scope**: Dozens to low hundreds of appointments per window; label directories typically ≤ 200 entries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Interactive CLI-First | ✅ PASS | Work stays within Textual split layout; enhancements strengthen keyboard + visual cues. |
| II | Explicit Confirmation | ✅ PASS | Save continues to pipe through `ConfirmationDialog` diff preview before API calls. |
| III | Credential Security | ✅ PASS | No auth changes; still rely on `GROUPALARM_API_KEY` env var and sanitized logging. |
| IV | Framework Reuse | ✅ PASS | Editing + reminder validation leverage `framework.appointment.Appointment` + `AppointmentService`; label suggestions tap existing `LabelService`. |
| V | Export & Round-Trip | ✅ PASS | UX polish (dates/labels) does not alter exporter contract; list refresh after saves keeps exports accurate. |
| VI | Test Discipline | ✅ PASS | Plan adds pytest coverage for focus shortcuts, reminder validation, label autocomplete/diff preview. |

**Gate result: PASS** — proceed to Phase 0 once reminder-limit constraint is clarified.

## Project Structure

### Documentation (this feature)

```text
specs/002-tui-ux-enhancements/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 findings (to be generated)
├── data-model.md        # Phase 1 artifact (entities/flows)
├── quickstart.md        # Phase 1 artifact (operator guide)
├── contracts/           # Phase 1 API/UI contracts
└── tasks.md             # Phase 2 via /speckit.tasks (not part of this run)
```

### Source Code (repository root)

```text
cli/
├── app.py                      # App-level bindings; add new shortcuts
├── screens/
│   └── main_screen.py          # Focus routing, list/detail arrows, save preview hook
├── widgets/
│   ├── appointment_list.py     # Display German-formatted timestamps
│   ├── detail_panel.py         # Rebuilt editing form, reminder/label inputs
│   ├── filter_bar.py           # Full label directory, keyboard traversal
│   ├── confirmation_dialog.py  # Diff preview remains source of truth
│   └── ... (other supporting widgets)
├── services/
│   ├── appointment_service.py  # Validation + refresh triggers (minor tweaks)
│   └── label_service.py        # Provide autocomplete data + colors
└── styles/app.tcss             # Color accents + spacing tweaks

framework/
├── appointment.py              # Source of reminder + datetime fields (no schema change)
├── client.py                   # Already enforced API contracts (may add helper for reminder limits)
└── ...                         # Existing modules reused

tests/
├── test_app.py                 # Textual focus/shortcut coverage
├── test_detail_panel.py        # (New) reminder/unit validation, diff preview data
├── test_filter_bar.py          # (New) keyboard navigation + label availability
├── test_runner.py, etc.        # Existing suites unaffected
```

**Structure Decision**: Continue enhancing the `cli/` package (App → Screen → Widgets) without creating new top-level modules, ensuring `framework/` stays reusable (Constitution Principle IV). Tests live under `tests/` with new modules mirroring the widgets they validate.

## Complexity Tracking

No constitution violations — table intentionally omitted.

## Phase 0: Research — Complete

- **R-201** confirmed the backend reminder cap is 10 080 minutes, so the new reminder input can validate locally before save.  
- **R-202** defined focus helpers for the filter bar so `ctrl+/`, `ctrl+shift+/`, arrow keys, and Tab can move between start/end/search inputs without building a custom focus manager.  
- **R-203** established `LabelService` as the canonical source for autocomplete suggestions and warn-on-miss logic, independent of the filtered appointment set.  
- **R-204** standardized the German timestamp format (`dd.mm.yyyy HH:MM`) for both the list and detail panel, ensuring timezone conversions stay in `ZoneInfo`.  
- **R-205** decouples filter label availability from the current appointment subset, keeping time/search controls visible even when no appointments match.

See [research.md](research.md) for details and alternatives considered.
