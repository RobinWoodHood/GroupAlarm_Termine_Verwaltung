# Quickstart: TUI Excel Import with Preview and Upload

**Feature**: 004-tui-excel-import  
**Date**: 2026-03-28

## Prerequisites

- Python ≥ 3.11 with virtual environment activated
- `GROUPALARM_API_KEY` environment variable set
- `.groupalarm.toml` with `organization_id` configured
- An Excel file to import (e.g., one previously exported by the TUI via `x` key)

## Quick Verification

### 1. Import a TUI-exported Excel (zero-config)

```bash
# Start the TUI
python groupalarm_cli.py

# In the TUI:
# 1. Press Ctrl+O               → Import file dialog appears
# 2. Type the Excel file path    → e.g. appointments_2026-03-28.xlsx
# 3. Press Enter                 → Preview screen loads
#
# Expected:
# - Red "⚠ IMPORT PREVIEW" banner at top
# - All appointment text in red
# - List on left, detail panel on right
# - Arrow keys navigate the list; detail updates on highlight
```

### 2. Navigate and filter the preview

```
# In the preview screen:
# - Up/Down arrows  → move through appointment list
# - Ctrl+F          → focus search input
# - Ctrl+T          → focus date filter
# - Label buttons   → toggle label filters
# - Escape          → cancel import, return to normal view
#
# Expected:
# - Filters work identically to the main screen
# - Detail panel shows all fields read-only (no 'e' edit mode)
```

### 3. Upload (or dry-run)

```bash
# If using --dry-run:
python groupalarm_cli.py --dry-run

# In the preview screen:
# - Press Ctrl+U                → Confirmation dialog shows create/update counts
# - Press 'y' or Enter          → Upload begins
#
# Expected:
# - Summary screen appears after upload
# - Shows: Total / Created / Updated / Failed
# - Failed items listed with name + error
# - Press Escape or Enter to dismiss → returns to normal main view
```

### 4. Import with a Python mapping module (Tier 2)

```toml
# Add to .groupalarm.toml:
[import]
mapping_file = "Bereichsausbildungen_productive.py"   # or any .py file exporting a `mapping` dict
sheet_name = "Termine"                                 # optional
```

The referenced Python file must export a `mapping` dict (and optional `defaults` dict) in the same format used by the existing framework `Runner`:

```python
# mappings/bereichsausbildungen.py
from framework.label_mapper import map_labels_from_participants, DEFAULT_TOKEN_MAP

mapping = {
    "name": lambda r, helpers: f"{r['[Nr. laut Katalog]']} {r['Lehrgang **']}",
    "startDate": lambda r, helpers: helpers["parse_date"](
        r.get("[Beginn]"), fmt="%d.%m.%Y %H:%M", tz="Europe/Berlin"
    ),
    "endDate": lambda r, helpers: helpers["parse_date"](
        r.get("[Ende]"), fmt="%d.%m.%Y %H:%M", tz="Europe/Berlin"
    ),
    "organizationID": 13915,
    "labelIDs": lambda r, helpers: map_labels_from_participants(
        r.get("Teilnehmer"), DEFAULT_TOKEN_MAP
    ),
    "isPublic": False,
}

defaults = {"timezone": "Europe/Berlin", "start_hour": 19, "end_hour": 22}
```

```bash
# Start TUI, press Ctrl+O, enter path to your custom Excel/CSV file
# Preview should show appointments mapped using the Python module's mapping logic
# Banner shows: ⚠ IMPORT PREVIEW — filename.xlsx (N appointments) [Tier 2: bereichsausbildungen.py]
```

> **Note**: Existing scripts like `Bereichsausbildungen_productive.py` and `example_usage.py` already export `mapping` and `defaults` dicts — they can be used directly as Tier 2 mapping modules without any modifications.

### 4b. Tier 3 — Interactive wizard (future)

The interactive column mapper wizard is planned for a future iteration. When available, it will guide users through mapping columns visually and generate a Python mapping file for Tier 2 reuse.

### 5. Run tests

```bash
pytest tests/test_import_service.py tests/test_import_preview_screen.py tests/test_import_config.py tests/test_import_summary.py -v
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "No appointments found in file" | Excel has no data rows or sheet_name filter mismatches | Check Excel file has data rows; verify `sheet_name` in `[import]` matches |
| "Mapping file not found" | `mapping_file` path in config is wrong | Check the path is correct (relative to project root or absolute) |
| "Syntax error in mapping file" | Python syntax error in your mapping module | Fix the syntax error in the referenced `.py` file |
| "Mapping file must export a 'mapping' dict" | The Python file doesn't have a `mapping` variable | Add `mapping = { ... }` to your mapping module |
| Preview shows wrong dates | Date format or parse logic in mapping module is incorrect | Fix `helpers["parse_date"]()` call or date format string in your mapping module |
| Upload fails with 401 | API key invalid or expired | Check `GROUPALARM_API_KEY` environment variable |
| "Skipped N rows" notification | Rows with missing name or start date | Check source Excel for incomplete rows |
