# Data Model: TUI UX Enhancements

**Date**: 2026-03-23 | **Status**: Complete

## Entities

### 1. NavigationState

**Purpose**: Track which pane (list, detail, filter bar) currently has focus so arrow icons, keyboard shortcuts, and Tab order stay in sync.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `active_panel` | `Literal["list", "detail", "filter"]` | Yes | Controls which pane highlights its left/right arrow affordance. |
| `focused_widget_id` | `Optional[str]` | No | Stores the last-focused widget ID so focus can be restored after dialogs. |
| `list_cursor_key` | `Optional[int]` | No | Caches the appointment ID at the list cursor for re-selection after edits/saves. |
| `filter_focus_index` | `int` | No (default 0) | Sequential index for filter controls to support arrow-key cycling without relying on DOM order. |

**Transitions**:
- Arrow buttons (`←` / `→`) or bindings trigger `set_active_panel()` which updates `active_panel` and focuses the mapped widget.
- When `DetailPanel` enters edit mode, `active_panel` changes to `detail` and `focused_widget_id` becomes the active form field.

---

### 2. FilterControls

**Purpose**: Persist the user's time range, search, and label selections regardless of which appointments are currently loaded.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `start_date_text` | `str` | No | Raw `YYYY-MM-DD` text the user typed (so partial input can be preserved). |
| `end_date_text` | `str` | No | Same as above for end date. |
| `search_text` | `str` | No | Case-insensitive substring matched against appointment name and optionally description. |
| `search_in_description` | `bool` | No (default False) | Mirrors the "Desc" switch. |
| `available_labels` | `list[LabelReference]` | Yes | Full directory from `LabelService`, not filtered by current appointments. |
| `selected_label_ids` | `set[int]` | No | Used by both the filter UI and appointment query pipeline. |
| `keyboard_order` | `list[str]` | Yes | Ordered widget IDs used by arrow keys/Tab to move focus deterministically. |

**Validation Rules**:
- When both start and end dates parse successfully, `start <= end` must hold; otherwise a warning is shown and the pending API call is aborted.
- `selected_label_ids` must always be a subset of `available_labels.id` — unknown IDs are discarded when labels refresh.

---

### 3. LabelDirectory / LabelReference

**Purpose**: Provide metadata for label toggles and edit-form suggestions.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `int` | Yes | Primary key passed to the API. |
| `name` | `str` | Yes | Display name and autocomplete token. |
| `color` | `str` | No | Hex color used in filter buttons and detail badges. |
| `assigned_count` | `int` | No (derived) | Count of currently loaded appointments containing the label; used only for zero-state hints. |
| `active` | `bool` | No | Indicates whether a label toggle is currently selected. |

**Relationships**:
- Shared by `FilterControls.available_labels`, `DetailPanel.EditFormState.label_tokens`, and label autocomplete suggestions.
- Each label toggle view binds to a `LabelReference`; changes propagate to `selected_label_ids`.

---

### 4. EditFormState

**Purpose**: Represent the editable copy of the selected appointment, including granular inputs for dates, times, reminder units, and label suggestions.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `fields` | `dict[str, str]` | Yes | Normalized string values for each editable field (name, description, etc.). |
| `start_date` | `str` | Yes | Date portion `dd.mm.yyyy`. |
| `start_time` | `str` | Yes | Time portion `HH:MM`. |
| `end_date` | `str` | Yes | Date portion `dd.mm.yyyy`. |
| `end_time` | `str` | Yes | Time portion `HH:MM`. |
| `notification_date` | `str` | No | Optional `dd.mm.yyyy`. |
| `notification_time` | `str` | No | Optional `HH:MM`. |
| `label_tokens` | `list[str]` | No | User-entered labels split on commas or Enter for autocomplete. |
| `invalid_labels` | `set[str]` | No | Signals labels that do not exist in `LabelDirectory`; triggers warning banners. |
| `reminder` | `ReminderSetting` | No | Structured reminder input (value + unit). |
| `dirty` | `bool` | Yes (default False) | Tracks whether form differs from `_original_snapshot`. |
| `_original_snapshot` | `dict[str, str]` | Yes | Baseline for diff preview and dirty tracking. |

**ReminderSetting Sub-Entity**:

| Field | Type | Notes |
|-------|------|-------|
| `value` | `int` | User-entered magnitude. |
| `unit` | `Literal["minutes", "hours", "days", "weeks"]` | Determines conversion factor. |
| `minutes_total` | `int` | `value * unit_multiplier`; must stay within 0–10 080. |
| `warning` | `Optional[str]` | Message produced when the converted value is out of range.

**State Transitions**:
1. Load appointment → hydrate `EditFormState` and `_original_snapshot` (dates/times split into German format).  
2. User edits a field → update `fields[...]`, recompute `dirty`, and re-render badges/spacers.  
3. `save` action → validate (dates parse, `start <= end`, reminder range, known labels). On success produce diff payload and pass to confirmation modal.  
4. Confirm → merge structured values back into `Appointment` model → call client.  
5. Cancel/discard → reset to `_original_snapshot` and clear warnings.

---

### 5. DiffPreviewPayload

**Purpose**: Feed the confirmation dialog with before/after values, grouped for readability after an edit.

| Field | Type | Notes |
|-------|------|-------|
| `sections` | `list[DiffSection]` | Allows grouping (e.g., "Schedule", "Reminder", "Labels"). |
| `contains_changes` | `bool` | Short-circuits when no data changed. |
| `formatted_lines` | `list[str]` | Pre-rendered Textual markup consumed by `ConfirmationDialog`. |

**DiffSection Sub-Entity**:

| Field | Type | Notes |
|-------|------|-------|
| `title` | `str` | Display heading. |
| `entries` | `list[DiffEntry]` | Each `DiffEntry` has `field`, `old`, `new`. |

**Usage**:
- Built from `EditFormState` just before showing the modal.  
- Passed to `ConfirmationDialog.build_update_diff()` to keep constitution Principle II intact.  
- Also reused after saves to drive success toast copy.

---

## Relationships

```
LabelDirectory 1──* LabelReference
LabelReference *──* EditFormState (through label_tokens)
EditFormState 1──1 DiffPreviewPayload (per save attempt)
NavigationState 1──1 FilterControls (active panel can be "filter")
FilterControls 1──* AppointmentService filters (start/end/search/labels)
```

## Notes & Validation Summary

- All displayed timestamps (list + detail) rely on a shared formatter that produces `dd.mm.yyyy HH:MM` while reading/writing UTC ISO 8601 to the API.
- Reminder conversions always pass through `ReminderSetting.minutes_total` so the API sees minutes; validation ensures the 0–10 080 constraint from R-201.
- `LabelDirectory.available_labels` is populated from `LabelService.labels` at startup and never reduced by current appointment results; zero-count labels are simply styled as inactive.
- `NavigationState` allows us to show left/right arrow hints contextually and ensures `Tab`/arrow loops never dead-end.
