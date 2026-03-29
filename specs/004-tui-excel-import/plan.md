# Implementation Plan: TUI Excel Import with Preview and Upload

**Branch**: `004-tui-excel-import` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-tui-excel-import/spec.md`

## Summary

Add an Excel import workflow to the TUI with a **three-tier mapping strategy**:

- **Tier 1 (P1, zero-config)**: The user presses Ctrl+O, enters a file path, and the system parses the Excel using a built-in default mapping that matches the TUI's own export format (`COLUMNS` from `exporter.py`). No `[import]` config section needed — Excel files exported by the TUI can be re-imported without any configuration.
- **Tier 2 (P1, Python mapping module)**: The user sets `mapping_file = "path/to/mapping.py"` in the `[import]` section of `.groupalarm.toml`. The system loads the referenced Python module via `importlib`, extracts its `mapping` and `defaults` dicts, and uses the existing `Mapper` class for full-power row transformation — lambdas, multi-column templates, `map_labels_from_participants()`, `parse_date()` with custom formats, `{"days_before": N}` relative dates, and literal constants. Existing mapping files (e.g. `Bereichsausbildungen_productive.py`) work without modification.
- **Tier 3 (P3, future wizard)**: An interactive column mapper wizard in the TUI that guides the user through mapping Excel columns to appointment fields and generates a Python mapping file for reuse as Tier 2. Deferred to a future iteration.

Parsed appointments are shown in a dedicated import-preview screen that reuses the existing list+detail split layout but with red text styling and a prominent "IMPORT PREVIEW" banner. The preview is read-only (no edit mode) but supports all existing filters (date, label, search). Pressing Ctrl+U uploads all appointments (create new / update existing) with per-appointment error handling. A summary screen reports success/failure counts and lists any failed items by name with error reason.

## Technical Context

**Language/Version**: Python ≥ 3.11  
**Primary Dependencies**: Textual (TUI framework), openpyxl (Excel read via pandas in `ExcelImporter`), pandas, requests (HTTP), tomllib/tomli_w (config)  
**Storage**: GroupAlarm REST API (remote), `.groupalarm.toml` (local config), Excel files (local import source)  
**Testing**: pytest (unit tests with monkeypatched HTTP, no live API calls)  
**Target Platform**: Windows / Linux / macOS terminal  
**Project Type**: CLI / TUI application  
**Performance Goals**: Preview screen renders within 5 seconds for files up to 500 rows; upload processes sequentially with per-appointment feedback  
**Constraints**: No network access in tests; environment-variable authentication only; import preview is strictly read-only  
**Scale/Scope**: Single-user TUI; typical import files 10–200 rows; single worksheet per file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Interactive CLI-First | **PASS** | New import workflow is fully keyboard-driven in the TUI — Ctrl+O to import, Ctrl+U to upload, arrow keys to navigate, filters available |
| II. Explicit Confirmation | **PASS** | The entire preview screen is an explicit confirmation step: user reviews all appointments visually before choosing to upload. The Ctrl+U upload shortcut triggers a confirmation dialog before sending. Escape cancels without any server-side effect |
| III. Credential Security | **PASS** | Upload uses the same `GroupAlarmClient` and `GROUPALARM_API_KEY` env var. No new credential paths introduced. File paths entered by the user are for local Excel files, not credentials |
| IV. Framework Reuse | **PASS** | Reuses `ExcelImporter` for file parsing, `Mapper` class for Tier 2 mapping module evaluation, `GroupAlarmClient.create_appointment()`/`update_appointment()` for upload, `ImporterToken` for token management. Config extended via `AppConfig` dataclass. Tier 2 reuses the exact same `mapping`/`defaults` dict format as existing `Runner`. `framework/` remains independently usable |
| V. Export & Round-Trip | **PASS** | Tier 1 default mapping matches the existing export column layout (`COLUMNS` in `exporter.py`). Excel files exported by the TUI can be imported without configuration changes, completing the round-trip. Tier 2 extends this to arbitrary file formats via Python mapping modules |
| VI. Test Discipline | **PASS** | All new modules (import service, import mapper, ImportPreviewScreen, ImportSummaryScreen, config extension) will have pytest unit tests with mocked data and no live API calls |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-tui-excel-import/
├── plan.md              # This file
├── research.md          # Phase 0 output — all unknowns resolved
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — verification guide
├── contracts/           # Phase 1 output — interface contracts
│   ├── import-service.md
│   ├── config-import-section.md
│   └── import-preview-screen.md
└── tasks.md             # Phase 2 output (not created by /speckit.plan)
```

