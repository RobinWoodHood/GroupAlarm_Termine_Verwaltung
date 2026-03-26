# Implementation Plan: Interactive CLI TUI for GroupAlarm Appointment Management

**Branch**: `001-interactive-cli-tui` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-interactive-cli-tui/spec.md`

## Summary

Build an interactive terminal UI (TUI) using Textual that exposes all existing `framework/` capabilities through a split-view interface. Users browse and filter appointments by label (toggle list with typeahead) and date range, sort by start date or name, search by text, select one for inline editing with unsaved-changes protection, export filtered results to round-trip-compatible Excel (with overwrite prompt), and create/delete appointments — all with explicit confirmation before any server mutation. Labels are displayed by name and color throughout (never raw IDs). The API key is read from `GROUPALARM_API_KEY` env var; org ID and display defaults (including appointment duration) are persisted in `.groupalarm.toml`. Dry-run mode shows a persistent banner. Graceful shutdown handles Ctrl+C and unsaved changes. All significant events are logged to file.

## Technical Context

**Language/Version**: Python ≥ 3.11  
**Primary Dependencies**: Textual (TUI framework), Rich (rendering — bundled with Textual), openpyxl (Excel export), requests (HTTP), pandas (import pipeline), python-dateutil (date parsing), tomli/tomllib (config reading), tomli-w (config writing)  
**Storage**: Local config file `.groupalarm.toml` (org ID, default date range, default label filters). No database.  
**Testing**: pytest with monkeypatch for HTTP mocking, tmp_path for file fixtures. Textual's pilot testing API for TUI widget tests.  
**Target Platform**: Windows (primary), macOS, Linux — any terminal supporting 256 colors and Unicode  
**Project Type**: CLI / TUI application extending existing library  
**Performance Goals**: Startup to list display < 5s; export 100 appointments < 10s (SC-001, SC-003, SC-006)  
**Constraints**: No network access in tests; API key never in logs/exports/stack traces (sanitized); all mutations require confirmation; UI locked during in-flight API calls  
**Scale/Scope**: Single-user desktop tool; typical appointment count 10–500 per query window

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| I | Interactive CLI-First | ✅ PASS | Split-view TUI with Textual, keyboard+mouse, footer bar, label/date filtering — spec FR-002 through FR-007, FR-017, FR-020 |
| II | Explicit Confirmation (NON-NEGOTIABLE) | ✅ PASS | Every mutation requires confirmation dialog with diff/payload — spec FR-008, FR-009, FR-010 |
| III | Credential Security | ✅ PASS | `GROUPALARM_API_KEY` env var only, no prompts/args/config, no logging — spec FR-001, FR-016 |
| IV | Framework Reuse | ✅ PASS | CLI builds on `framework/` library; `delete_appointment` added to `GroupAlarmClient` first — spec FR-024, Assumptions |
| V | Export & Round-Trip | ✅ PASS | Excel export with `groupalarm_id` + `ga_importer_token` columns — spec FR-011, FR-012 |
| VI | Test Discipline | ✅ PASS | pytest, monkeypatch HTTP mocking, no network in tests — spec Assumptions, constitution |

**Gate result: PASS** — no violations, no complexity justification needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-interactive-cli-tui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
framework/                    # Existing library — extended, not replaced
├── __init__.py
├── appointment.py            # Extend: add recurrence field
├── client.py                 # Extend: add delete_appointment, list labels
├── config.py                 # NEW: .groupalarm.toml read/write
├── exporter.py               # NEW: appointment → Excel export
├── importer_token.py
├── importers.py
├── label_mapper.py
├── mapper.py
├── runner.py
└── utils.py

cli/                          # NEW: TUI application package
├── __init__.py
├── app.py                    # Textual App subclass, entry point
├── screens/
│   ├── __init__.py
│   ├── main_screen.py        # Split-view: list + detail panels
│   └── help_screen.py        # ? help overlay
├── widgets/
│   ├── __init__.py
│   ├── appointment_list.py   # Scrollable list with selection
│   ├── detail_panel.py       # Editable appointment detail form
│   ├── filter_bar.py         # Label + date range filter controls
│   ├── confirmation_dialog.py # Mutation confirmation with diff
│   └── footer.py             # Contextual key hints
├── services/
│   ├── __init__.py
│   ├── appointment_service.py # Async bridge to GroupAlarmClient
│   └── label_service.py      # Label fetch + cache
└── styles/
    └── app.tcss              # Textual CSS for layout and theming

tests/
├── test_client.py            # Existing — extend with delete tests
├── test_config.py            # NEW: config read/write tests
├── test_exporter.py          # NEW: Excel export tests
├── test_importer_token.py
├── test_importers.py
├── test_label_mapper.py
├── test_mapper.py
├── test_runner.py
├── test_utils.py
├── test_app.py               # NEW: Textual pilot tests for TUI
└── test_confirmation.py      # NEW: confirmation dialog behavior

groupalarm_cli.py             # NEW: CLI entry point (python groupalarm_cli.py)
```

