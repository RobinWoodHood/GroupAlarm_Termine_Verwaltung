# Feature Specification: TUI UX Enhancements

**Feature Branch**: `002-tui-ux-enhancements`  
**Created**: 2026-03-23  
**Status**: Draft  
**Input**: User description: "Improve navigation between appointment list/detail views, restore full filter controls with shortcuts, and deliver a functional editing flow with readable formatting, reminders, and label suggestions."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keyboard Navigation Between List and Detail (Priority: P1)

Dispatchers reviewing many appointments need to switch between the appointment list, detail panel, and filter bar without losing context or using the mouse.

**Why this priority**: Fast navigation directly impacts daily throughput and reduces data-entry mistakes when triaging appointments.

**Independent Test**: Open the CLI UI with seeded data, rely solely on arrow controls and keyboard shortcuts, and confirm the operator can reach list, detail, and filter inputs without touching the mouse.

**Acceptance Scenarios**:

1. **Given** the appointment list and detail panel are visible, **When** the user activates the left/right arrow affordances or presses the mapped keys, **Then** focus and highlight move between list and detail without losing selection.
2. **Given** the filter bar label section is not focused and is showing only five label toggles plus a `+N weitere` helper chip when additional labels exist, **When** the user presses `Ctrl + /` (start-date filter), `Ctrl + Shift + /` (end-date filter), or `Ctrl + F` (search), **Then** the targeted input receives focus, the label section expands to reveal the full directory, and existing filters remain visible.
3. **Given** focus is inside the filter bar, **When** the user presses arrow keys or Tab, **Then** focus cycles predictably across time filter, search, and label toggles, never skipping controls even if the current list has no matching labels.
4. **Given** focus enters any filter bar control, **When** the UI renders, **Then** the label section expands immediately to show every available toggle; when focus leaves, it returns to a five-toggle preview (or all toggles if five or fewer exist) while preserving counts and the helper chip that indicates hidden labels.

---

### User Story 2 - Confident Appointment Editing With Preview (Priority: P1)

Editors must update appointment details (dates, reminders, labels, description) and only persist changes after reviewing a diff-style confirmation.

**Why this priority**: Editing errors directly affect notification accuracy; operators need to see exactly what will change before saving.

**Independent Test**: Enter edit mode on an appointment, modify multiple fields (date/time, reminder, labels), preview the diff, and confirm that accepting the diff updates the record and refreshes the list.

**Acceptance Scenarios**:

1. **Given** an appointment in edit mode, **When** the user navigates fields with up/down arrows and presses Enter, **Then** the field becomes editable with dedicated inputs for date and time (start, end, notification) using the German format.
2. **Given** the reminder input, **When** the user selects minutes, hours, days, or weeks and enters a value within the allowed range, **Then** the UI validates the limit and shows a friendly warning if exceeded.
3. **Given** label editing, **When** the user types a label name, **Then** typeahead suggestions show existing labels and a warning appears if the entry does not exist.
4. **Given** the user clicks Save, **When** changes exist, **Then** a diff preview lists field-level differences and requires explicit confirmation before persisting and refreshing the appointment list.

---

### User Story 3 - Readable Detail Presentation (Priority: P2)

Viewers want the detail panel to remain lightweight but visually separated with spacing, color accents, and consistent formatting so key times are scannable.

**Why this priority**: Visual clarity reduces cognitive load and helps operators verify times at a glance.

**Independent Test**: Display a sample appointment in view mode and confirm spacing after description/start/end blocks, clear headings, and German-formatted timestamps without entering edit mode.

**Acceptance Scenarios**:

1. **Given** any appointment detail view, **When** it renders, **Then** all date/time fields display as `dd.mm.yyyy HH:MM` with distinct labels for start, end, and notification times.
2. **Given** a long description or multiple labels, **When** the detail panel renders, **Then** additional spacing and subtle color cues keep sections visually separated without clipping content.

---

### Edge Cases

