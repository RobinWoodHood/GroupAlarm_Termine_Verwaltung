# Research: TUI Excel Import with Preview and Upload

**Feature**: 004-tui-excel-import  
**Date**: 2026-03-28

## Research Tasks

### R1: How to build the import preview screen reusing existing widgets

**Decision**: Create `ImportPreviewScreen(Screen)` as a full screen (not modal) that reuses `AppointmentList`, `DetailPanel`, and `FilterBar` directly. The screen receives a list of parsed `Appointment` objects and manages its own in-memory filter/sort state via a lightweight adapter (no API calls needed for filtering).

**Rationale**: The existing `MainScreen` composes `FilterBar`, `AppointmentList`, and `DetailPanel` with service injection. The import preview has no backing API — all data is local. Rather than subclassing `MainScreen` (which is tightly coupled to `AppointmentService` and live data), a new screen that composes the same widgets with a local appointment list is cleaner. The `DetailPanel` already supports a read-only display mode (its default state before entering edit mode), so no edit-mode binding is needed on the preview screen.

**Alternatives considered**:
- Subclass `MainScreen` → rejected because `MainScreen` has many side-effects (API loading, edit mode, save, delete) that would need to be disabled. A clean screen with the same layout is simpler.
- Push a modal screen with a DataTable → rejected because it wouldn't reuse the existing detail panel and filter infrastructure.

### R2: How to apply red styling (per-screen CSS customisation)

**Decision**: Use Textual's per-screen CSS override. `ImportPreviewScreen` defines `DEFAULT_CSS` that targets `DataTable`, `DetailPanel`, and `Static` children with `color: red;`. The app-level `app.tcss` is not modified for import-specific rules. Instead, the screen-level CSS takes precedence for content within the preview.

**Rationale**: Textual CSS scoping works by specificity — screen-level `DEFAULT_CSS` applies only when that screen is active. This avoids polluting the global stylesheet. The `DataTable` cells, `Static` widgets in `DetailPanel`, and the `FilterBar` labels can all be overridden via descendant selectors (e.g., `ImportPreviewScreen DataTable { color: red; }`).

**Alternatives considered**:
- Add CSS classes to individual widgets → rejected because it requires modifying `AppointmentList` and `DetailPanel` to accept a "preview mode" parameter. Screen-level CSS is less invasive.
- Use Rich markup with `[red]` in cell text → rejected because it doesn't cover the detail panel and is fragile.

### R3: File path input approach

**Decision**: Use a Textual `Input` widget mounted in a simple modal dialog (`ImportFileDialog(ModalScreen[str | None])`) with a text field for the file path. The user types or pastes the path and presses Enter to confirm or Escape to cancel.

**Rationale**: Textual does not provide a native file picker widget. The existing codebase uses `Input` widgets extensively (filter bar, edit mode). A modal with a single `Input` follows the same UX pattern as the existing `ConfirmationDialog`. The dialog returns the path string or `None` on cancel.

**Alternatives considered**:
- Use `tkinter.filedialog.askopenfilename()` → rejected because mixing GUI toolkits with a terminal app is unreliable and breaks headless/SSH usage.
- Accept file path as a CLI argument → rejected because the spec requires triggering import from within the running TUI.
- Prompt via `self.app.notify` + stdin → rejected because Textual captures stdin for its own event loop.

### R4: Default column mapping for TUI-exported Excel files

**Decision**: Define a `DEFAULT_IMPORT_COLUMNS` dict that maps the 13 COLUMNS from `exporter.py` directly to `Appointment` fields. This serves as the fallback when no `[import]` section is configured. The mapping handles:
- `name` → `Appointment.name`
- `description` → `Appointment.description`
- `startDate` → ISO 8601 string → `datetime` (using `dateutil.parser.isoparse`)
- `endDate` → ISO 8601 string → `datetime`
- `organizationID` → `int`
- `labelIDs` → comma-separated string → `list[int]`
- `isPublic` → `bool`
- `reminder` → `int | None`
- `notificationDate` → ISO 8601 string → `datetime | None`
- `feedbackDeadline` → ISO 8601 string → `datetime | None`
- `timezone` → `str`
- `groupalarm_id` → `int | None` (stored on `Appointment.id`)
- `ga_importer_token` → `str | None` (re-appended to description if present)

**Rationale**: The export format uses ISO 8601 datetimes and comma-separated label IDs. The default mapping must parse these without any config. The existing `Mapper` class supports callable specs, which can handle the ISO parsing and label splitting.

