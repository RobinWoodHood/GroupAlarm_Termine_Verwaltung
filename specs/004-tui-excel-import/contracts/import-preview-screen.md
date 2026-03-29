# Contract: Import Preview Screen

**Module**: `cli/screens/import_preview_screen.py`  
**Feature**: 004-tui-excel-import

## Purpose

Display a dedicated import preview screen with the same list+detail layout as `MainScreen`, but styled in red, read-only, and backed by local in-memory data (no API calls for listing). Provides filter/search/navigation capabilities and the Ctrl+U upload trigger.

## Class: `ImportPreviewScreen(Screen)`

### Constructor

```python
def __init__(
    self,
    import_session: ImportSession,
    client: GroupAlarmClient,
    label_service: LabelService,
    config: AppConfig,
    dry_run: bool = False,
)
```

| Parameter | Purpose |
|-----------|---------|
| `import_session` | Parsed appointments + metadata from `ImportService.parse_excel()` |
| `client` | For upload operations |
| `label_service` | For label name resolution in list/detail/filter |
| `config` | For timezone, organization_id |
| `dry_run` | For upload behaviour |

### Key Bindings

| Key | Action | Description |
|-----|--------|-------------|
| `ctrl+u` | `action_upload` | Begin upload workflow (confirmation → upload → summary) |
| `escape` | `action_cancel` | Cancel preview, return to main screen |
| `left` | `action_focus_list_panel` | Focus the appointment list |
| `right` | `action_focus_detail_panel` | Focus the detail panel |
| `ctrl+f` | `action_search` | Focus search input in filter bar |
| `ctrl+t` | `action_focus_start_filter` | Focus date filter |

**Not bound**: `e` (edit mode), `ctrl+s` (save), `n` (new), `d` (delete), `x` (export), `i` (tokens)

### Layout

```
┌──────────────────────────────────────────────────────┐
│ ⚠ IMPORT PREVIEW — {filename} ({N} appointments)    │  ← red banner, always visible
├──────────────────────────────────────────────────────┤
│ [FilterBar: labels, date range, search]              │
├─────────────────────────────┬────────────────────────┤
│ AppointmentList (red text)  │ DetailPanel (read-only) │
│                             │ (red text)              │
│ ↑↓ navigate                │ shows highlighted appt  │
│                             │                         │
└─────────────────────────────┴────────────────────────┘
```

### CSS Styling (screen-level)

```css
ImportPreviewScreen {
    layout: vertical;
}

#import-banner {
    dock: top;
    height: 1;
    background: darkred;
    color: white;
    text-align: center;
    text-style: bold;
}

ImportPreviewScreen DataTable {
    color: red;
}

ImportPreviewScreen DataTable > .datatable--cursor {
    background: darkred;
    color: white;
}

ImportPreviewScreen DetailPanel .field-label {
    color: red;
}

ImportPreviewScreen DetailPanel .read-only-field {
    color: red;
}
```

### Behaviour

#### On Mount
1. Display banner: `⚠ IMPORT PREVIEW — {filename} ({N} appointments) [Tier {1|2}: {mapping description}]`
2. If `import_session.skipped_rows` is non-empty → show notification: `Skipped {N} rows (parse errors)`
3. Populate `AppointmentList` with `import_session.appointments`
4. Build label directory from imported appointments' label IDs (resolved via `label_service`)
5. Populate `FilterBar` with available labels
6. Focus the appointment list

#### Navigation (highlight)
- `on_appointment_highlighted(event)` → call `detail_panel.show_appointment()` in read-only mode
- No `on_appointment_selected` handling (no edit mode)

#### Filtering
- Reuse `FilterControls` state object
- Apply filters locally: label filter, date filter, search text → all applied in-memory to `import_session.appointments`
- Re-populate `AppointmentList` after each filter change

#### Upload (`action_upload`)
1. Collect currently filtered appointments
2. Count create vs. update (based on `appointment.id` being None vs. set)
3. Push `ConfirmationDialog` with summary: "Upload {N} appointments? ({X} new, {Y} updates)"
4. On confirm → call `ImportService.upload()` with the filtered list
5. On completion → push `ImportSummaryScreen` with results
6. On summary dismiss → pop both screens (return to `MainScreen`), trigger refresh

#### Cancel (`action_cancel`)
1. Pop the preview screen
2. Return to `MainScreen` — no data modified

---

## Class: `ImportFileDialog(ModalScreen[str | None])`

**Module**: `cli/screens/import_preview_screen.py` (co-located)

Simple modal for entering the Excel file path.

### Layout

```
┌────────────────────────────────┐
│   Import Excel File            │
│                                │
│   Path: [___________________]  │
│                                │
│   [Import]  [Cancel]           │
└────────────────────────────────┘
```

### Behaviour

- `Input` widget with placeholder "Path to Excel file (.xlsx)"
- Enter or Import button → validate file exists → `dismiss(path_string)`
- Escape or Cancel button → `dismiss(None)`
- If file does not exist → show error notification, keep dialog open

---

## Class: `ImportSummaryScreen(ModalScreen[None])`

**Module**: `cli/screens/import_summary_screen.py`

### Layout

```
┌────────────────────────────────────────┐
│   Import Summary                       │
│                                        │
│   Total: 20 | Created: 12 | Updated: 6│
│   Failed: 2                            │
│                                        │
│   Failed appointments:                 │
│   ├─ "Training A" — 404 Not Found     │
│   └─ "Meeting B"  — Validation error  │
│                                        │
│   [OK]                                 │
└────────────────────────────────────────┘
```

### Bindings

| Key | Action |
|-----|--------|
| `escape` | dismiss |
| `enter` | dismiss |

### Behaviour

- Receives `ImportSummary` in constructor
- Displays aggregate counts
- If `dry_run` → title includes "(DRY-RUN)"
- If failures → scrollable list of failed items with name + error
- On dismiss → returns `None` (caller handles screen navigation)

---

## Future: `ColumnMapperWizard(Screen)` — Tier 3 (not in this iteration)

**Module**: `cli/screens/column_mapper_wizard.py` (future)

Placeholder for the interactive column mapper wizard. When the imported file doesn't match the Tier 1 default mapping and no Tier 2 `mapping_file` is configured, this wizard will guide the user through:

1. Displaying detected Excel column headers
2. Mapping each column to an appointment field (or "skip")
3. Configuring date format strings for date fields
4. Choosing label resolution strategy (direct IDs or token mapping)
5. Previewing a sample row with the mapping applied
6. Generating and saving a Python mapping file → becomes Tier 2 for future runs

**Not implemented in this iteration** — raises `ValueError` with guidance to create a mapping file manually.
