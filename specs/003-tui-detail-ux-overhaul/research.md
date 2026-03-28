# Research: TUI Detail Panel UX Overhaul

**Feature**: 003-tui-detail-ux-overhaul  
**Date**: 2026-03-28

## R-001: Live Preview via DataTable Cursor Events

**Question**: How to update the detail panel on arrow-key navigation in the list?

**Decision**: Use Textual's `DataTable.RowHighlighted` event.

**Rationale**: The current codebase only handles `DataTable.RowSelected` (fires on Enter/click). Textual also provides `DataTable.RowHighlighted` which fires on **every arrow-key cursor movement**. Adding an `on_data_table_row_highlighted` handler in `AppointmentList` (or catching it in `MainScreen`) enables live preview without changing the Enter behavior.

**Alternatives considered**:
- Polling `table.cursor_coordinate` on a timer — rejected (laggy, wasteful).
- Overriding `DataTable.watch_cursor_coordinate` — rejected (fragile internal API).

---

## R-002: Focus Switching Between List and Detail Panel

**Question**: How to implement keyboard-driven focus transitions (Enter/Right → detail, Left → back)?

**Decision**: Extend existing `MainScreen` bindings and `NavigationState` tracking.

**Rationale**: `MainScreen` already has `action_focus_list_panel()` and `action_focus_detail_panel()` with Left/Right bindings. Currently, Right arrow focuses the detail panel and Left returns to the list. The additional behavior needed:
- Enter in the list should also move to the detail panel (add binding or handle in `on_data_table_row_selected`)
- E in the list should enter edit mode directly (existing `action_edit_mode` already handles this — it activates edit and moves focus to detail)
- Left arrow in detail panel (read-only mode) with unsaved changes triggers the existing `UnsavedChangesDialog`
- In edit mode, Left/Right arrow keys are reserved for text cursor navigation within input fields — the user must press Escape first to return to read-only mode before Left can navigate back to the list

The existing `_focus_detail_panel()` calls `detail.focus_content()` which focuses `#detail-scroll` (VerticalScroll) — this already allows Up/Down scrolling in read-only mode.