**Alternatives considered**:
- Require the user to always configure `[import]` → rejected because the spec explicitly requires zero-config for TUI-exported files.
- Auto-detect columns by header names → rejected because it adds fragile heuristics. A fixed default mapping is deterministic.

### R5: Config file extension — `[import]` section structure (Three-Tier Approach)

**Decision**: The `[import]` section in `.groupalarm.toml` is simplified to support the three-tier mapping strategy. Instead of embedding complex column mappings in TOML (`[import.columns]`), the config points at an external Python mapping module file. The tier selection logic is:

- **Tier 1** (no `[import]` section or empty): Use built-in default mapping matching TUI export `COLUMNS`.
- **Tier 2** (`mapping_file` set): Load the referenced Python module, extract `mapping` and `defaults` dicts, use `Mapper` class.
- **Tier 3** (future): Interactive wizard generates a Python mapping file.

```toml
# Tier 1: No [import] section needed — zero-config round-trip

# Tier 2: Point at an existing Python mapping module
[import]
mapping_file = "mappings/bereichsausbildungen.py"  # path relative to project root or absolute
sheet_name = "Termine"                              # optional, defaults to first sheet
```

**Rationale**: TOML cannot express the full power of the existing `Mapper` class — lambdas, multi-column templates, `map_labels_from_participants()`, `parse_date()` with custom formats, `{"days_before": N}` relative dates. Rather than inventing a TOML DSL that approximates a subset of these capabilities, the config simply references a Python file that export the same `mapping` and `defaults` dicts used by the existing `Runner`. This approach:
- Preserves backward compatibility (existing mapping scripts work as-is)
- Respects Constitution Principle IV (Framework Reuse — leverages `Mapper`)
- Keeps the config file simple and declarative
- Avoids security risks of embedding code in TOML

**Alternatives considered**:
- Complex `[import.columns]` TOML sub-tables (str=column name, int=literal, bool=literal) → rejected because it cannot express lambdas, multi-column templates, label token mapping, or per-field date formats. Real-world usage (e.g. `Bereichsausbildungen_productive.py`) requires all of these.
- Per-column date format in TOML → rejected as insufficient; real mappings need callable-based date parsing with different formats per field.
- Separate YAML/JSON config for import mappings → rejected; adds a new format without solving the expressiveness problem. Python dict is the right abstraction.

### R6: Upload orchestration — create vs. update decision

**Decision**: The import service iterates over appointments and for each:
1. If `appointment.id` is set (from `groupalarm_id` column) → call `client.update_appointment()`
2. If `appointment.id` is `None` → call `ImporterToken.ensure_token(appointment)` then `client.create_appointment()`
3. Wrap each call in try/except, recording the outcome (created/updated/failed) with error message
4. On `AppointmentNotFound` (404 on update) → fall back to create (matching existing runner behaviour)

In dry-run mode, payloads are logged but no HTTP calls are made (handled by `GroupAlarmClient` internally).

**Rationale**: This matches the existing `Runner.run()` logic but adapted for the TUI context (no source file write-back needed, results collected in memory for the summary screen).

**Alternatives considered**:
- Batch upload via a single API call → rejected because GroupAlarm API does not support batch operations.
- Parallel upload with asyncio → rejected because the API uses `requests` (synchronous) and parallel writes could cause rate-limiting. Sequential is safer and simpler.

### R7: Confirmation before upload

**Decision**: When the user presses Ctrl+U, show a `ConfirmationDialog` displaying the count of appointments to upload (X to create, Y to update) before proceeding. This satisfies Constitution Principle II (Explicit Confirmation).

**Rationale**: The preview itself is not the confirmation — it's a review step. The upload button must still prompt for explicit confirmation per the constitution's NON-NEGOTIABLE requirement. A consolidated summary ("Create 5, Update 12 — proceed?") respects the batch exception in the constitution.

**Alternatives considered**:
- Confirm each appointment individually → rejected for large files (50+ rows would be tedious). The constitution allows "a consolidated summary the user can accept or reject" for batch operations.
- No confirmation, just upload → rejected as it directly violates Constitution Principle II.

### R8: Summary screen design

**Decision**: `ImportSummaryScreen(ModalScreen[None])` as a dismissable modal. Layout:
- Title: "Import Summary" (or "Import Summary (DRY-RUN)" in dry-run mode)
- Stats line: "Total: N | Created: X | Updated: Y | Failed: Z"
- If failures exist: scrollable list of failed appointments with name + error
- Dismiss: Escape or Enter → pops modal, triggers `_load_appointments()` on `MainScreen` to refresh

