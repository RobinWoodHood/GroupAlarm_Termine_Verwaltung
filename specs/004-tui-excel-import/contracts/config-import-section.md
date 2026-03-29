# Contract: Config Import Section

**Module**: `framework/config.py`  
**Feature**: 004-tui-excel-import

## Purpose

Extend the existing `AppConfig` and TOML loading/saving to support an `[import]` configuration section. The config section is deliberately minimal — it controls which mapping tier to use and optional file-level settings. Complex column mapping logic lives in external Python mapping modules (Tier 2), not in TOML.

## Three-Tier Mapping Strategy

| Tier | Config State | Behaviour |
|------|-------------|-----------|
| **Tier 1** (default) | No `[import]` section, or `mapping_file` not set | Built-in default mapping matching TUI export `COLUMNS`. Zero-config round-trip. |
| **Tier 2** (module) | `mapping_file = "path/to/mapping.py"` | Load Python module, extract `mapping` + `defaults` dicts, use `Mapper` class. Full framework power. |
| **Tier 3** (wizard, future) | N/A — triggered when file doesn't match Tier 1 and no Tier 2 configured | Interactive wizard generates a Python mapping file → becomes Tier 2 for future runs. |

## Data Structures

### `ImportConfig` (new frozen dataclass)

```python
@dataclass(frozen=True)
class ImportConfig:
    mapping_file: str | None = None   # path to Python mapping module (Tier 2)
    sheet_name: str | None = None     # Excel sheet name, None = first sheet
```

### `AppConfig` (extended)

```python
@dataclass
class AppConfig:
    # ... existing fields unchanged ...
    import_config: ImportConfig | None = None  # NEW
```

## TOML Format

```toml
# Tier 1: No [import] section needed — zero-config for TUI export round-trip
# (The system uses the built-in DEFAULT_IMPORT_COLUMNS mapping)

# Tier 2: Point at a Python mapping module
[import]
mapping_file = "mappings/bereichsausbildungen.py"  # relative to project root or absolute
sheet_name = "Termine"                              # optional, defaults to first sheet
```

### Example Python mapping module (`mappings/bereichsausbildungen.py`)

The referenced file exports a `mapping` dict and optional `defaults` dict — the same format used by the existing `Runner`:

```python
from framework.label_mapper import map_labels_from_participants, DEFAULT_TOKEN_MAP

mapping = {
    "name": lambda r, helpers: f"{r['[Nr. laut Katalog]']} {r['Lehrgang **']}",
    "description": lambda r, helpers: (
        f"Ort: {r.get('Veranstaltungs-Adresse')}\n"
        f"Bemerkung: {r.get('[Bemerkung]')}\n"
        f"Melde-Frist: {r.get('Melde-Frist')}"
    ),
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
    "reminder": 60 * 24 * 7,
    "feedbackDeadline": lambda r, helpers: helpers["parse_date"](
        r.get("Melde-Frist"), fmt="%d.%m.%Y", tz="Europe/Berlin"
    ),
    "isPublic": False,
}

defaults = {
    "timezone": "Europe/Berlin",
    "start_hour": 19,
    "end_hour": 22,
}
```

## Loading Behaviour

In `load_config()`:

1. Read `data.get("import", None)`
2. If `None` → `config.import_config = None` (Tier 1 — use default mapping)
3. If present:
   - Extract `mapping_file = import_section.get("mapping_file")`
   - Extract `sheet_name = import_section.get("sheet_name")`
   - Create `ImportConfig(mapping_file=mapping_file, sheet_name=sheet_name)`

## Saving Behaviour

In `save_config()`:

1. If `config.import_config is not None`:
   - Write `[import]` section with `mapping_file` and `sheet_name` (if not None)
2. If `config.import_config is None`: do not write `[import]` section

## Module Loading (performed by `ImportService`, not `config.py`)

The `ImportConfig` stores the path only. Actual module loading is handled by `ImportService.parse_excel()`:

1. Resolve `mapping_file` path (relative to project root if not absolute)
2. Validate file exists and has `.py` extension
3. Load via `importlib.util.spec_from_file_location()` + `module_from_spec()`
4. Extract `mapping` (required dict) and `defaults` (optional dict) attributes
5. Pass to `Mapper(mapping, defaults)` for row transformation

## Backward Compatibility

- Existing configs without `[import]` continue to work identically
- `load_config()` returns `import_config=None` when section is absent
- `save_config()` omits `[import]` when field is `None`
- No changes to `[general]` or `[defaults]` sections
- Existing Python mapping files (e.g. `Bereichsausbildungen_productive.py`) work as-is — they already export `mapping` and `defaults` dicts in the required format