**Alternatives considered**:
- Custom focus ring manager — rejected (Textual's built-in focus management suffices).

---

## R-003: Yellow Highlight Color for Field Labels

**Question**: What is the exact yellow color to use, and how to apply it in the TCSS?

**Decision**: Use the Textual theme variable `$accent` for field labels.

**Rationale**: The border between list and detail panel is styled as `border-left: solid $accent` (in the `.is-active` state). In Textual's default dark theme, `$accent` maps to yellow. Using Rich markup `[$accent]Label:[/$accent]` in Static widgets, or applying a CSS class with `color: $accent`, ensures visual consistency.

For edit mode labels, a CSS class `.field-label { color: $accent; }` can be applied to Static widgets preceding each input.

**Alternatives considered**:
- Hardcoded `yellow` color — rejected (would not adapt to theme changes).
- `$primary` (blue by default) — rejected (user explicitly said "same yellow as the line").

---

## R-004: Arrow Key Navigation in Edit Mode

**Question**: Can Up/Down move between edit fields without conflicting with TextArea line navigation?

**Decision**: Add Up/Down bindings to `EditInput` that call `screen.focus_previous()`/`screen.focus_next()`. For `TextArea` (description), Up/Down navigate lines within the text area and only trigger field-to-field navigation at the boundaries: Down on the **last line** moves to the next field, Up on the **first line** moves to the previous field.

**Rationale**: `EditInput` (subclass of `Input`) does not currently bind Up/Down. Textual's `Input` widget ignores Up/Down (they propagate). Adding bindings is straightforward. The `TextArea` used for description has multi-line content where Up/Down navigate lines. To avoid breaking text editing while still allowing keyboard-only field navigation, boundary detection is used: `TextArea.cursor_location` returns `(row, col)` and `TextArea.document.line_count` gives the total number of lines. When `row == 0` and Up is pressed, or `row == line_count - 1` and Down is pressed, the event is intercepted to move focus to the adjacent field.

**Alternatives considered**:
- Never intercepting Up/Down in TextArea (Tab-only exit) — rejected (inconsistent with the field-to-field pattern; user expects Down at end of description to reach the next field).
- Always intercepting Up/Down in TextArea — rejected (breaks multi-line editing).
- Using only Ctrl+Up/Ctrl+Down — rejected (user explicitly requested plain arrow keys).

---

## R-005: Participant Data and Name Resolution

**Question**: How are participants stored and how to resolve user IDs to names?

**Decision**: Parse `Appointment.participants` (List[Dict]) for `userID`, `labelID`, `feedback`, `feedbackMessage`. Add a `list_users()` method to `GroupAlarmClient` calling `GET /users?organization={id}`. Cache user lookup in a new `UserService`.

**Rationale**: The appointment schema includes `participants` as `AppointmentParticipant[]` with fields: `userID`, `labelID`, `feedback` (int), `feedbackMessage` (string), `appointmentID`, `startDate`. However, the `/appointments/calendar` list endpoint may return participants without full detail. The single-appointment `GET /appointment/{id}` endpoint returns the full `Appointment` schema including participants.

For name resolution, the Users API provides `GET /users?organization={orgId}` returning `PublicUser[]` with `id`, `name`, `surname`, `email`. This can be cached per session since the org member list rarely changes.

**Alternatives considered**:
- Resolving names one-by-one via `GET /user/{id}` — rejected (N+1 queries, slow for many participants).
- Embedding names in the appointment response — not supported by API.

---

## R-006: Feedback Status Mapping

**Question**: What integer values does `AppointmentFeedbackStatus` use?

**Decision**: Treat as: 0 = no feedback (pending), 1 = accepted (positive), 2 = declined (negative).

**Rationale**: The OpenAPI spec defines `AppointmentFeedbackStatus` as `integer (int64)` without enumerating values. Based on GroupAlarm's typical Go enum pattern (iota starts at 0) and the API description ("current feedback status"), the conventional mapping is 0=none, 1=accepted, 2=declined. This will be verified during implementation by inspecting API responses. The code should use named constants to make future corrections easy.

**Alternatives considered**:
- Fetching status descriptions from a metadata endpoint — no such endpoint exists.

---

## R-007: Users API Integration

**Question**: Which Users API endpoint to use and authentication mechanism?

**Decision**: Use `GET /users?organization={orgId}` with `Personal-Access-Token` header (same as appointment API).

**Rationale**: The Users OpenAPI spec (`api-docs/users.openapi.json`) confirms:
- `GET /users` with query param `organization` (required, int) returns all users from an organization
- Authentication: `Personal-Access-Token` header (same as used by `GroupAlarmClient`)
- Response: array of `PublicUser` objects with `id`, `name`, `surname`, `email`, `availableStatus`, `pending`
- Base URL: `https://app.groupalarm.com/api/v1` (same as appointment API)

Since `GroupAlarmClient` already uses the same base URL and token, the method can be added directly to the existing client.

**Alternatives considered**:
- `GET /users/pagination` — provides pagination but adds complexity; the full list endpoint suffices for typical org sizes.

---

## R-008: keepLabelParticipantsInSync and isPublic in Create Form

**Question**: How to add these fields to the create/edit form?

**Decision**: Add `keepLabelParticipantsInSync` and change `isPublic` default in `EDIT_FIELD_DEFS` and `EditFormState`. The `Appointment` dataclass already has both fields.

**Rationale**: `Appointment` already defines `isPublic: bool = True` and `keepLabelParticipantsInSync: bool = True`. The edit form already includes `isPublic`. Changes needed:
1. Add `keepLabelParticipantsInSync` to `EDIT_FIELD_DEFS` (Ja/Nein input)
2. Change default for `isPublic` in the create-mode initialization to `False`
3. The `to_api_payload()` already includes both fields in the payload

**Alternatives considered**:
- Adding a separate settings/preferences panel — rejected (overengineered for two toggles).

---

## R-009: Direct User Addition (Participants Field)

**Question**: How to implement comma-separated user suggestion analogous to label suggestion?

**Decision**: Create a `UserSuggester` class (analogous to `LabelSuggester`) that suggests from the organization user list. Add a "Teilnehmer" `EditInput` field to the create/edit form. Use the same comma-separated token pattern as labels.

**Rationale**: The existing `LabelSuggester` class already handles comma-separated token suggestions by parsing the last token after the last comma. The same pattern applies to users: type "Max M" → suggests "Max Mustermann", press Tab to accept, type comma, type next name. After accepting, user IDs are resolved from the cached user list when building the API payload.

**Alternatives considered**:
- Separate per-participant dialog — rejected (too many clicks for multiple participants).
- Integer ID entry — rejected (terrible UX).

---

## R-010: Tab-Accept Cursor Position

**Question**: Does the current `EditInput.action_accept_or_next` place the cursor at the end?

**Decision**: The current implementation is correct — setting `self.value = self._suggestion` in Textual's Input widget places the cursor at the end of the new value. No change needed.

**Rationale**: Tested by code inspection: Textual's `Input.value` setter resets the cursor to the end of the string. The existing `action_accept_or_next` already achieves the desired behavior.

---

## R-011: Existing Configuration and Example File

**Question**: Does a config file or example already exist?

**Decision**: No `.groupalarm.toml` or `.groupalarm.example.toml` exists. Create `.groupalarm.example.toml` with all config keys documented.

**Rationale**: `framework/config.py` defines the schema:
```toml
[general]
organization_id = 12345
timezone = "Europe/Berlin"

[defaults]
date_range_days = 30
label_ids = []
appointment_duration_hours = 4
```
The `load_config()` function gracefully returns defaults if the file is missing. An example file serves as documentation.