**Structure Decision**: Preserve existing `framework/` as library; add new `cli/` package for TUI. Entry point is `groupalarm_cli.py` at repo root. This keeps the library independently usable (Constitution Principle IV) while providing the new interactive interface.

## Phase 0: Research — Complete

**Output**: [research.md](research.md) — 10 research items resolved:
- R-001: Textual layout patterns (Horizontal + VerticalScroll)
- R-002: Modal confirmation dialogs (ModalScreen[bool])
- R-003: Async API operations (@work(thread=True) with requests)
- R-004: TUI testing with Pilot API
- R-005: Label API endpoint (GET /labels?organization={id}&all=true — simpler than /label/organizations)
- R-006: Config file format (.groupalarm.toml with tomllib/tomli-w)
- R-007: Excel export round-trip compatibility (openpyxl, ImporterToken)
- R-008: Delete appointment API contract (DELETE /appointment/{id} with strategy+time)
- R-009: Date/time input (Input with restrict regex + DateTimeValidator)
- R-010: Recurring appointments V1 scope (read-only display, strategy for update/delete)

All NEEDS CLARIFICATION items resolved. No open unknowns.

## Phase 1: Design & Contracts — Complete

**Outputs**:
- [data-model.md](data-model.md) — 4 entities: Appointment (extended with recurrence), Label, AppConfig (with appointment_duration_hours), ExportFile
- [contracts/client-extensions.md](contracts/client-extensions.md) — delete_appointment, list_labels, update_appointment strategy param
- [contracts/config-module.md](contracts/config-module.md) — AppConfig (5 fields), load_config, save_config
- [contracts/exporter-module.md](contracts/exporter-module.md) — export_appointments with round-trip column mapping
- [contracts/cli-application.md](contracts/cli-application.md) — CLI args (--org-id, --dry-run, --verbose), 13 key bindings, screen flow with unsaved changes guard
- [quickstart.md](quickstart.md) — installation, config, usage guide

**Post-checklist review updates** (2026-03-22): Spec expanded from 25 to 35 FRs based on full-review checklist feedback. Key additions: label filter mechanics (toggle list + typeahead), sort/search, unsaved changes guard, concurrent API call handling, logging requirements, graceful shutdown, API key sanitization scope, config file permissions, dry-run visuals, export overwrite handling, default appointment duration (4h, configurable). All contracts and data-model updated accordingly.

## Constitution Check — Post-Design

| # | Principle | Status | Post-Design Evidence |
|---|-----------|--------|---------------------|
| I | Interactive CLI-First | ✅ PASS | Horizontal split with VerticalScroll list + Vertical detail. Footer BINDINGS. Filter bar with toggle list + typeahead. Sort/search. 13 key bindings. Dry-run banner. Help in empty detail panel. |
| II | Explicit Confirmation | ✅ PASS | ModalScreen[bool] for all mutations. Strategy selector for recurring. Side-by-side diff for updates. Unsaved changes guard on navigation/quit (FR-029). |
| III | Credential Security | ✅ PASS | Env var only. Exit(1) if missing. API key sanitized from all logs/stack traces/crash dumps (FR-016). Config file has restrictive permissions, no API key (FR-033). |
| IV | Framework Reuse | ✅ PASS | delete_appointment + list_labels + strategy in GroupAlarmClient first. Config + exporter in framework/. CLI imports framework/. |
| V | Export & Round-Trip | ✅ PASS | 13-column export with groupalarm_id + ga_importer_token. Default filename pattern. Overwrite prompt (FR-011). |
| VI | Test Discipline | ✅ PASS | Pilot API for TUI. Monkeypatch HTTP. Config+exporter test files planned. No network. |

**Post-design gate: PASS** — no violations, no new complexity exceptions.

## Complexity Tracking

No constitution violations — table intentionally left empty.
