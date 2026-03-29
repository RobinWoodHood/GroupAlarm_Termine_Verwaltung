# GroupAlarm_Termine_Verwaltung Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-28

## Active Technologies
- Python ≥ 3.11 + Textual (TUI framework), requests (HTTP), tomllib/tomli_w (config) (003-tui-detail-ux-overhaul)
- GroupAlarm REST API (remote), `.groupalarm.toml` (local config) (003-tui-detail-ux-overhaul)
- Python ≥ 3.11 + Textual (TUI framework), openpyxl (Excel read via pandas in `ExcelImporter`), pandas, requests (HTTP), tomllib/tomli_w (config) (004-tui-excel-import)
- GroupAlarm REST API (remote), `.groupalarm.toml` (local config), Excel files (local import source) (004-tui-excel-import)

- Python ≥ 3.11 + Textual (TUI framework), Rich (rendering — bundled with Textual), openpyxl (Excel export), requests (HTTP), pandas (import pipeline), python-dateutil (date parsing), tomli/tomllib (config reading), tomli-w (config writing) (001-interactive-cli-tui)

## Project Structure

```text
src/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python ≥ 3.11: Follow standard conventions

## Recent Changes
- 004-tui-excel-import: Added Python ≥ 3.11 + Textual (TUI framework), openpyxl (Excel read via pandas in `ExcelImporter`), pandas, requests (HTTP), tomllib/tomli_w (config)
- 004-tui-excel-import: Added Python ≥ 3.11 + Textual (TUI framework), openpyxl (Excel read via pandas in `ExcelImporter`), pandas, requests (HTTP), tomllib/tomli_w (config)
- 003-tui-detail-ux-overhaul: Added Python ≥ 3.11 + Textual (TUI framework), requests (HTTP), tomllib/tomli_w (config)


<!-- MANUAL ADDITIONS START -->
## Mandatory Pre-Read

1. Before any edits, open [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) and skim the sections relevant to your task. This file lists every class, method, and function alongside their docstrings.
2. If you change or add Python classes/functions, re-run `python scripts/generate_api_docs.py --root . --output docs/API_REFERENCE.md` so the reference stays in sync.

Failure to review this document before making changes is considered out-of-process — please keep it open while you work.
<!-- MANUAL ADDITIONS END -->

## Specialized Skill Routing

- For any request mentioning GA-IMPORTER, GI importer token, importer hash, token-based matching, duplicate prevention, or import update identity, load and follow [`.github/skills/ga-importer-token/SKILL.md`](.github/skills/ga-importer-token/SKILL.md) before editing code.
- This skill defines the required token-first workflow for import updates and mandatory token injection for create paths.