### Source Code (repository root)

```text
framework/
├── config.py            # MODIFIED — add ImportConfig dataclass + [import] section parsing
├── importers.py         # EXISTING — ExcelImporter used as-is
├── importer_token.py    # EXISTING — ImporterToken used as-is
├── exporter.py          # EXISTING — COLUMNS list used for Tier 1 default mapping reference
├── mapper.py            # EXISTING — Mapper used for Tier 2 mapping module evaluation
├── client.py            # EXISTING — create_appointment/update_appointment used
└── appointment.py       # EXISTING — Appointment dataclass used

cli/
├── app.py               # MODIFIED — add Ctrl+O binding, action_import() delegation
├── screens/
│   ├── main_screen.py   # MODIFIED — add action_import() handler
│   ├── import_preview_screen.py  # NEW — import preview with red styling + banner
│   └── import_summary_screen.py  # NEW — upload results summary modal
├── services/
│   └── import_service.py         # NEW — Tier selection, module loading, parsing, upload
├── widgets/
│   ├── appointment_list.py       # EXISTING — reused in preview screen
│   ├── detail_panel.py           # EXISTING — reused in preview screen (read-only mode)
│   ├── filter_bar.py             # EXISTING — reused in preview screen
│   └── state.py                  # EXISTING — FilterControls/NavigationState reused
└── styles/
    └── app.tcss          # EXISTING — not modified (import uses screen-level DEFAULT_CSS per R2)

mappings/                          # CONVENTION — user mapping modules directory (not created by feature, but documented)
├── bereichsausbildungen.py        # EXAMPLE — existing mapping files can be placed here
└── dienst_ausbildungsplan.py      # EXAMPLE — and referenced from [import].mapping_file

tests/
├── test_import_service.py        # NEW — unit tests for tier selection, module loading, parsing, upload
├── test_import_preview_screen.py # NEW — unit tests for preview screen behaviour
├── test_import_config.py         # NEW — unit tests for config [import] section
└── test_import_summary.py        # NEW — unit tests for summary screen
```

**Structure Decision**: Follows the existing single-project layout. New screens go in `cli/screens/`, the new service goes in `cli/services/`, config changes extend the existing `framework/config.py`. No new packages or structural changes needed.

## Complexity Tracking

> No constitution violations — table not required.

## Post-Design Constitution Re-Check

*Re-evaluation after Phase 1 design artifacts are complete.*

| Principle | Status | Post-Design Notes |
|---|---|---|
| I. Interactive CLI-First | **PASS** | Design delivers: ImportFileDialog (keyboard input), ImportPreviewScreen (same split-view as MainScreen), arrow-key navigation, FilterBar integration. All keyboard-driven |
| II. Explicit Confirmation | **PASS** | Upload flow: Ctrl+U → ConfirmationDialog ("Upload N appointments? X new, Y updates") → user confirms → upload proceeds. Preview screen itself is a visual review step. Escape cancels. Batch confirmation follows constitution's "consolidated summary" exception |
| III. Credential Security | **PASS** | No new credential handling. Upload reuses existing `GroupAlarmClient` from `GROUPALARM_API_KEY`. File paths are local filesystem paths, not secrets. No credentials in logs or exports |
| IV. Framework Reuse | **PASS** | `ImportService` delegates to `ExcelImporter` (framework), `Mapper` (framework, Tier 2), `ImporterToken` (framework), `GroupAlarmClient.create/update_appointment()` (framework). Tier 2 loads the same `mapping`/`defaults` dicts used by `Runner`. `ImportConfig` extends `AppConfig` (framework). No duplication of existing logic. `framework/` package has no CLI imports |
| V. Export & Round-Trip | **PASS** | Tier 1 default import mapping exactly mirrors `exporter.COLUMNS`. Round-trip verified: export → import → preview matches original data. Tier 2 extends this for third-party files via Python mapping modules. Existing mapping files work unmodified |
| VI. Test Discipline | **PASS** | 4 new test files planned: `test_import_service.py`, `test_import_preview_screen.py`, `test_import_config.py`, `test_import_summary.py`. All use mocked data, no network. Follow existing monkeypatch patterns |

**Post-design gate result**: PASS — no violations. Design is consistent with all constitution principles.