- If the appointment list contains labels not present in the global directory, the filter bar still lists all known labels and, when a label has zero applicable appointments, shows a muted `0` badge plus a "Keine Treffer" helper chip while keeping the toggle focusable. When the bar is unfocused it always shows a five-toggle preview (or the full set if five or fewer exist) along with a `+N weitere` helper chip so operators know additional labels are available; focusing any filter control expands the directory instantly.
- When no reminders are allowed beyond a backend-imposed maximum, the reminder input must surface the exact limit before the user confirms changes.
- If an appointment has no description or optional fields, spacing and keyboard navigation must still maintain predictable focus order without collapsing the layout.
- All appointment datetimes are stored as UTC by the backend but must be converted to `Europe/Berlin` before rendering in the list or detail panel; failures must fall back to the raw ISO timestamp and raise a warning toast.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Provide visible left/right arrow affordances (and equivalent keyboard shortcuts) to switch focus between the appointment list and detail panel without altering the current selection.
- **FR-002**: Implement `Ctrl + /` to focus the start-date filter, `Ctrl + Shift + /` to focus the end-date filter, and `Ctrl + F` to focus the search field regardless of current focus state.
- **FR-003**: Ensure the filter bar always displays time filter, search, and the complete label toggle set; arrow keys and Tab must move focus sequentially across these controls even when some filters have zero matches.
- **FR-004**: Display all appointment timestamps (list and detail) in German format `dd.mm.yyyy HH:MM`, including start, end, and notification times.
- **FR-005**: Enable edit mode so each field (description, start, end, notification, labels, reminder) becomes editable; up/down arrows move between fields and Enter initiates editing.
- **FR-006**: Provide dedicated date and time inputs for start, end, and notification that validate logical ordering (start <= end) and convert user entries into the unified display format.
- **FR-007**: Support reminder durations in minutes, hours, days, and weeks, enforcing the backend limit (see Assumptions) and surfacing inline warnings when users exceed it.
- **FR-008**: Offer label inputs with autocomplete suggestions sourced from all available labels; if a typed label is unknown, present a warning and allow cancellation before saving.
- **FR-009**: Upon Save, present a diff preview summarizing all modified fields, require explicit confirmation, and refresh both the list and detail panel after a successful commit.
- **FR-010**: Apply additional spacing and subtle color accents in the detail panel so sections (description, timing, labels, reminder) remain visually distinct in both view and edit modes.

### Key Entities *(include if feature involves data)*

- **Appointment**: Represents a scheduled activity with description, start/end timestamps, notification time, reminder settings, and assigned labels.
- **Filter Controls**: Aggregated state for time range selection, search query, and label toggles; must persist regardless of current query results.
- **Label Directory**: Complete catalog of labels available for tagging appointments, used for filter options and edit-mode autocomplete.
- **Reminder Setting**: User-defined lead time expressed in minutes/hours/days/weeks with an enforced maximum before the appointment start.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can move focus between list, detail, and filter controls using arrows/shortcuts in under 1 second per transition during usability testing, measured via a Textual Pilot timing benchmark recorded in `docs/tui-focus-metrics.md`.
- **SC-002**: 100% of appointment timestamps (view and edit) render in `dd.mm.yyyy HH:MM` format with no regressions reported during QA.
- **SC-003**: Editing flow sign-off requires that users can review a diff and confirm changes, with at least 95% of edits saving successfully on the first attempt during UAT, documented in `docs/tui-save-metrics.md`.
- **SC-004**: At least 90% of surveyed operators report the new detail-panel spacing/colors make key fields easier to scan after one week of adoption.
- **SC-005**: Keyboard-only navigation through filter bar and edit fields completes without dead-ends in 5 consecutive QA runs, with the evidence logged in `docs/tui-focus-metrics.md` alongside the SC-001 timing benchmarks.

## Assumptions

- Reminder lead times must stay within the backend's documented window of 0–10 080 minutes (exactly seven days) before the appointment start, as confirmed in R-201; the UI must enforce and message this limit consistently. This limit is static at runtime—if the backend changes it, the CLI must be updated and re-released.
- Color accents and spacing changes will follow existing GroupAlarm CLI branding to avoid re-theming the entire application.
- Available label directory is already cached locally by the CLI; the feature only needs to surface it for suggestions and filters.
- Server datetimes are stored in UTC, but the CLI must display them in `Europe/Berlin` using `zoneinfo.ZoneInfo("Europe/Berlin")` and document any deviation in the QA notes.