**Rationale**: Follows the `HelpScreen` modal pattern. A modal is appropriate because it overlays the preview screen and dismisses back to the normal flow. On dismiss, the app pops back to `MainScreen` (the preview screen is also dismissed) and the main screen reloads from the API.

**Alternatives considered**:
- In-place notification → rejected because a single notification cannot display a list of failures.
- Replace preview screen content → rejected because the user might want to see the preview data alongside results.

---

### R9: Python mapping module loading (Tier 2 — `importlib`)

**Decision**: Use `importlib.util.spec_from_file_location()` + `module_from_spec()` to dynamically load a user-provided Python mapping file. Extract `mapping` (required) and `defaults` (optional) top-level dicts from the loaded module. Pass these to the existing `Mapper` class.

**Rationale**: `importlib.util.spec_from_file_location()` loads a `.py` file from an arbitrary filesystem path without requiring it to be on `sys.path` or inside a package. This matches the user's workflow — mapping files live alongside the project (e.g. `Bereichsausbildungen_productive.py`). The loaded module's namespace is inspected for `mapping` and `defaults` attributes, which are the same dicts the existing `Runner` consumes.

**Security considerations**: Mapping files are trusted user-authored code running in the same process as the TUI. This is the same trust model as the existing `Runner` — users already execute these files via `python Bereichsausbildungen_productive.py`. No sandboxing is needed. The system validates:
- File exists and has `.py` extension
- Module loads without SyntaxError
- Module exports a `mapping` attribute that is a dict

**Error handling**:
- `FileNotFoundError` → "Mapping file not found: {path}"
- `SyntaxError` → "Syntax error in mapping file: {path}: {details}"
- Missing `mapping` attribute → "Mapping file must export a 'mapping' dict: {path}"
- Import-time exception → "Error loading mapping file: {path}: {details}"

**Alternatives considered**:
- `exec()` the file → rejected as less structured than `importlib`; harder to get clean namespace isolation.
- `runpy.run_path()` → viable but returns a dict instead of a module, making attribute access less ergonomic. `importlib` is the standard approach.
- Require mapping files to be installed packages → rejected; too heavy for single-file configs.

---

### R10: Tier selection logic in `ImportService.parse_excel()`

**Decision**: The tier is determined automatically by the `ImportConfig`:

1. **Tier 2** (highest priority): If `import_config.mapping_file` is set → load the Python module, use `Mapper` with the loaded `mapping`/`defaults` dicts.
2. **Tier 1** (default): If `import_config` is `None` or `mapping_file` is not set → use built-in `DEFAULT_IMPORT_COLUMNS` mapping.
3. **Tier 3** (future): If neither Tier 1 nor Tier 2 produces valid results (headers don't match default mapping and no mapping_file) → offer to launch wizard. For now, this tier raises a `ValueError` with guidance to create a mapping file.

**Rationale**: Explicit config wins over implicit detection. If the user has a `mapping_file`, that's the authoritative source. If they don't, the default mapping for TUI export format is a safe bet. The wizard tier is deferred to a future iteration.

**Alternatives considered**:
- Auto-detect tier by inspecting Excel headers → rejected because ambiguous headers could match partially, leading to silent data corruption. Explicit config is safer.
- Require explicit `tier = 1` or `tier = 2` in config → rejected as unnecessary indirection; the presence/absence of `mapping_file` is sufficient.

---

### R11: Interactive column mapper wizard design (Tier 3 — future)

**Decision**: Defer full design to a separate spec iteration. High-level concept:

1. A `ColumnMapperWizard(Screen)` presents steps:
   - Step 1: Show detected Excel columns, let user map each to an appointment field (or "skip")
   - Step 2: For date fields, let user specify the format string
   - Step 3: For label fields, let user choose direct IDs or token mapping
   - Step 4: Preview a sample row with the mapping applied
   - Step 5: Save the generated `mapping` dict as a `.py` file
2. The wizard outputs a valid Python mapping file that can be used for Tier 2
3. The config is updated with `mapping_file` pointing to the generated file

**Rationale**: The wizard is a P3 enhancement — nice to have but not blocking the core import workflow. Tier 1 + Tier 2 cover all existing use cases. The wizard's main value is onboarding users who don't want to write Python. By generating a Python file (not a proprietary format), the output is fully compatible with Tier 2 and the existing `Runner`.

**Alternatives considered**:
- Generate TOML instead of Python → rejected because TOML cannot express the full mapping power. Generating Python directly ensures round-trip compatibility.
- Interactive prompt-based wizard (non-TUI) → rejected because the constitution requires Interactive CLI-First (TUI-based interaction).
